import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from produits.models import Produit
from dashboard.models import SiteSettings


class Command(BaseCommand):
    help = "Initialise le catalogue de produits, les catégories et les paramètres du site si la base est vide."

    def handle(self, *args, **options):
        # Si des produits existent déjà, on ne touche à rien
        nb_produits = Produit.objects.count()
        if nb_produits > 0:
            self.stdout.write(self.style.SUCCESS(f"Base de donnees deja initialisee ({nb_produits} produits)."))
            return

        fixture_path = 'initial_data.json'
        if os.path.exists(fixture_path):
            self.stdout.write("Chargement du catalogue initial depuis initial_data.json...")
            try:
                call_command('loaddata', fixture_path)
                self.stdout.write(self.style.SUCCESS("Catalogue initial et utilisateurs charges avec succes !"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Avertissement loaddata: {e}"))
        else:
            self.stdout.write(self.style.WARNING("Fichier initial_data.json introuvable."))

        # S'assurer que les paramètres du site (Sack-Tech, téléphone, etc.) sont bien configurés
        try:
            settings_obj = SiteSettings.get_settings()
            modifie = False
            if not settings_obj.site_nom or settings_obj.site_nom == 'TechShop':
                settings_obj.site_nom = 'Sack-Tech'
                modifie = True
            if not settings_obj.telephone:
                settings_obj.telephone = '93012582'
                modifie = True
            if not settings_obj.whatsapp_number:
                settings_obj.whatsapp_number = '93012582'
                modifie = True
            if not settings_obj.email:
                settings_obj.email = 'mahamadousacko599@gmail.com'
                modifie = True
            if not settings_obj.adresse:
                settings_obj.adresse = 'Golf'
                modifie = True
            if not settings_obj.logo:
                logo_rel = 'settings/WhatsApp_Image_2026-09-30_at_10.53.26.jpeg'
                if os.path.exists(os.path.join('media', logo_rel)):
                    settings_obj.logo = logo_rel
                    modifie = True
            if modifie:
                settings_obj.save()
                self.stdout.write(self.style.SUCCESS("Parametres du site Sack-Tech configures."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Avertissement SiteSettings: {e}"))
