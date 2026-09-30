from rest_framework import serializers

from commandes.models import Commande
from produits.models import Avis, Categorie, ImageProduit, Produit


def _media(champ):
    return champ.url if champ else None


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['nom', 'slug']


class ProduitCarteSerializer(serializers.ModelSerializer):
    """Représentation légère d'un produit (listes, cartes, panier)."""
    image = serializers.SerializerMethodField()
    categorie = CategorieSerializer(read_only=True)
    marque_label = serializers.CharField(source='get_marque_display', read_only=True)
    note_moyenne = serializers.FloatField(read_only=True)
    nb_avis = serializers.IntegerField(read_only=True)

    class Meta:
        model = Produit
        fields = [
            'id', 'nom', 'slug', 'prix', 'prix_barre', 'image', 'marque', 'marque_label',
            'categorie', 'stock', 'en_stock', 'en_promo', 'pourcentage_reduction',
            'est_nouveau', 'note_moyenne', 'nb_avis', 'a_la_une',
        ]

    def get_image(self, obj):
        return _media(obj.image)


class ImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ImageProduit
        fields = ['image', 'legende']

    def get_image(self, obj):
        return _media(obj.image)


class AvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avis
        fields = ['id', 'auteur', 'note', 'commentaire', 'date_creation']


class ProduitDetailSerializer(ProduitCarteSerializer):
    description = serializers.CharField(read_only=True)
    galerie = serializers.SerializerMethodField()

    class Meta(ProduitCarteSerializer.Meta):
        fields = ProduitCarteSerializer.Meta.fields + ['description', 'galerie']

    def get_galerie(self, obj):
        return obj.images_galerie


class CommandeSerializer(serializers.ModelSerializer):
    lignes = serializers.SerializerMethodField()
    sous_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    methode_paiement_label = serializers.CharField(source='get_methode_paiement_display', read_only=True)
    statut_label = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Commande
        fields = [
            'id', 'nom_client', 'telephone', 'email', 'adresse', 'note',
            'methode_paiement', 'methode_paiement_label', 'paiement_statut',
            'statut', 'statut_label', 'reduction', 'frais_livraison',
            'sous_total', 'total', 'date_creation', 'lignes',
        ]

    def get_lignes(self, obj):
        return [
            {
                'nom_produit': l.nom_produit,
                'quantite': l.quantite,
                'prix_unitaire': l.prix_unitaire,
                'sous_total': l.sous_total,
            }
            for l in obj.lignes.all()
        ]
