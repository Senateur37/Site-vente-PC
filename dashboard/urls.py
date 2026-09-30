from django.urls import path
from . import stats, views, vues_catalogue, vues_commandes, vues_contenu, vues_equipe

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.connexion, name='login'),
    path('logout/', views.deconnexion, name='logout'),
    path('', stats.index, name='index'),

    # Inscription (désactivée en production — seul l'admin crée les comptes)
    # path('inscription/', views.inscription, name='inscription'),

    # Password reset (code de vérification)
    path('mot-de-passe-oublie/', views.mot_de_passe_oublie, name='mot_de_passe_oublie'),
    path('mot-de-passe-oublie/code/', views.verifier_code, name='verifier_code'),
    path('mot-de-passe-oublie/nouveau/', views.nouveau_mot_de_passe, name='nouveau_mot_de_passe'),

    # Produits
    path('produits/', vues_catalogue.liste_produits, name='produits_liste'),
    path('produits/ajouter/', vues_catalogue.ajouter_produit, name='produit_ajouter'),
    path('produits/<int:produit_id>/modifier/', vues_catalogue.modifier_produit, name='produit_modifier'),
    path('produits/<int:produit_id>/supprimer/', vues_catalogue.supprimer_produit, name='produit_supprimer'),

    # Categories
    path('categories/', vues_catalogue.liste_categories, name='categories_liste'),
    path('categories/<int:categorie_id>/supprimer/', vues_catalogue.supprimer_categorie, name='categorie_supprimer'),

    # Marques
    path('marques/', vues_catalogue.liste_marques, name='marques_liste'),
    path('marques/<int:marque_id>/supprimer/', vues_catalogue.supprimer_marque, name='marque_supprimer'),

    # Commandes
    path('commandes/', vues_commandes.liste_commandes, name='commandes_liste'),
    path('commandes/<int:commande_id>/', vues_commandes.detail_commande, name='commande_detail'),
    path('commandes/export/', vues_commandes.export_commandes, name='commandes_export'),
    path('commandes/<int:commande_id>/facture/', vues_commandes.facture, name='commande_facture'),
    path('commandes/<int:commande_id>/bon-livraison/', vues_commandes.bon_livraison, name='commande_bon_livraison'),

    # Avis
    path('avis/', vues_catalogue.liste_avis, name='avis_liste'),
    path('avis/<int:avis_id>/approuver/', vues_catalogue.approuver_avis, name='avis_approuver'),
    path('avis/<int:avis_id>/supprimer/', vues_catalogue.supprimer_avis, name='avis_supprimer'),

    # Clients
    path('clients/', vues_commandes.liste_clients, name='clients_liste'),

    # Contenu du site affiché sur la vitrine
    path('engagements/', vues_contenu.engagements_liste, name='engagement_liste'),
    path('engagements/ajouter/', vues_contenu.engagement_editer, name='engagement_ajouter'),
    path('engagements/<int:pk>/modifier/', vues_contenu.engagement_editer, name='engagement_modifier'),
    path('engagements/<int:pk>/supprimer/', vues_contenu.engagement_supprimer, name='engagement_supprimer'),
    path('sections/', vues_contenu.sections_liste, name='section_liste'),
    path('sections/ajouter/', vues_contenu.section_editer, name='section_ajouter'),
    path('sections/<int:pk>/modifier/', vues_contenu.section_editer, name='section_modifier'),
    path('sections/<int:pk>/supprimer/', vues_contenu.section_supprimer, name='section_supprimer'),
    path('codes-promo/', vues_contenu.codes_promo_liste, name='code_promo_liste'),
    path('codes-promo/ajouter/', vues_contenu.code_promo_editer, name='code_promo_ajouter'),
    path('codes-promo/<int:pk>/modifier/', vues_contenu.code_promo_editer, name='code_promo_modifier'),
    path('codes-promo/<int:pk>/supprimer/', vues_contenu.code_promo_supprimer, name='code_promo_supprimer'),

    # Équipe, rôles et journal d'activité
    path('equipe/', vues_equipe.equipe_liste, name='equipe_liste'),
    path('equipe/ajouter/', vues_equipe.equipe_ajouter, name='equipe_ajouter'),
    path('equipe/<int:user_id>/', vues_equipe.equipe_modifier, name='equipe_modifier'),
    path('journal/', vues_equipe.journal, name='journal'),

    # Parametres
    path('parametres/', vues_contenu.parametres, name='parametres'),

    # Images
    path('images/<int:image_id>/supprimer/', vues_catalogue.supprimer_image_produit, name='supprimer_image_produit'),
]
