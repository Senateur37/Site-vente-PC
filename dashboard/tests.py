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


class ContenuDuSiteTests(DashboardBase):
    """Ce qui est saisi dans le dashboard doit apparaître dans l'API de la vitrine."""

    def setUp(self):
        super().setUp()
        self.client.login(username='admin', password='MotDePasse!2024')

    def _params(self, **extra):
        """Données POST du formulaire Paramètres, pré-remplies avec les valeurs actuelles."""
        from django import forms
        from dashboard.forms import SiteSettingsForm
        from dashboard.models import SiteSettings
        form = SiteSettingsForm(instance=SiteSettings.get_settings())
        data = {}
        for nom, champ in form.fields.items():
            if isinstance(champ, forms.FileField):
                continue
            valeur = form[nom].value()
            data[nom] = 'on' if valeur is True else valeur if valeur is not None else ''
            if valeur is False:
                del data[nom]
        data.update(extra)
        return data

    def test_parametres_vers_api(self):
        r = self.client.post(reverse('dashboard:parametres'), self._params(
            site_nom='Ma Boutique', hero_titre='Bienvenue chez', hero_titre_accent='Ma Boutique',
            hero_bouton='Entrer', telephone='01 02', whatsapp_number='+22370000000',
            facebook_url='https://fb.com/x', footer_texte='Livraison 24h', monnaie_symbole='XOF',
            accent_couleur='#ff0000', apropos_texte='Premier.\n\nSecond.',
        ))
        self.assertEqual(r.status_code, 302)
        site = self.client.get('/api/site/').json()
        self.assertEqual(site['nom'], 'Ma Boutique')
        self.assertEqual(site['hero']['titre'], 'Bienvenue chez')
        self.assertEqual(site['hero']['bouton'], 'Entrer')
        self.assertEqual(site['telephone'], '01 02')
        self.assertEqual(site['whatsapp'], '+22370000000')
        self.assertEqual(site['facebook'], 'https://fb.com/x')
        self.assertEqual(site['footer_texte'], 'Livraison 24h')
        self.assertEqual(site['monnaie'], 'XOF')
        self.assertEqual(site['couleurs']['accent'], '#ff0000')
        self.assertEqual(site['apropos'], ['Premier.', 'Second.'])

    def test_couleur_invalide_refusee(self):
        r = self.client.post(reverse('dashboard:parametres'), self._params(accent_couleur='rouge'))
        self.assertEqual(r.status_code, 200)
        from dashboard.models import SiteSettings
        self.assertEqual(SiteSettings.get_settings().accent_couleur, '#2563eb')

    def test_engagements_par_defaut_et_crud(self):
        from dashboard.models import Engagement
        self.assertEqual(len(self.client.get('/api/site/').json()['engagements']), 3)
        self.client.post(reverse('dashboard:engagement_ajouter'),
                         {'icone': '⭐', 'titre': 'Service premium', 'texte': 'x', 'ordre': 0, 'actif': 'on'})
        titres = [e['titre'] for e in self.client.get('/api/site/').json()['engagements']]
        self.assertIn('Service premium', titres)
        e = Engagement.objects.get(titre='Service premium')
        self.client.post(reverse('dashboard:engagement_supprimer', args=[e.id]))
        titres = [e['titre'] for e in self.client.get('/api/site/').json()['engagements']]
        self.assertNotIn('Service premium', titres)

    def test_engagement_inactif_masque(self):
        from dashboard.models import Engagement
        Engagement.objects.all().update(actif=False)
        self.assertEqual(self.client.get('/api/site/').json()['engagements'], [])

    def test_section_accueil_visible_sur_la_vitrine(self):
        from produits.models import SectionAccueil
        self.client.post(reverse('dashboard:section_ajouter'), {
            'titre': 'Nouveautés du mois', 'type_section': 'nouveautes', 'marque': '',
            'max_produits': 8, 'ordre': 1, 'active': 'on', 'afficher_voir_plus': 'on'})
        self.assertTrue(SectionAccueil.objects.filter(titre='Nouveautés du mois').exists())
        sections = self.client.get('/api/accueil/').json()['sections']
        self.assertEqual([s['titre'] for s in sections], ['Nouveautés du mois'])

    def test_code_promo_depuis_le_dashboard(self):
        from commandes.models import CodePromo
        self.client.post(reverse('dashboard:code_promo_ajouter'),
                         {'code': 'bienvenue10', 'pourcentage': 10, 'montant': 0, 'utilisations_max': 0, 'actif': 'on'})
        self.assertEqual(CodePromo.objects.get().code, 'BIENVENUE10')
        r = self.client.post(reverse('dashboard:code_promo_ajouter'),
                             {'code': 'VIDE', 'pourcentage': 0, 'montant': 0, 'utilisations_max': 0, 'actif': 'on'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(CodePromo.objects.count(), 1)

    def test_pages_reservees_au_staff(self):
        self.client.logout()
        for nom in ('engagement_liste', 'section_liste', 'code_promo_liste', 'parametres'):
            self.assertEqual(self.client.get(reverse(f'dashboard:{nom}')).status_code, 302)

    def test_prix_barre_modifiable(self):
        r = self.client.post(reverse('dashboard:produit_modifier', args=[self.p.id]), {
            'categorie': self.p.categorie_id, 'marque': '', 'nom': 'Laptop', 'slug': 'laptop',
            'description': '', 'prix': '1000', 'prix_barre': '1500', 'stock': 5, 'disponible': 'on'})
        self.assertEqual(r.status_code, 302)
        d = self.client.get('/api/produits/laptop/').json()
        self.assertTrue(d['en_promo'])
        self.assertEqual(d['pourcentage_reduction'], 33)

    def test_pages_du_contenu_s_affichent(self):
        from dashboard.models import Engagement
        e = Engagement.objects.first()
        for nom, args in [('parametres', []), ('engagement_liste', []), ('engagement_ajouter', []),
                          ('engagement_modifier', [e.id]), ('engagement_supprimer', [e.id]),
                          ('section_liste', []), ('section_ajouter', []),
                          ('code_promo_liste', []), ('code_promo_ajouter', [])]:
            r = self.client.get(reverse(f'dashboard:{nom}', args=args))
            self.assertEqual(r.status_code, 200, nom)
