# TechShop — Application de e-commerce

Application de vente en ligne pour matériel informatique (ordinateurs, accessoires, composants).

## Fonctionnalités

- **Boutique publique** : catalogue de produits avec catégories, marques, filtres et recherche
- **Panier** : ajout/suppression de produits, validation de commande
- **Dashboard admin** : gestion des produits, catégories, marques, commandes et paramètres du site
- **Mode sombre** : support du thème clair/sombre

## Installation

### Prérequis

- Python 3.10 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes

1. **Extraire le dossier** `techshop.zip`

2. **Ouvrir un terminal** dans le dossier `techshop`

3. **Créer un environnement virtuel** (recommandé) :
   ```bash
   python -m venv venv
   ```

4. **Activer l'environnement virtuel** :
   - Windows : `venv\Scripts\activate`
   - Mac/Linux : `source venv/bin/activate`

5. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

6. **Appliquer les migrations** (créer la base de données) :
   ```bash
   python manage.py migrate
   ```

7. **Créer un super-utilisateur** (compte admin) :
   ```bash
   python manage.py createsuperuser
   ```
   Suivez les instructions pour créer un nom d'utilisateur, email et mot de passe.

8. **Lancer le serveur** :
   ```bash
   python manage.py runserver
   ```

9. **Ouvrir le navigateur** à l'adresse : `http://127.0.0.1:8000`

## Accès

| Page | URL |
|------|-----|
| Boutique (client) | `/` |
| Dashboard (admin) | `/dashboard/` |
| Espace admin Django | `/admin/` |

## Comptes

- **Super-utilisateur** : créé via `createsuperuser` (étapes ci-dessus)
- Connectez-vous au dashboard via `/dashboard/login/`

## Structure du projet

```
techshop/
├── commandes/          # Gestion des commandes et panier
├── dashboard/          # Dashboard admin (produits, commandes, paramètres)
├── produits/           # Catalogue produits, catégories, marques
├── techshop/           # Configuration Django (settings, urls)
├── templates/          # Templates HTML
├── static/             # Fichiers statiques (CSS, JS)
├── media/              # Uploads (images produits, logos)
├── manage.py           # Commande principale Django
├── requirements.txt    # Dépendances Python
└── db.sqlite3          # Base de données (fichier)
```

## Personnalisation

Les paramètres du site (nom, description, logo, contact) se modifient depuis le dashboard :
**Dashboard → Paramètres**


## Front-end (Tailwind CSS)

Le CSS est compilé (plus de CDN) dans `static/css/tailwind.css`, fichier versionné : le serveur de production n'a pas besoin de Node.
Après avoir ajouté ou changé des classes Tailwind dans les templates :

```bash
npm install        # une seule fois
npm run build:css  # ou : npm run watch:css pendant le développement
```
