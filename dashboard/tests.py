from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from commandes.models import Commande, LigneCommande
from produits.models import Avis, Categorie, Produit


class DashboardBase(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user('admin', 'admin@ex.com', 'MotDePasse!2024', is_staff=True)
        cat = Categorie.objects.create(nom="PC", slug="pc")
        self.p = Produit.objects.create(nom="Laptop", slug="laptop", categorie=cat, prix=1000, stock=5)


class AccesTests(DashboardBase):
    def test_dashboard_reserve_au_staff(self):
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 302)
        self.client.login(username='admin', password='MotDePasse!2024')
        self.assertEqual(self.client.get(reverse('dashboard:index')).status_code, 200)

    def test_client_non_staff_refuse(self):
        User.objects.create_user('client', 'c@ex.com', 'MotDePasse!2024')
        r = self.client.post(reverse('dashboard:login'), {'username': 'client', 'password': 'MotDePasse!2024'})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_actions_destructives_refusent_get(self):
        self.client.login(username='admin', password='MotDePasse!2024')
        a = Avis.objects.create(produit=self.p, auteur='x', note=5)
        self.assertEqual(self.client.get(reverse('dashboard:avis_supprimer', args=[a.id])).status_code, 405)
        self.assertEqual(self.client.get(reverse('dashboard:avis_approuver', args=[a.id])).status_code, 405)
        self.assertTrue(Avis.objects.filter(id=a.id).exists())


class ConnexionThrottleTests(DashboardBase):
    def test_blocage_apres_5_echecs(self):
        for _ in range(5):
            self.client.post(reverse('dashboard:login'), {'username': 'admin', 'password': 'faux'})
        r = self.client.post(reverse('dashboard:login'), {'username': 'admin', 'password': 'MotDePasse!2024'})
        self.assertEqual(r.status_code, 429)
        self.assertNotIn('_auth_user_id', self.client.session)


class ReinitialisationTests(DashboardBase):
    def _demande(self, email='admin@ex.com'):
        return self.client.post(reverse('dashboard:mot_de_passe_oublie'), {'email': email})

    def test_email_inconnu_meme_reponse_et_aucun_mail(self):
        r = self._demande('inconnu@ex.com')
        self.assertRedirects(r, reverse('dashboard:verifier_code'))
        self.assertEqual(len(mail.outbox), 0)

    def test_parcours_complet(self):
        self._demande()
        code = self.client.session['reset_code']
        self.assertEqual(len(code), 6)
        self.assertIn(code, mail.outbox[0].subject)
        r = self.client.post(reverse('dashboard:verifier_code'), {'code': code})
        self.assertRedirects(r, reverse('dashboard:nouveau_mot_de_passe'))
        self.client.post(reverse('dashboard:nouveau_mot_de_passe'),
                         {'password': 'NouveauMdp!2024x', 'password2': 'NouveauMdp!2024x'})
        self.assertTrue(User.objects.get(username='admin').check_password('NouveauMdp!2024x'))

    def test_force_brute_du_code_bloquee(self):
        self._demande()
        bon = self.client.session['reset_code']
        faux = '000000' if bon != '000000' else '111111'
        for _ in range(5):
            self.client.post(reverse('dashboard:verifier_code'), {'code': faux})
        r = self.client.post(reverse('dashboard:verifier_code'), {'code': bon})
        self.assertRedirects(r, reverse('dashboard:mot_de_passe_oublie'))
        self.assertFalse(self.client.session.get('reset_code_verifie'))

    def test_mot_de_passe_faible_refuse(self):
        self._demande()
        self.client.post(reverse('dashboard:verifier_code'), {'code': self.client.session['reset_code']})
        self.client.post(reverse('dashboard:nouveau_mot_de_passe'), {'password': '12345678', 'password2': '12345678'})
        self.assertTrue(User.objects.get(username='admin').check_password('MotDePasse!2024'))


class CommandeStaffTests(DashboardBase):
    def test_annulation_remet_le_stock_une_seule_fois(self):
        c = Commande.objects.create(nom_client='A', telephone='1', adresse='x')
        LigneCommande.objects.create(commande=c, produit=self.p, nom_produit='Laptop', prix_unitaire=1000, quantite=2)
        self.client.login(username='admin', password='MotDePasse!2024')
        url = reverse('dashboard:commande_detail', args=[c.id])
        self.client.post(url, {'statut': 'annulee'})
        self.client.post(url, {'statut': 'annulee'})
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 7)
        self.client.post(url, {'statut': 'en_attente'})
        c.refresh_from_db()
        self.assertEqual(c.statut, 'annulee')
