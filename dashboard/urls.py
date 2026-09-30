from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.connexion, name='login'),
    path('logout/', views.deconnexion, name='logout'),
    path('', views.index, name='index'),

    # Inscription (désactivée en production — seul l'admin crée les comptes)
    # path('inscription/', views.inscription, name='inscription'),

    # Password reset (code de vérification)
    path('mot-de-passe-oublie/', views.mot_de_passe_oublie, name='mot_de_passe_oublie'),
    path('mot-de-passe-oublie/code/', views.verifier_code, name='verifier_code'),
    path('mot-de-passe-oublie/nouveau/', views.nouveau_mot_de_passe, name='nouveau_mot_de_passe'),

    # Produits
    path('produits/', views.liste_produits, name='produits_liste'),
    path('produits/ajouter/', views.ajouter_produit, name='produit_ajouter'),
    path('produits/<int:produit_id>/modifier/', views.modifier_produit, name='produit_modifier'),
    path('produits/<int:produit_id>/supprimer/', views.supprimer_produit, name='produit_supprimer'),

    # Categories
    path('categories/', views.liste_categories, name='categories_liste'),
    path('categories/<int:categorie_id>/supprimer/', views.supprimer_categorie, name='categorie_supprimer'),

    # Marques
    path('marques/', views.liste_marques, name='marques_liste'),
    path('marques/<int:marque_id>/supprimer/', views.supprimer_marque, name='marque_supprimer'),

    # Commandes
    path('commandes/', views.liste_commandes, name='commandes_liste'),
    path('commandes/<int:commande_id>/', views.detail_commande, name='commande_detail'),
    path('commandes/export/', views.export_commandes, name='commandes_export'),

    # Avis
    path('avis/', views.liste_avis, name='avis_liste'),
    path('avis/<int:avis_id>/approuver/', views.approuver_avis, name='avis_approuver'),
    path('avis/<int:avis_id>/supprimer/', views.supprimer_avis, name='avis_supprimer'),

    # Clients
    path('clients/', views.liste_clients, name='clients_liste'),

    # Contenu du site affiché sur la vitrine
    path('engagements/', views.engagements_liste, name='engagement_liste'),
    path('engagements/ajouter/', views.engagement_editer, name='engagement_ajouter'),
    path('engagements/<int:pk>/modifier/', views.engagement_editer, name='engagement_modifier'),
    path('engagements/<int:pk>/supprimer/', views.engagement_supprimer, name='engagement_supprimer'),
    path('sections/', views.sections_liste, name='section_liste'),
    path('sections/ajouter/', views.section_editer, name='section_ajouter'),
    path('sections/<int:pk>/modifier/', views.section_editer, name='section_modifier'),
    path('sections/<int:pk>/supprimer/', views.section_supprimer, name='section_supprimer'),
    path('codes-promo/', views.codes_promo_liste, name='code_promo_liste'),
    path('codes-promo/ajouter/', views.code_promo_editer, name='code_promo_ajouter'),
    path('codes-promo/<int:pk>/modifier/', views.code_promo_editer, name='code_promo_modifier'),
    path('codes-promo/<int:pk>/supprimer/', views.code_promo_supprimer, name='code_promo_supprimer'),

    # Parametres
    path('parametres/', views.parametres, name='parametres'),

    # Images
    path('images/<int:image_id>/supprimer/', views.supprimer_image_produit, name='supprimer_image_produit'),
]
