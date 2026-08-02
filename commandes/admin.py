from django.contrib import admin
from .models import Commande, LigneCommande, CodePromo

class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 0

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ['id', 'nom_client', 'utilisateur', 'telephone', 'statut', 'total', 'date_creation']
    list_filter = ['statut', 'methode_paiement']
    search_fields = ['nom_client', 'telephone', 'email']
    inlines = [LigneCommandeInline]

@admin.register(CodePromo)
class CodePromoAdmin(admin.ModelAdmin):
    list_display = ['code', 'pourcentage', 'montant', 'actif', 'utilisations', 'utilisations_max', 'date_expiration']
    list_filter = ['actif']