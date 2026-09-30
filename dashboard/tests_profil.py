"""Profil du membre connecté : identité, photo, mot de passe."""
import io
import os
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import ActiviteLog, ProfilStaff

MDP = 'MotDePasse!2024x'
MEDIA_TEST = tempfile.mkdtemp(prefix='media_test_')


def image(format='PNG', taille=(800, 400), nom='photo.png', mode='RGB'):
    tampon = io.BytesIO()
    Image.new(mode, taille, (200, 30, 30) if mode == 'RGB' else (200, 30, 30, 128)).save(tampon, format=format)
    return SimpleUploadedFile(nom, tampon.getvalue(), content_type=f'image/{format.lower()}')


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class ProfilTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user('awa', 'awa@ex.com', MDP, is_staff=True, first_name='Awa', last_name='T')
        self.client.login(username='awa', password=MDP)
        self.url = reverse('dashboard:profil')

    def poster(self, **extra):
        donnees = {'first_name': 'Awa', 'last_name': 'T', 'email': 'awa@ex.com'}
        donnees.update(extra)
        return self.client.post(self.url, donnees)

    def test_page_accessible_et_reservee_au_staff(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
        User.objects.create_user('client', 'c@ex.com', MDP)
        self.client.login(username='client', password=MDP)
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_le_menu_lateral_renvoie_vers_le_profil(self):
        html = self.client.get(reverse('dashboard:index')).content.decode()
        self.assertIn(f'href="{self.url}"', html)
        self.assertIn('Modifier mon profil et ma photo', html)

    def test_modifier_nom_et_email(self):
        r = self.poster(first_name='Aïcha', last_name='Keita', email='aicha@ex.com')
        self.assertRedirects(r, self.url)
        self.user.refresh_from_db()
        self.assertEqual((self.user.first_name, self.user.last_name, self.user.email), ('Aïcha', 'Keita', 'aicha@ex.com'))
        self.assertTrue(ActiviteLog.objects.filter(action='modification', objet='Profil : awa').exists())

    def test_email_invalide_refuse(self):
        self.assertEqual(self.poster(email='pasunemail').status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'awa@ex.com')

    def test_ajout_de_photo_recadree_en_carre_et_reduite(self):
        self.poster(photo=image(taille=(1600, 800)))
        fiche = ProfilStaff.objects.get(utilisateur=self.user)
        self.assertTrue(fiche.photo.name.startswith('profils/') and fiche.photo.name.endswith('.webp'))
        with Image.open(fiche.photo.path) as img:
            self.assertEqual(img.size, (512, 512))
            self.assertEqual(img.format, 'WEBP')
        # affichée dans le menu latéral
        self.assertContains(self.client.get(reverse('dashboard:index')), fiche.photo.url)

    def test_petite_image_et_png_transparent(self):
        self.poster(photo=image(taille=(60, 40), mode='RGBA'))
        fiche = ProfilStaff.objects.get(utilisateur=self.user)
        with Image.open(fiche.photo.path) as img:
            self.assertEqual(img.size, (512, 512))

    def test_remplacement_supprime_l_ancien_fichier(self):
        self.poster(photo=image())
        ancien = ProfilStaff.objects.get(utilisateur=self.user).photo.path
        self.assertTrue(os.path.exists(ancien))
        self.poster(photo=image(nom='autre.png'))
        fiche = ProfilStaff.objects.get(utilisateur=self.user)
        self.assertNotEqual(fiche.photo.path, ancien)
        self.assertFalse(os.path.exists(ancien))
        self.assertTrue(os.path.exists(fiche.photo.path))

    def test_suppression_de_la_photo(self):
        self.poster(photo=image())
        chemin = ProfilStaff.objects.get(utilisateur=self.user).photo.path
        self.poster(supprimer_photo='on')
        self.assertFalse(ProfilStaff.objects.get(utilisateur=self.user).photo)
        self.assertFalse(os.path.exists(chemin))

    def test_fichiers_dangereux_ou_invalides_refuses(self):
        svg = SimpleUploadedFile('x.svg', b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', 'image/svg+xml')
        faux = SimpleUploadedFile('x.png', b'ceci n est pas une image', 'image/png')
        html = SimpleUploadedFile('x.html', b'<script>alert(1)</script>', 'text/html')
        for fichier in (svg, faux, html):
            self.assertEqual(self.poster(photo=fichier).status_code, 200, fichier.name)
        self.assertFalse(ProfilStaff.objects.get(utilisateur=self.user).photo)

    def test_image_trop_lourde_refusee(self):
        gros = SimpleUploadedFile('gros.png', b'\x89PNG' + b'0' * (5 * 1024 * 1024 + 10), 'image/png')
        self.assertEqual(self.poster(photo=gros).status_code, 200)
        self.assertFalse(ProfilStaff.objects.get(utilisateur=self.user).photo)

    def test_changement_de_mot_de_passe_sans_deconnexion(self):
        r = self.client.post(self.url, {'action': 'mot_de_passe', 'old_password': MDP,
                                        'new_password1': 'NouveauMdp!2024y', 'new_password2': 'NouveauMdp!2024y'})
        self.assertRedirects(r, self.url)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NouveauMdp!2024y'))
        self.assertEqual(self.client.get(self.url).status_code, 200)   # toujours connecté

    def test_mot_de_passe_refuse_si_ancien_faux_ou_faible(self):
        for donnees in ({'old_password': 'faux', 'new_password1': 'NouveauMdp!2024y', 'new_password2': 'NouveauMdp!2024y'},
                        {'old_password': MDP, 'new_password1': '12345678', 'new_password2': '12345678'},
                        {'old_password': MDP, 'new_password1': 'NouveauMdp!2024y', 'new_password2': 'different'}):
            self.assertEqual(self.client.post(self.url, {'action': 'mot_de_passe', **donnees}).status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(MDP))

    def test_chaque_membre_ne_modifie_que_son_propre_profil(self):
        autre = User.objects.create_user('moussa', 'm@ex.com', MDP, is_staff=True, first_name='Moussa')
        self.poster(first_name='Pirate', photo=image())
        autre.refresh_from_db()
        self.assertEqual(autre.first_name, 'Moussa')
        self.assertFalse(ProfilStaff.objects.filter(utilisateur=autre, photo__gt='').exists())

    def test_la_liste_equipe_affiche_les_photos(self):
        from .roles import creer_groupes
        creer_groupes()
        self.poster(photo=image())
        self.user.is_superuser = True
        self.user.save()
        r = self.client.get(reverse('dashboard:equipe_liste'))
        self.assertContains(r, ProfilStaff.objects.get(utilisateur=self.user).photo.url)
