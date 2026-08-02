"""
Panier géré via la session Django - aucun compte utilisateur requis.
"""
from produits.models import Produit

SESSION_KEY = 'panier'


class Panier:
    def __init__(self, request):
        self.session = request.session
        panier = self.session.get(SESSION_KEY)
        if panier is None:
            panier = self.session[SESSION_KEY] = {}
        self.panier = panier

    def ajouter(self, produit, quantite=1):
        produit_id = str(produit.id)
        if produit_id in self.panier:
            self.panier[produit_id]['quantite'] += quantite
        else:
            self.panier[produit_id] = {'quantite': quantite}
        self.enregistrer()

    def modifier_quantite(self, produit_id, quantite):
        produit_id = str(produit_id)
        if produit_id in self.panier:
            if quantite <= 0:
                self.supprimer(produit_id)
            else:
                self.panier[produit_id]['quantite'] = quantite
                self.enregistrer()

    def supprimer(self, produit_id):
        produit_id = str(produit_id)
        if produit_id in self.panier:
            del self.panier[produit_id]
            self.enregistrer()

    def vider(self):
        self.session[SESSION_KEY] = {}
        self.enregistrer()

    def enregistrer(self):
        self.session.modified = True

    def __iter__(self):
        produit_ids = self.panier.keys()
        produits = Produit.objects.filter(id__in=produit_ids)
        produits_dict = {str(p.id): p for p in produits}

        for produit_id, item in self.panier.items():
            produit = produits_dict.get(produit_id)
            if produit is None:
                continue
            yield {
                'produit': produit,
                'quantite': item['quantite'],
                'sous_total': produit.prix * item['quantite'],
            }

    def __len__(self):
        return sum(item['quantite'] for item in self.panier.values())

    def total(self):
        return sum(item['sous_total'] for item in self)