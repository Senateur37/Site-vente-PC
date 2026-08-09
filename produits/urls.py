from django.urls import path
from . import views

app_name = 'produits'

urlpatterns = [
    path('', views.liste_produits, name='liste'),
    path('section/<int:section_id>/', views.section_detail, name='section_detail'),
    path('produit/<slug:slug>/', views.detail_produit, name='detail'),
    path('recherche/', views.recherche_ajax, name='recherche_ajax'),
    path('contact/', views.contact, name='contact'),
    path('apropos/', views.apropos, name='apropos'),
]