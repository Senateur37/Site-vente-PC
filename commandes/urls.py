from django.urls import path
from . import views

app_name = 'commandes'

urlpatterns = [
    path('panier/', views.voir_panier, name='voir_panier'),
    path('panier/ajouter/<int:produit_id>/', views.ajouter_au_panier, name='ajouter'),
    path('panier/modifier/<int:produit_id>/', views.modifier_panier, name='modifier'),
    path('panier/supprimer/<int:produit_id>/', views.supprimer_du_panier, name='supprimer'),
    path('commander/', views.passer_commande, name='passer_commande'),
    path('paiement/<int:commande_id>/', views.payer_commande, name='payer'),
    path('paiement/notification/', views.notification_paiement, name='notification_paiement'),
    path('confirmation/<int:commande_id>/', views.confirmation_commande, name='confirmation'),
]