import os
from PIL import Image

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models


def validate_image_file(value):
    """Valide que le fichier est une image autorisée (extension + MIME)."""
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.svg']
    if ext not in valid_extensions:
        raise ValidationError(f"Extension '{ext}' non autorisée. Utilisez: {', '.join(valid_extensions)}")
    
    valid_mime_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/avif', 'image/svg+xml']
    if hasattr(value, 'content_type'):
        if value.content_type not in valid_mime_types:
            raise ValidationError(f"Type MIME '{value.content_type}' non autorisé.")
    
    # Vérification du fichier image
    if value.size > 0:
        if ext not in ['.svg', '.avif']:
            try:
                value.seek(0)
                img = Image.open(value)
                img.verify()
                value.seek(0)
            except Exception:
                raise ValidationError("Le fichier ne semble pas être une image valide.")
    
    # Limite de taille : 5 Mo
    if value.size > 5 * 1024 * 1024:
        raise ValidationError("L'image ne doit pas dépasser 5 Mo.")


class SiteSettings(models.Model):
    # Identifiant unique (on utilise le pattern singleton)
    id = models.BigAutoField(primary_key=True)

    # Site
    site_nom = models.CharField(max_length=100, default="TechShop")
    site_description = models.CharField(max_length=255, blank=True, default="Ordinateurs & accessoires")

    # Logo & Favicon
    logo = models.ImageField(upload_to="settings/", blank=True, null=True, validators=[validate_image_file], help_text="Logo du site (PNG recommandé)")
    favicon = models.ImageField(upload_to="settings/", blank=True, null=True, validators=[validate_image_file], help_text="Icône du site (32x32px)")

    # Bannière de la boutique (1200x400px — créez-la sur Canva)
    banniere = models.ImageField(upload_to="settings/", blank=True, null=True, validators=[validate_image_file], help_text="Image bannière 1200x400px")

    # Couleurs
    accent_couleur = models.CharField(max_length=7, default="#2563eb", verbose_name="Couleur principale")
    accent_sombre = models.CharField(max_length=7, default="#1d4ed8", verbose_name="Couleur foncée")
    surface_couleur = models.CharField(max_length=7, default="#f8fafc", verbose_name="Couleur de surface")

    # Monnaie
    monnaie_symbole = models.CharField(max_length=10, default="FCFA", verbose_name="Symbole monétaire")
    monnaie_code = models.CharField(max_length=3, default="XOF", verbose_name="Code ISO")

    # Contact
    telephone = models.CharField(max_length=50, blank=True, default="")
    adresse = models.TextField(blank=True, default="")
    email = models.EmailField(blank=True, default="")

    # Footer
    footer_texte = models.CharField(max_length=255, blank=True, default="Paiement à la livraison sur Abidjan.")
    copyright_texte = models.CharField(max_length=255, blank=True, default="TechShop — Ordinateurs & accessoires.")

    # Livraison
    livraison_prix_fixe = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Frais de livraison fixes (FCFA)",
    )
    livraison_gratuite_des = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Livraison gratuite à partir de (FCFA)",
        help_text="0 = jamais de livraison gratuite.",
    )

    # Mode sombre par défaut
    mode_sombre_defaut = models.BooleanField(default=False, verbose_name="Mode sombre par défaut")

    # Social
    facebook_url = models.URLField(blank=True, default="")
    instagram_url = models.URLField(blank=True, default="")
    whatsapp_number = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        verbose_name = "Paramètres du site"
        verbose_name_plural = "Paramètres du site"

    def __str__(self):
        return "Paramètres du site"

    CACHE_KEY = 'site_settings'

    @classmethod
    def get_settings(cls):
        """Singleton mis en cache (lu à chaque requête par un context processor)."""
        obj = cache.get(cls.CACHE_KEY)
        if obj is None:
            obj, _ = cls.objects.get_or_create(id=1)
            cache.set(cls.CACHE_KEY, obj, 300)
        return obj

    def save(self, *args, **kwargs):
        self.id = 1
        super().save(*args, **kwargs)
        cache.delete(self.CACHE_KEY)
