from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from produits.models import Categorie, Produit
from .models import CodePromo, Commande


def _produit(stock=5, prix=1000):
    cat = Categorie.objects.create(nom="PC", slug="pc")
    return Produit.objects.create(nom="Laptop", categorie=cat, prix=prix, stock=stock, disponible=True)


DONNEES = {
    'nom_client': 'Awa', 'telephone': '70000000', 'email': '',
    'adresse': 'Quartier X', 'note': '', 'methode_paiement': 'a_la_livraison',
}


class PanierTests(TestCase):
    def setUp(self):
        self.p = _produit(stock=3)

    def test_ajout_get_refuse(self):
        r = self.client.get(reverse('commandes:ajouter', args=[self.p.id]))
        self.assertEqual(r.status_code, 405)

    def test_quantite_invalide_ne_plante_pas(self):
        r = self.client.post(reverse('commandes:ajouter', args=[self.p.id]), {'quantite': 'abc'})
        self.assertEqual(r.status_code, 302)

    def test_quantite_limitee_au_stock(self):
        self.client.post(reverse('commandes:ajouter', args=[self.p.id]), {'quantite': 99})
        self.assertEqual(self.client.session['panier'][str(self.p.id)]['quantite'], 3)


class CommandeTests(TestCase):
    def setUp(self):
        self.p = _produit(stock=3)
        self.client.post(reverse('commandes:ajouter', args=[self.p.id]), {'quantite': 2})

    def test_commande_decremente_stock_et_confirmation_protegee(self):
        r = self.client.post(reverse('commandes:passer_commande'), DONNEES)
        c = Commande.objects.get()
        self.assertRedirects(r, reverse('commandes:confirmation', args=[c.id]))
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 1)
        self.assertEqual(c.total, Decimal('2000'))
        # un autre visiteur ne peut pas lire la confirmation
        from django.test import Client
        self.assertEqual(Client().get(reverse('commandes:confirmation', args=[c.id])).status_code, 404)
        self.assertEqual(self.client.get(reverse('commandes:confirmation', args=[c.id])).status_code, 200)

    def test_stock_insuffisant_bloque_la_commande(self):
        Produit.objects.filter(pk=self.p.pk).update(stock=1)
        self.client.post(reverse('commandes:passer_commande'), DONNEES)
        self.assertEqual(Commande.objects.count(), 0)

    def test_code_promo_incremente_utilisations(self):
        CodePromo.objects.create(code='PROMO10', pourcentage=10)
        self.client.post(reverse('commandes:passer_commande'), {**DONNEES, 'code_promo': 'promo10'})
        c = Commande.objects.get()
        self.assertEqual(c.reduction, Decimal('200'))
        self.assertEqual(CodePromo.objects.get().utilisations, 1)


from unittest import mock

from django.test import override_settings

from . import cinetpay


@override_settings(CINETPAY_ACTIF=True, CINETPAY_API_KEY='k', CINETPAY_SITE_ID='s', SITE_URL='https://ex.com')
class PaiementEnLigneTests(TestCase):
    def setUp(self):
        self.p = _produit(stock=3, prix=1000)
        self.client.post(reverse('commandes:ajouter', args=[self.p.id]), {'quantite': 1})
        self.client.post(reverse('commandes:passer_commande'), {**DONNEES, 'methode_paiement': 'mobile_money'})
        self.c = Commande.objects.get()

    def test_commande_en_ligne_en_attente_de_paiement(self):
        self.assertEqual(self.c.paiement_statut, 'en_attente')
        self.assertTrue(self.c.transaction_id.startswith(f'TS{self.c.id}-'))

    def test_redirection_vers_cinetpay(self):
        with mock.patch.object(cinetpay, 'initier_paiement', return_value='https://pay.cinetpay.test/x'):
            r = self.client.get(reverse('commandes:payer', args=[self.c.id]))
        self.assertRedirects(r, 'https://pay.cinetpay.test/x', fetch_redirect_response=False)

    def test_webhook_valide_aupres_de_l_api(self):
        url = reverse('commandes:notification_paiement')
        with mock.patch.object(cinetpay, 'verifier_paiement', return_value=(False, None)):
            self.client.post(url, {'cpm_trans_id': self.c.transaction_id})
        self.c.refresh_from_db()
        self.assertEqual(self.c.paiement_statut, 'echoue')
        self.c.paiement_statut = 'en_attente'
        self.c.save()
        with mock.patch.object(cinetpay, 'verifier_paiement', return_value=(True, 1000)):
            self.client.post(url, {'cpm_trans_id': self.c.transaction_id})
        self.c.refresh_from_db()
        self.assertEqual(self.c.paiement_statut, 'paye')

    def test_webhook_montant_insuffisant_ne_valide_pas(self):
        with mock.patch.object(cinetpay, 'verifier_paiement', return_value=(True, 5)):
            self.client.post(reverse('commandes:notification_paiement'), {'cpm_trans_id': self.c.transaction_id})
        self.c.refresh_from_db()
        self.assertEqual(self.c.paiement_statut, 'en_attente')

    def test_webhook_transaction_inconnue(self):
        r = self.client.post(reverse('commandes:notification_paiement'), {'cpm_trans_id': 'nope'})
        self.assertEqual(r.status_code, 404)


class PaiementDesactiveTests(TestCase):
    def test_options_en_ligne_masquees_sans_cinetpay(self):
        from .forms import CommandeForm
        valeurs = [v for v, _ in CommandeForm().fields['methode_paiement'].choices]
        self.assertEqual(valeurs, ['a_la_livraison'])
