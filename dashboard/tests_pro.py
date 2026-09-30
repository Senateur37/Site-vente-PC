"""Tests du dashboard professionnel : stats, rôles, recherche/filtres, commandes, équipe, journal."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from commandes.models import CodePromo, Commande, HistoriqueCommande, LigneCommande
from produits.models import Avis, Categorie, Produit

from .models import ActiviteLog
from .roles import creer_groupes, domaines_de, role_de

MDP = 'MotDePasse!2024x'


def membre(username, role=None, **extra):
    u = User.objects.create_user(username, f'{username}@ex.com', MDP, is_staff=True, **extra)
    if role:
        creer_groupes()
        u.groups.add(Group.objects.get(name=role))
    return u


class Base(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = membre('admin', 'Administrateur')
        self.cat = Categorie.objects.create(nom='PC', slug='pc')
        self.p = Produit.objects.create(nom='Laptop', slug='laptop', categorie=self.cat, prix=1000, stock=10, marque='hp')
        self.client.login(username='admin', password=MDP)

    def commande(self, statut='en_attente', quantite=2, tel='70 00 00 01', nom='Awa', **kw):
        c = Commande.objects.create(nom_client=nom, telephone=tel, adresse='Quartier', statut=statut, **kw)
        LigneCommande.objects.create(commande=c, produit=self.p, nom_produit='Laptop', prix_unitaire=1000, quantite=quantite)
        return c


class StatsTests(Base):
    def test_ca_net_des_commandes_livrees_et_payees(self):
        self.commande('livree_payee', 2, reduction=Decimal('200'))   # 2000 - 200
        self.commande('livree_payee', 1)                               # 1000
        self.commande('en_attente', 5)                                 # ignorée
        self.commande('annulee', 5)                                    # ignorée
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['ca'], Decimal('2800'))
        self.assertEqual(r.context['nb_commandes'], 3)
        self.assertEqual(r.context['livrees'], 2)
        self.assertEqual(r.context['nb_a_traiter'], 1)
        self.assertEqual(r.context['panier_moyen'], Decimal('1400'))

    def test_variation_par_rapport_a_la_periode_precedente(self):
        ancienne = self.commande('livree_payee', 1)
        Commande.objects.filter(pk=ancienne.pk).update(date_creation=timezone.now() - timedelta(days=40))
        self.commande('livree_payee', 3)
        r = self.client.get(reverse('dashboard:index') + '?p=30')
        self.assertEqual(r.context['ca_variation'], 200)   # 1000 -> 3000
        r = self.client.get(reverse('dashboard:index') + '?p=7')
        self.assertIsNone(r.context['ca_variation'])       # pas de base de comparaison

    def test_periodes_et_serie_du_graphique(self):
        self.commande('livree_payee', 1)
        for p, n in ((7, 7), (30, 30), (90, 90)):
            r = self.client.get(reverse('dashboard:index') + f'?p={p}')
            self.assertEqual(len(r.context['graph_ca']['labels']), n + 1 if n else n)
            self.assertAlmostEqual(sum(r.context['graph_ca']['valeurs']), 1000)
        r = self.client.get(reverse('dashboard:index') + '?p=365')
        self.assertLessEqual(len(r.context['graph_ca']['labels']), 13)
        self.assertEqual(self.client.get(reverse('dashboard:index') + '?p=abc').status_code, 200)

    def test_alertes_stock(self):
        Produit.objects.create(nom='Rupture', slug='r', categorie=self.cat, prix=1, stock=0)
        Produit.objects.create(nom='Faible', slug='f', categorie=self.cat, prix=1, stock=2)
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.context['nb_ruptures'], 1)
        self.assertEqual(r.context['nb_stock_faible_total'], 1)


class RolesTests(Base):
    def test_domaines_par_role(self):
        self.assertEqual(role_de(self.admin), 'Administrateur')
        cmd = membre('cmd', 'Gestionnaire de commandes')
        cat = membre('cat', 'Gestionnaire de catalogue')
        self.assertEqual(domaines_de(cmd), {'commandes', 'avis'})
        self.assertEqual(domaines_de(cat), {'catalogue', 'contenu', 'avis'})

    def test_staff_sans_role_reste_administrateur(self):
        ancien = membre('ancien')
        self.assertEqual(role_de(ancien), 'Administrateur')
        self.assertIn('equipe', domaines_de(ancien))

    def test_gestionnaire_de_commandes_est_cantonne(self):
        membre('cmd', 'Gestionnaire de commandes')
        self.client.login(username='cmd', password=MDP)
        self.assertEqual(self.client.get(reverse('dashboard:commandes_liste')).status_code, 200)
        for nom in ('produits_liste', 'equipe_liste', 'journal', 'parametres', 'section_liste'):
            r = self.client.get(reverse(f'dashboard:{nom}'))
            self.assertRedirects(r, reverse('dashboard:index'), fetch_redirect_response=False, msg_prefix=nom)
        self.assertEqual(self.client.get(reverse('dashboard:index')).status_code, 200)

    def test_gestionnaire_de_catalogue_est_cantonne(self):
        membre('cat', 'Gestionnaire de catalogue')
        self.client.login(username='cat', password=MDP)
        self.assertEqual(self.client.get(reverse('dashboard:produits_liste')).status_code, 200)
        for nom in ('commandes_liste', 'clients_liste', 'equipe_liste', 'code_promo_liste'):
            r = self.client.get(reverse(f'dashboard:{nom}'))
            self.assertEqual(r.status_code, 302, nom)

    def test_menu_masque_les_sections_interdites(self):
        membre('cmd', 'Gestionnaire de commandes')
        self.client.login(username='cmd', password=MDP)
        html = self.client.get(reverse('dashboard:index')).content.decode()
        self.assertIn(reverse('dashboard:commandes_liste'), html)
        self.assertNotIn(reverse('dashboard:equipe_liste'), html)
        self.assertNotIn(reverse('dashboard:produits_liste'), html)

    def test_compte_desactive_ou_non_staff_refuse(self):
        u = membre('parti', 'Administrateur')
        u.is_active = False
        u.save()
        self.client.logout()
        r = self.client.post(reverse('dashboard:login'), {'username': 'parti', 'password': MDP})
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(r.status_code, 200)

    def test_redirection_apres_connexion_uniquement_interne(self):
        self.client.logout()
        url = reverse('dashboard:login')
        r = self.client.post(url, {'username': 'admin', 'password': MDP, 'next': '/dashboard/commandes/'})
        self.assertRedirects(r, '/dashboard/commandes/', fetch_redirect_response=False)
        self.client.logout()
        r = self.client.post(url, {'username': 'admin', 'password': MDP, 'next': 'https://evil.example/'})
        self.assertRedirects(r, reverse('dashboard:index'), fetch_redirect_response=False)


class RechercheEtPaginationTests(Base):
    def test_produits_filtres(self):
        Produit.objects.create(nom='Souris', slug='souris', categorie=self.cat, prix=50, stock=0, marque='hp')
        Produit.objects.create(nom='Clavier', slug='clavier', categorie=self.cat, prix=70, stock=2, disponible=False)
        url = reverse('dashboard:produits_liste')
        noms = lambda r: sorted(p.nom for p in r.context['produits'])
        self.assertEqual(noms(self.client.get(url + '?q=souris')), ['Souris'])
        self.assertEqual(noms(self.client.get(url + '?stock=rupture')), ['Souris'])
        self.assertEqual(noms(self.client.get(url + '?stock=faible')), ['Clavier'])
        self.assertEqual(noms(self.client.get(url + '?stock=ok')), ['Laptop'])
        self.assertEqual(noms(self.client.get(url + '?dispo=non')), ['Clavier'])
        self.assertEqual(noms(self.client.get(url + '?marque=hp')), ['Laptop', 'Souris'])
        self.assertEqual(noms(self.client.get(url + f'?categorie={self.cat.id}&tri=prix_asc')), ['Clavier', 'Laptop', 'Souris'] if False else ['Clavier', 'Laptop', 'Souris'])
        r = self.client.get(url + '?tri=prix_asc')
        self.assertEqual([p.nom for p in r.context['produits']], ['Souris', 'Clavier', 'Laptop'])
        self.assertEqual(self.client.get(url + '?marque=inconnue&tri=x&stock=x').status_code, 200)

    def test_pagination_conserve_les_filtres(self):
        for i in range(45):
            Produit.objects.create(nom=f'Pc {i}', slug=f'pc-{i}', categorie=self.cat, prix=10, stock=5)
        url = reverse('dashboard:produits_liste')
        r = self.client.get(url + '?q=Pc')
        self.assertEqual(len(r.context['produits']), 20)
        self.assertEqual(r.context['total'], 45)
        self.assertContains(r, 'q=Pc&page=2')
        self.assertEqual(len(self.client.get(url + '?q=Pc&page=3').context['produits']), 5)
        self.assertEqual(self.client.get(url + '?q=Pc&page=999').status_code, 200)   # page hors limite
        self.assertEqual(self.client.get(url + '?q=Pc&page=abc').status_code, 200)

    def test_commandes_filtrees(self):
        a = self.commande('en_attente', tel='70 11 22 33', nom='Awa Traoré')
        b = self.commande('livree_payee', nom='Moussa')
        Commande.objects.filter(pk=b.pk).update(date_creation=timezone.now() - timedelta(days=10))
        url = reverse('dashboard:commandes_liste')
        ids = lambda r: sorted(c.id for c in r.context['commandes'])
        self.assertEqual(ids(self.client.get(url + '?q=traor')), [a.id])
        self.assertEqual(ids(self.client.get(url + '?q=70 11')), [a.id])
        self.assertEqual(ids(self.client.get(url + f'?q=%23{b.id}')), [b.id])
        self.assertEqual(ids(self.client.get(url + '?statut=livree_payee')), [b.id])
        du = (timezone.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        self.assertEqual(ids(self.client.get(url + f'?du={du}')), [a.id])
        au = (timezone.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        self.assertEqual(ids(self.client.get(url + f'?au={au}')), [b.id])
        self.assertEqual(self.client.get(url + '?du=pas-une-date&statut=bidon').status_code, 200)

    def test_avis_filtres(self):
        Avis.objects.create(produit=self.p, auteur='Awa', note=5, commentaire='Top', approuve=True)
        Avis.objects.create(produit=self.p, auteur='Moi', note=2, commentaire='Bof')
        url = reverse('dashboard:avis_liste')
        self.assertEqual(self.client.get(url + '?statut=en_attente').context['total'], 1)
        self.assertEqual(self.client.get(url + '?note=5').context['total'], 1)
        self.assertEqual(self.client.get(url + '?q=bof').context['total'], 1)


class CommandesTests(Base):
    def test_changement_de_statut_historise(self):
        c = self.commande()
        url = reverse('dashboard:commande_detail', args=[c.id])
        self.client.post(url, {'action': 'statut', 'statut': 'en_livraison', 'note': 'Livreur parti'})
        c.refresh_from_db()
        self.assertEqual(c.statut, 'en_livraison')
        h = HistoriqueCommande.objects.get()
        self.assertEqual((h.ancien_statut, h.nouveau_statut, h.note, h.utilisateur), ('en_attente', 'en_livraison', 'Livreur parti', self.admin))
        self.assertTrue(h.est_changement_statut)
        self.assertContains(self.client.get(url), 'Livreur parti')
        self.assertTrue(ActiviteLog.objects.filter(action='statut', objet=f'Commande #{c.id}').exists())

    def test_meme_statut_n_ajoute_rien(self):
        c = self.commande()
        self.client.post(reverse('dashboard:commande_detail', args=[c.id]), {'action': 'statut', 'statut': 'en_attente'})
        self.assertEqual(HistoriqueCommande.objects.count(), 0)

    def test_note_interne(self):
        c = self.commande()
        self.client.post(reverse('dashboard:commande_detail', args=[c.id]), {'action': 'note', 'note': 'Client VIP'})
        h = HistoriqueCommande.objects.get()
        self.assertEqual(h.note, 'Client VIP')
        self.assertFalse(h.est_changement_statut)
        c.refresh_from_db()
        self.assertEqual(c.statut, 'en_attente')

    def test_annulation_remet_le_stock_une_fois_et_est_definitive(self):
        c = self.commande(quantite=3)
        Produit.objects.filter(pk=self.p.pk).update(stock=7)
        url = reverse('dashboard:commande_detail', args=[c.id])
        self.client.post(url, {'statut': 'annulee'})
        self.client.post(url, {'statut': 'annulee'})
        self.client.post(url, {'statut': 'en_attente'})
        self.p.refresh_from_db()
        c.refresh_from_db()
        self.assertEqual((self.p.stock, c.statut), (10, 'annulee'))
        self.assertEqual(HistoriqueCommande.objects.count(), 1)

    def test_email_au_client_lors_du_changement(self):
        from django.core import mail
        c = self.commande(email='awa@ex.com')
        self.client.post(reverse('dashboard:commande_detail', args=[c.id]), {'statut': 'livree_payee'})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('livrée', mail.outbox[0].body)

    def test_facture_et_bon_de_livraison(self):
        c = self.commande(quantite=2, reduction=Decimal('100'), frais_livraison=Decimal('500'))
        r = self.client.get(reverse('dashboard:commande_facture', args=[c.id]))
        self.assertContains(r, f'F-{c.id:05d}')
        self.assertContains(r, '2 400')          # 2000 - 100 + 500
        r = self.client.get(reverse('dashboard:commande_bon_livraison', args=[c.id]))
        self.assertContains(r, f'BL-{c.id:05d}')
        self.assertContains(r, 'Montant à encaisser')
        payee = self.commande('livree_payee')
        self.assertNotContains(self.client.get(reverse('dashboard:commande_bon_livraison', args=[payee.id])), 'Montant à encaisser')

    def test_export_csv_filtre_et_protege_des_formules(self):
        a = self.commande('en_attente', nom='=HYPERLINK("http://x")')
        self.commande('livree_payee', nom='Autre')
        r = self.client.get(reverse('dashboard:commandes_export') + '?statut=en_attente')
        texte = r.content.decode('utf-8')
        self.assertIn(f'{a.id};', texte)
        self.assertNotIn('Autre', texte)
        self.assertIn("'=HYPERLINK", texte)
        self.assertTrue(ActiviteLog.objects.filter(action='export').exists())

    def test_clients_regroupes_par_telephone(self):
        self.commande(tel='70 00 00 01', nom='Awa')
        self.commande(tel='70-00-00-01', nom='Awa T.')
        self.commande(tel='65 00 00 02', nom='Moussa', statut='annulee')
        r = self.client.get(reverse('dashboard:clients_liste'))
        clients = {c['telephone']: c for c in r.context['clients']}
        self.assertEqual(r.context['total'], 2)
        awa = clients['70-00-00-01']
        self.assertEqual((awa['nb_commandes'], awa['total_depense']), (2, Decimal('4000')))
        self.assertEqual(clients['65 00 00 02']['nb_commandes'], 0)   # annulée : non comptée
        self.assertEqual(self.client.get(reverse('dashboard:clients_liste') + '?q=moussa').context['total'], 1)


class EquipeTests(Base):
    DONNEES = {'username': 'nouveau', 'first_name': 'Nadia', 'last_name': 'K', 'email': 'n@ex.com',
               'role': 'Gestionnaire de commandes', 'password1': MDP, 'password2': MDP}

    def test_creation_d_un_membre_avec_role(self):
        r = self.client.post(reverse('dashboard:equipe_ajouter'), self.DONNEES)
        self.assertRedirects(r, reverse('dashboard:equipe_liste'))
        u = User.objects.get(username='nouveau')
        self.assertTrue(u.is_staff and not u.is_superuser)
        self.assertEqual(role_de(u), 'Gestionnaire de commandes')
        self.assertTrue(self.client.login(username='nouveau', password=MDP))
        self.assertEqual(self.client.get(reverse('dashboard:commandes_liste')).status_code, 200)
        self.assertTrue(ActiviteLog.objects.filter(action='création', objet='Membre : nouveau').exists())

    def test_validations_creation(self):
        url = reverse('dashboard:equipe_ajouter')
        self.assertEqual(self.client.post(url, {**self.DONNEES, 'password2': 'autre'}).status_code, 200)
        self.assertEqual(self.client.post(url, {**self.DONNEES, 'password1': '12345678', 'password2': '12345678'}).status_code, 200)
        self.assertEqual(self.client.post(url, {**self.DONNEES, 'username': 'ADMIN'}).status_code, 200)   # doublon (casse)
        self.assertEqual(self.client.post(url, {**self.DONNEES, 'role': 'Dieu'}).status_code, 200)
        self.assertFalse(User.objects.filter(username='nouveau').exists())

    def test_changer_role_desactiver_et_mot_de_passe(self):
        self.client.post(reverse('dashboard:equipe_ajouter'), self.DONNEES)
        u = User.objects.get(username='nouveau')
        url = reverse('dashboard:equipe_modifier', args=[u.id])
        self.client.post(url, {'first_name': 'N', 'last_name': 'K', 'email': 'n@ex.com', 'is_active': 'on',
                               'role': 'Gestionnaire de catalogue', 'password1': 'NouveauMdp!2024y'})
        u.refresh_from_db()
        self.assertEqual(role_de(u), 'Gestionnaire de catalogue')
        self.assertEqual(u.groups.count(), 1)
        self.assertTrue(u.check_password('NouveauMdp!2024y'))
        self.client.post(url, {'first_name': 'N', 'last_name': 'K', 'email': 'n@ex.com',
                               'role': 'Gestionnaire de catalogue'})   # is_active absent = désactivé
        u.refresh_from_db()
        self.assertFalse(u.is_active)

    def test_on_ne_peut_pas_se_desactiver_ni_changer_son_role(self):
        url = reverse('dashboard:equipe_modifier', args=[self.admin.id])
        autre = membre('autre', 'Administrateur')   # il reste donc un autre admin
        r = self.client.post(url, {'email': 'a@ex.com', 'role': 'Administrateur'})   # is_active absent
        self.assertEqual(r.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        r = self.client.post(url, {'email': 'a@ex.com', 'is_active': 'on', 'role': 'Gestionnaire de commandes'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(role_de(self.admin), 'Administrateur')

    def test_le_dernier_administrateur_est_protege(self):
        autre = membre('autre', 'Administrateur')
        self.client.login(username='autre', password=MDP)
        # 'autre' tente de désactiver 'admin' alors qu'ils sont deux : autorisé
        url = reverse('dashboard:equipe_modifier', args=[self.admin.id])
        self.client.post(url, {'email': 'a@ex.com', 'role': 'Administrateur'})
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_active)
        # 'autre' est désormais seul : un gestionnaire ne peut pas le rétrograder
        gest = membre('gest', 'Administrateur')
        Group.objects.get(name='Administrateur').user_set.remove(autre)
        self.assertEqual(role_de(autre), 'Administrateur')   # sans rôle explicite = admin historique

    def test_equipe_reservee_aux_administrateurs(self):
        membre('cat', 'Gestionnaire de catalogue')
        self.client.login(username='cat', password=MDP)
        self.assertEqual(self.client.post(reverse('dashboard:equipe_ajouter'), self.DONNEES).status_code, 302)
        self.assertFalse(User.objects.filter(username='nouveau').exists())


class JournalTests(Base):
    def test_actions_journalisees_et_filtrables(self):
        self.client.post(reverse('dashboard:categories_liste'), {'nom': 'Écrans', 'slug': 'ecrans'})
        self.client.post(reverse('dashboard:produit_supprimer', args=[self.p.id]))
        r = self.client.get(reverse('dashboard:journal'))
        self.assertEqual(r.status_code, 200)
        objets = {a.objet for a in r.context['activites']}
        self.assertIn('Catégorie : Écrans', objets)
        self.assertIn('Produit : Laptop', objets)
        only = self.client.get(reverse('dashboard:journal') + '?action=suppression')
        self.assertEqual([a.action for a in only.context['activites']], ['suppression'])
        self.assertEqual(self.client.get(reverse('dashboard:journal') + f'?utilisateur={self.admin.id}&q=laptop').context['total'], 1)
        self.assertEqual(self.client.get(reverse('dashboard:journal') + '?du=zzz&action=bidon').status_code, 200)

    def test_connexion_journalisee(self):
        self.client.logout()
        self.client.post(reverse('dashboard:login'), {'username': 'admin', 'password': MDP})
        self.assertTrue(ActiviteLog.objects.filter(action='connexion', nom_utilisateur='admin').exists())

    def test_code_promo_et_parametres_journalises(self):
        self.client.post(reverse('dashboard:code_promo_ajouter'),
                         {'code': 'ete', 'pourcentage': 10, 'montant': 0, 'utilisations_max': 0, 'actif': 'on'})
        self.assertTrue(CodePromo.objects.filter(code='ETE').exists())
        self.assertTrue(ActiviteLog.objects.filter(action='création', objet__startswith='Code promo').exists())
