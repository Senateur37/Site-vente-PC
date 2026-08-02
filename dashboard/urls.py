from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.connexion, name='login'),
    path('logout/', views.deconnexion, name='logout'),
    path('', views.index, name='index'),

    # Inscription
    path('inscription/', views.inscription, name='inscription'),

    # Password reset
    path('mot-de-passe-oublie/', auth_views.PasswordResetView.as_view(
        template_name='dashboard/mot_de_passe_oublie.html',
        email_template_name='dashboard/email_reinitialisation.html',
        subject_template_name='dashboard/email_reinitialisation_sujet.html',
        success_url='/dashboard/mot-de-passe-oublie/envoye/'
    ), name='mot_de_passe_oublie'),
    path('mot-de-passe-oublie/envoye/', auth_views.PasswordResetDoneView.as_view(
        template_name='dashboard/mot_de_passe_envoye.html'
    ), name='mot_de_passe_envoye'),
    path('reinitialiser/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='dashboard/reinitialiser_mot_de_passe.html',
        success_url='/dashboard/reinitialiser/termine/'
    ), name='reinitialiser_mot_de_passe'),
    path('reinitialiser/termine/', auth_views.PasswordResetCompleteView.as_view(
        template_name='dashboard/reinitialiser_termine.html'
    ), name='reinitialiser_termine'),

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

    # Clients
    path('clients/', views.liste_clients, name='clients_liste'),

    # Parametres
    path('parametres/', views.parametres, name='parametres'),

    # Images
    path('images/<int:image_id>/supprimer/', views.supprimer_image_produit, name='supprimer_image_produit'),
]
