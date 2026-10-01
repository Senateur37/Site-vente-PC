import os
import sys
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techshop.settings')
django.setup()

from produits.models import Produit, Categorie, SectionAccueil

cat_ordinateurs, _ = Categorie.objects.get_or_create(nom="Ordinateurs", slug="ordinateurs")
cat_accessoires, _ = Categorie.objects.get_or_create(nom="Accessoires", slug="accessoires")
cat_composants, _ = Categorie.objects.get_or_create(nom="Composants", slug="composants")
cat_smartphones, _ = Categorie.objects.get_or_create(nom="Smartphones", slug="smartphones")

produits_data = [
    ("MacBook Pro M3 Max", cat_ordinateurs, "apple", "850000", True, 15),
    ("Dell XPS 15 2026", cat_ordinateurs, "dell", "750000", True, 8),
    ("Lenovo ThinkPad X1", cat_ordinateurs, "lenovo", "650000", False, 12),
    ("Souris Logitech MX Master 3S", cat_accessoires, "logitech", "65000", True, 50),
    ("Clavier Mécanique Keychron K8", cat_accessoires, "autre", "75000", False, 30),
    ("Casque Sony WH-1000XM5", cat_accessoires, "sony", "195000", True, 20),
    ("Samsung Galaxy S24 Ultra", cat_smartphones, "samsung", "650000", True, 25),
    ("iPhone 15 Pro Max", cat_smartphones, "apple", "750000", True, 10),
    ("Carte Graphique NVIDIA RTX 4090", cat_composants, "autre", "1250000", False, 2),
    ("Processeur AMD Ryzen 9", cat_composants, "autre", "350000", False, 5),
    ("Ecran Dell UltraSharp 32", cat_ordinateurs, "dell", "450000", True, 7),
    ("Tablette iPad Pro", cat_smartphones, "apple", "550000", True, 18),
]

for p in produits_data:
    nom, cat, marque, prix, a_la_une, stock = p
    produit, created = Produit.objects.get_or_create(
        nom=nom,
        defaults={
            'slug': nom.lower().replace(' ', '-').replace(',', ''),
            'categorie': cat,
            'marque': marque,
            'prix': Decimal(prix),
            'description': f"Superbe produit de la marque {marque}. Achetez-le dès maintenant sur TechShop Bamako !",
            'disponible': True,
            'stock': stock,
            'a_la_une': a_la_une,
        }
    )
    if not created:
        produit.a_la_une = a_la_une
        produit.stock = stock
        produit.categorie = cat
        produit.save()

# Création de quelques sections d'accueil pour bien voir
SectionAccueil.objects.get_or_create(
    titre="Nouveautés Apple",
    type_section="marque",
    marque="apple",
    ordre=1,
    active=True
)
SectionAccueil.objects.get_or_create(
    titre="L'univers PC",
    type_section="categorie",
    categorie=cat_ordinateurs,
    ordre=2,
    active=True
)

print(f"Base de données peuplée. Total produits: {Produit.objects.count()}")
