from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('csrf/', views.csrf),
    path('site/', views.site),
    path('accueil/', views.accueil),
    path('produits/', views.produits),
    path('produits/<slug:slug>/', views.produit_detail),
    path('produits/<slug:slug>/avis/', views.avis_creer),
    path('recherche/', views.recherche),
    path('favoris/<int:produit_id>/', views.favori_basculer),
    path('panier/', views.panier_voir),
    path('panier/ajouter/', views.panier_ajouter),
    path('panier/<int:produit_id>/modifier/', views.panier_modifier),
    path('panier/<int:produit_id>/supprimer/', views.panier_supprimer),
    path('commandes/', views.commande_creer),
    path('commandes/<int:commande_id>/', views.commande_detail),
    path('contact/', views.contact),
]
