from datetime import timedelta

from django.db import models
from django.db.models import Avg, Count, Q
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from dashboard.models import validate_image_file


class SectionAccueil(models.Model):
    TYPE_SECTION = [
        ('meilleures_ventes', 'Meilleures ventes'),
        ('nouveautes', 'Nouveautés'),
        ('plus_aimes', 'Produits les plus aimés'),
        ('categorie', 'Par catégorie'),
        ('marque', 'Par marque'),
        ('personnalise', 'Produits personnalisés'),
    ]
    MARQUE_CHOICES = [
        ("hp", "HP"),
        ("dell", "Dell"),
        ("lenovo", "Lenovo"),
        ("apple", "Apple"),
        ("asus", "Asus"),
        ("acer", "Acer"),
        ("samsung", "Samsung"),
        ("microsoft", "Microsoft"),
        ("autre", "Autre"),
    ]

    titre = models.CharField(max_length=200, verbose_name="Titre de la section")
    type_section = models.CharField(max_length=50, choices=TYPE_SECTION, verbose_name="Type de section")
    categorie = models.ForeignKey('Categorie', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Catégorie (si type = Par catégorie)")
    marque = models.CharField(max_length=50, choices=MARQUE_CHOICES, blank=True, verbose_name="Marque (si type = Par marque)")
    produits_personnalises = models.ManyToManyField('Produit', blank=True, verbose_name="Produits (si type = Personnalisés)")
    max_produits = models.PositiveSmallIntegerField(default=8, verbose_name="Nombre max de produits")
    afficher_voir_plus = models.BooleanField(default=True, verbose_name="Afficher 'Voir plus'")
    ordre = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre d'affichage")
    active = models.BooleanField(default=True, verbose_name="Active")

    class Meta:
        verbose_name = "Section accueil"
        verbose_name_plural = "Sections accueil"
        ordering = ['ordre']

    def __str__(self):
        return self.titre


class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class ProduitQuerySet(models.QuerySet):
    def avec_notes(self):
        """Annote note moyenne et nombre d'avis approuvés (évite une requête par carte produit)."""
        ok = Q(avis__approuve=True)
        return self.annotate(
            _note_moy=Avg('avis__note', filter=ok),
            _nb_avis=Count('avis', filter=ok),
        )


class Produit(models.Model):
    MARQUE_CHOICES = [
        ("hp", "HP"),
        ("dell", "Dell"),
        ("lenovo", "Lenovo"),
        ("apple", "Apple"),
        ("asus", "Asus"),
        ("acer", "Acer"),
        ("samsung", "Samsung"),
        ("microsoft", "Microsoft"),
        ("autre", "Autre"),
    ]
        
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name="produits")
    marque = models.CharField(max_length=50, choices=MARQUE_CHOICES, blank=True)
    nom = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    prix_barre = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Prix barré (promotion)")
    image = models.ImageField(upload_to="produits/", blank=True, null=True, validators=[validate_image_file])
    stock = models.PositiveIntegerField(default=0)
    disponible = models.BooleanField(default=True)
    a_la_une = models.BooleanField(
        default=False,
        verbose_name="Produit à la une (section statique)",
        help_text="Cochez pour afficher ce produit en permanence dans la section « À la une » de la boutique.",
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    objects = ProduitQuerySet.as_manager()

    class Meta:
        ordering = ["-date_ajout"]

    def __str__(self):
        return self.nom

    def get_absolute_url(self):
        return reverse("produits:detail", args=[self.slug])

    @property
    def note_moyenne(self):
        if hasattr(self, '_note_moy'):
            return round(self._note_moy, 1) if self._note_moy else 0
        moyenne = self.avis.filter(approuve=True).aggregate(m=Avg('note'))['m']
        return round(moyenne, 1) if moyenne else 0

    @property
    def nb_avis(self):
        if hasattr(self, '_nb_avis'):
            return self._nb_avis
        return self.avis.filter(approuve=True).count()

    @property
    def en_stock(self):
        return self.stock > 0

    @property
    def en_promo(self):
        return self.prix_barre is not None and self.prix_barre > self.prix

    @property
    def est_nouveau(self):
        return self.date_ajout >= timezone.now() - timedelta(days=7)

    @property
    def pourcentage_reduction(self):
        if self.en_promo and self.prix_barre:
            reduction = ((self.prix_barre - self.prix) / self.prix_barre) * 100
            return round(reduction)
        return 0

    @property
    def images_galerie(self):
        images = []
        if self.image:
            images.append({"url": self.image.url, "alt": self.nom})
        for img in self.images_supplementaires.all():
            images.append({"url": img.image.url, "alt": img.legende or self.nom})
        return images


class ImageProduit(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="images_supplementaires")
    image = models.ImageField(upload_to="produits/galerie/", validators=[validate_image_file])
    legende = models.CharField(max_length=200, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["ordre", "id"]
        verbose_name = "Image produit"
        verbose_name_plural = "Images produit"

    def __str__(self):
        return f"Image {self.ordre} — {self.produit.nom}"


class Avis(models.Model):
    NOTE_CHOICES = [(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)]

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="avis")
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avis",
    )
    auteur = models.CharField(max_length=150, verbose_name="Nom")
    note = models.PositiveSmallIntegerField(choices=NOTE_CHOICES, verbose_name="Note")
    commentaire = models.TextField(blank=True, verbose_name="Commentaire")
    approuve = models.BooleanField(default=False, verbose_name="Approuvé")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.auteur} — {self.note}/5 — {self.produit.nom}"


class Favori(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="favoris")
    session_id = models.CharField(max_length=100, blank=True)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="favoris",
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Favori"
        verbose_name_plural = "Favoris"
        constraints = [
            models.UniqueConstraint(
                fields=["produit", "session_id"],
                condition=models.Q(session_id__gt=''),
                name="unique_favori_session",
            ),
            models.UniqueConstraint(
                fields=["produit", "utilisateur"],
                condition=models.Q(utilisateur__isnull=False),
                name="unique_favori_utilisateur",
            ),
        ]

    def __str__(self):
        return f"Favori : {self.produit.nom}"


class LogoMarque(models.Model):
    """
    Associe une photo/logo à chaque marque (valeurs de Produit.MARQUE_CHOICES).
    Table séparée : aucune migration nécessaire sur le champ Produit.marque existant.
    Le client peut gérer les logos directement depuis l'admin Django.
    """
    marque = models.CharField(
        max_length=50,
        choices=Produit.MARQUE_CHOICES,
        unique=True,
        verbose_name="Marque",
    )
    photo = models.ImageField(
        upload_to="marques/",
        verbose_name="Logo / photo de la marque",
    )

    class Meta:
        verbose_name = "Logo de marque"
        verbose_name_plural = "Logos de marques"
        ordering = ["marque"]

    def __str__(self):
        return self.get_marque_display()