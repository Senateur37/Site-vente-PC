from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase

from commandes.models import Commande
from produits.models import Avis, Categorie, Produit


class ApiBase(TestCase):
    def setUp(self):
        cache.clear()
        self.cat = Categorie.objects.create(nom="PC", slug="pc")
        self.p = Produit.objects.create(
            nom="Laptop Pro", slug="laptop-pro", categorie=self.cat, prix=1000, stock=3, marque='hp')
        Produit.objects.create(nom="Caché", slug="cache", categorie=self.cat, prix=5, stock=1, disponible=False)

    def post(self, url, data=None, client=None):
        return (client or self.client).post(url, data or {}, content_type='application/json')


class CatalogueTests(ApiBase):
    def test_site_et_accueil(self):
        r = self.client.get('/api/site/').json()
        self.assertEqual(r['categories'][0]['slug'], 'pc')
        self.assertEqual([p['value'] for p in r['paiements']], ['a_la_livraison'])
        self.assertEqual(self.client.get('/api/accueil/').status_code, 200)

    def test_liste_filtre_et_masque_les_indisponibles(self):
        r = self.client.get('/api/produits/').json()
        self.assertEqual([p['slug'] for p in r['results']], ['laptop-pro'])
        self.assertEqual(r['results'][0]['prix'], 1000)
        self.assertEqual(self.client.get('/api/produits/?marque=dell').json()['count'], 0)
        self.assertEqual(self.client.get('/api/produits/?q=laptop&prix_max=2000').json()['count'], 1)
        self.assertEqual(self.client.get('/api/produits/?prix_min=abc').json()['count'], 1)

    def test_detail_avec_avis_approuves_seulement(self):
        Avis.objects.create(produit=self.p, auteur='a', note=5, approuve=True)
        Avis.objects.create(produit=self.p, auteur='b', note=1, approuve=False)
        d = self.client.get('/api/produits/laptop-pro/').json()
        self.assertEqual(len(d['avis']), 1)
        self.assertEqual(d['note_moyenne'], 5.0)
        self.assertEqual(self.client.get('/api/produits/cache/').status_code, 404)

    def test_recherche(self):
        self.assertEqual(self.client.get('/api/recherche/?q=l').json()['resultats'], [])
        self.assertEqual(len(self.client.get('/api/recherche/?q=lap').json()['resultats']), 1)

    def test_avis_moderation_et_robot(self):
        self.post('/api/produits/laptop-pro/avis/', {'note': 5, 'auteur': 'Moi', 'commentaire': 'Top'})
        self.assertFalse(Avis.objects.get().approuve)
        self.post('/api/produits/laptop-pro/avis/', {'note': 5, 'auteur': 'Bot', 'site_web': 'x'})
        self.assertEqual(Avis.objects.count(), 1)
        r = self.post('/api/produits/laptop-pro/avis/', {'note': 9, 'auteur': 'X'})
        self.assertEqual(r.status_code, 400)


class PanierEtCommandeTests(ApiBase):
    COMMANDE = {'nom_client': 'Awa', 'telephone': '70000000', 'email': 'awa@ex.com',
                'adresse': 'Quartier X', 'methode_paiement': 'a_la_livraison'}

    def test_panier_plafonne_au_stock(self):
        r = self.post('/api/panier/ajouter/', {'produit_id': self.p.id, 'quantite': 99}).json()
        self.assertEqual(r['count'], 3)
        r = self.post('/api/panier/ajouter/', {'produit_id': self.p.id, 'quantite': 1})
        self.assertEqual(r.status_code, 400)

    def test_quantite_invalide(self):
        r = self.post('/api/panier/ajouter/', {'produit_id': self.p.id, 'quantite': 'abc'})
        self.assertEqual(r.status_code, 200)

    def test_modifier_et_supprimer(self):
        self.post('/api/panier/ajouter/', {'produit_id': self.p.id, 'quantite': 1})
        r = self.post(f'/api/panier/{self.p.id}/modifier/', {'quantite': 2}).json()
        self.assertEqual(r['sous_total'], 2000)
        r = self.post(f'/api/panier/{self.p.id}/supprimer/').json()
        self.assertEqual(r['count'], 0)

    def test_commande_complete(self):
        self.post('/api/panier/ajouter/', {'produit_id': self.p.id, 'quantite': 2})
        r = self.post('/api/commandes/', self.COMMANDE)
        self.assertEqual(r.status_code, 201)
        cid = r.json()['id']
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 1)
        self.assertEqual(self.client.get('/api/panier/').json()['count'], 0)
        detail = self.client.get(f'/api/commandes/{cid}/').json()
        self.assertEqual(detail['total'], 2000)
        self.assertEqual(len(mail.outbox), 1)
        # un autre visiteur ne voit pas la commande
        self.assertEqual(Client().get(f'/api/commandes/{cid}/').status_code, 404)

    def test_commande_panier_vide_et_formulaire_invalide(self):
        self.assertEqual(self.post('/api/commandes/', self.COMMANDE).status_code, 400)
        self.post('/api/panier/ajouter/', {'produit_id': self.p.id})
        r = self.post('/api/commandes/', {'nom_client': ''})
        self.assertEqual(r.status_code, 400)
        self.assertIn('nom_client', r.json()['erreurs'])
        self.assertEqual(Commande.objects.count(), 0)

    def test_stock_insuffisant_renvoie_409(self):
        self.post('/api/panier/ajouter/', {'produit_id': self.p.id, 'quantite': 2})
        Produit.objects.filter(pk=self.p.pk).update(stock=1)
        r = self.post('/api/commandes/', self.COMMANDE)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(Commande.objects.count(), 0)


class ContactEtCsrfTests(ApiBase):
    def test_contact(self):
        r = self.post('/api/contact/', {'nom': 'A', 'email': 'a@b.co', 'sujet': 'Hi\nBcc: x', 'message': 'Yo'})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('\n', mail.outbox[0].subject)
        self.assertEqual(self.post('/api/contact/', {'nom': 'A', 'email': 'nope', 'message': 'Yo'}).status_code, 400)

    def test_csrf_exige_en_production(self):
        c = Client(enforce_csrf_checks=True)
        r = c.post('/api/panier/ajouter/', {'produit_id': self.p.id}, content_type='application/json')
        self.assertEqual(r.status_code, 403)
        token = c.get('/api/csrf/').json()['csrfToken']
        r = c.post('/api/panier/ajouter/', {'produit_id': self.p.id}, content_type='application/json',
                   HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code, 200)
