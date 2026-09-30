from django.core import mail
from django.core.cache import cache
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import Avis, Categorie, Produit


class BoutiqueTests(TestCase):
    def setUp(self):
        cache.clear()
        cat = Categorie.objects.create(nom="PC", slug="pc")
        self.p = Produit.objects.create(nom="Laptop Pro", slug="laptop-pro", categorie=cat, prix=1000, stock=5)
        Produit.objects.create(nom="Caché", slug="cache", categorie=cat, prix=5, stock=1, disponible=False)

    def test_liste_et_detail(self):
        r = self.client.get(reverse('produits:liste'))
        self.assertContains(r, "Laptop Pro")
        self.assertNotContains(r, "Caché")
        self.assertEqual(self.client.get(self.p.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(reverse('produits:detail', args=['cache'])).status_code, 404)

    def test_note_moyenne_ignore_avis_non_approuves(self):
        Avis.objects.create(produit=self.p, auteur='a', note=5, approuve=True)
        Avis.objects.create(produit=self.p, auteur='b', note=3, approuve=True)
        Avis.objects.create(produit=self.p, auteur='c', note=1, approuve=False)
        self.assertEqual(self.p.note_moyenne, 4.0)
        self.assertEqual(self.p.nb_avis, 2)
        annote = Produit.objects.avec_notes().get(pk=self.p.pk)
        self.assertEqual((annote.note_moyenne, annote.nb_avis), (4.0, 2))

    def test_nombre_de_requetes_independant_du_nombre_de_produits(self):
        with CaptureQueriesContext(connection) as avant:
            self.client.get(reverse('produits:liste'))
        for i in range(10):
            p = Produit.objects.create(nom=f"P{i}", slug=f"p{i}", categorie=self.p.categorie, prix=10, stock=1)
            Avis.objects.create(produit=p, auteur='a', note=4, approuve=True)
        with CaptureQueriesContext(connection) as apres:
            self.client.get(reverse('produits:liste'))
        self.assertLessEqual(len(apres), len(avant) + 1)

    def test_avis_en_attente_de_moderation(self):
        self.client.post(self.p.get_absolute_url(), {'note': 5, 'auteur': 'Moi', 'commentaire': 'Top'})
        self.assertFalse(Avis.objects.get().approuve)

    def test_avis_robot_ignore(self):
        self.client.post(self.p.get_absolute_url(), {'note': 5, 'auteur': 'Bot', 'site_web': 'http://spam'})
        self.assertEqual(Avis.objects.count(), 0)

    def test_avis_limite_par_ip(self):
        for _ in range(7):
            self.client.post(self.p.get_absolute_url(), {'note': 5, 'auteur': 'Moi', 'commentaire': 'x'})
        self.assertEqual(Avis.objects.count(), 5)

    def test_contact(self):
        d = {'nom': 'Awa', 'email': 'awa@ex.com', 'sujet': 'Hi\nBcc: x@y.z', 'message': 'Bonjour'}
        self.client.post(reverse('produits:contact'), d)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn('\n', mail.outbox[0].subject)

    def test_contact_email_invalide_ou_robot(self):
        self.client.post(reverse('produits:contact'), {'nom': 'A', 'email': 'pasunemail', 'message': 'x'})
        self.client.post(reverse('produits:contact'), {'nom': 'A', 'email': 'a@b.co', 'message': 'x', 'site_web': 'spam'})
        self.assertEqual(len(mail.outbox), 0)
