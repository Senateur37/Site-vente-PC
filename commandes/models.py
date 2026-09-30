from django.db import models
from django.conf import settings
from produits.models import Produit


class CodePromo(models.Model):
    code = models.CharField(max_length=30, unique=True, verbose_name="Code")
    pourcentage = models.PositiveSmallIntegerField(
        default=0,
        help_text="Réduction en pourcentage (ex: 10 = -10%)",
    )
    montant = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Réduction en montant fixe (FCFA). Ignoré si pourcentage > 0.",
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    utilisations_max = models.PositiveIntegerField(default=0, help_text="0 = illimité")
    utilisations = models.PositiveIntegerField(default=0, editable=False)
    date_expiration = models.DateField(null=True, blank=True, verbose_name="Expiration")

    class Meta:
        verbose_name = "Code promo"
        verbose_name_plural = "Codes promo"

    def __str__(self):
        return self.code

    @property
    def valide(self):
        from django.utils import timezone
        if not self.actif:
            return False
        if self.utilisations_max and self.utilisations >= self.utilisations_max:
            return False
        if self.date_expiration and self.date_expiration < timezone.now().date():
            return False
        return True

    def calculer_reduction(self, montant):
        """Retourne le montant de réduction pour un total donné."""
        if not self.valide:
            return 0
        if self.pourcentage:
            return (montant * self.pourcentage) / 100
        return min(self.montant, montant)


class Commande(models.Model):
    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("en_livraison", "En cours de livraison"),
        ("livree_payee", "Livrée et payée"),
        ("annulee", "Annulée"),
    ]
    PAIEMENT_CHOICES = [
        ("a_la_livraison", "Paiement à la livraison"),
        ("mobile_money", "Mobile Money (Orange/Moov/MTN via CinetPay)"),
        ("carte_bancaire", "Carte bancaire (via CinetPay)"),
    ]
    PAIEMENT_STATUT_CHOICES = [
        ("non_requis", "Paiement à la livraison"),
        ("en_attente", "Paiement en attente"),
        ("paye", "Payé en ligne"),
        ("echoue", "Paiement échoué"),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commandes",
        verbose_name="Client",
    )
    nom_client = models.CharField(max_length=150)
    telephone = models.CharField(max_length=30)
    email = models.EmailField(blank=True, verbose_name="Email (pour confirmation)")
    adresse = models.TextField()
    note = models.TextField(blank=True, help_text="Instructions supplémentaires pour la livraison")
    methode_paiement = models.CharField(
        max_length=20, choices=PAIEMENT_CHOICES, default="a_la_livraison",
        verbose_name="Méthode de paiement",
    )
    paiement_statut = models.CharField(
        max_length=20, choices=PAIEMENT_STATUT_CHOICES, default="non_requis",
        verbose_name="Statut du paiement en ligne",
    )
    transaction_id = models.CharField(max_length=60, blank=True, db_index=True)
    code_promo = models.ForeignKey(
        CodePromo, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Code promo appliqué",
    )
    reduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    frais_livraison = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_attente")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Commande #{self.id} - {self.nom_client}"

    @property
    def sous_total(self):
        return sum(ligne.sous_total for ligne in self.lignes.all())

    @property
    def total(self):
        return self.sous_total - self.reduction + self.frais_livraison


class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="lignes")
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True)
    nom_produit = models.CharField(max_length=200)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    quantite = models.PositiveIntegerField(default=1)

    @property
    def sous_total(self):
        return self.prix_unitaire * self.quantite

    def __str__(self):
        return f"{self.nom_produit} x{self.quantite}"