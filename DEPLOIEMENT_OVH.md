# Déploiement TechShop sur VPS OVH

Guide complet pour mettre le site en ligne sur un **VPS OVH (Ubuntu 22.04/24.04)**
avec Nginx + Gunicorn + PostgreSQL + SSL gratuit (Let's Encrypt).

---

## 1. Commandes du VPS

Après création du VPS sur le manager OVH, connectez-vous :

```bash
ssh root@IP_DU_VPS
```

(ou avec l'utilisateur `ubuntu` sur Ubuntu 22.04)

## 2. Points DNS (si vous avez un nom de domaine)

Dans le **manager OVH > Domaines > votre domaine > Zone DNS**, créez :

| Type | Hôte   | Cible              |
|------|--------|--------------------|
| A    | @      | IP_DU_VPS          |
| A    | www    | IP_DU_VPS          |

## 3. Transfert du projet

Depuis votre PC, dans le dossier `C:\techshop` :

```bash
# Option A - avec Git
git remote add origin https://github.com/votre-compte/techshop.git
git push -u origin main
```

```bash
# Option B - avec scp (sous PowerShell/WSL)
scp -r C:\techshop root@IP_DU_VPS:/tmp/techshop
```

## 4. Lancer l'installation automatique

Sur le serveur :

```bash
sudo bash /tmp/techshop/deploy_ovh.sh
```

Le script fait tout automatiquement :
- installation de Python, Nginx, PostgreSQL, Certbot
- environnement virtuel + dépendances
- création de la base PostgreSQL + fichier `.env` (clé secrète générée)
- migrations + collectstatic
- service Gunicorn (systemd) + configuration Nginx
- pare-feu (UFW) + certificat SSL
- sauvegarde automatique quotidienne de la base

## 5. Réglages après le script

**A)** Les variables à modifier dans `/home/techshop/techshop/.env` **avant** de lancer :

- `DOMAIN` en début de `deploy_ovh.sh` (ligne ~10)
- `DB_PASS` (ligne ~13)
- `EMAIL_HOST_PASSWORD` (votre mot de passe d'application Gmail)
- `DEFAULT_FROM_EMAIL` si besoin

Si vous avez déjà lancé le script, modifiez `/home/techshop/techshop/.env` puis :

```bash
sudo systemctl restart techshop
```

**B)** Charger les données existantes (produits, commandes, etc.) si vous venez de SQLite :

```bash
cd /home/techshop/techshop
sudo -u techshop ./venv/bin/python manage.py loaddata backup_<date>.json
```

(sinon : créer les produits et catégories via l'admin)

**C)** Vérifier le fonctionnement :

```bash
systemctl status techshop        # Gunicorn doit être "active (running)"
nginx -t                        # config Nginx valide
```

## 6. Commandes utiles au quotidien

```bash
# Redémarrer après une mise à jour du code
cd /home/techshop/techshop
git pull
sudo -u techshop ./venv/bin/pip install -r requirements.txt
sudo -u techshop ./venv/bin/python manage.py migrate --noinput
sudo -u techshop ./venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart techshop

# Consulter les logs
journalctl -u techshop -n 50 -f

# Sauvegarde manuelle de la base
sudo -u techshop ./venv/bin/python manage.py backup_db
# (une sauvegarde est déjà faite chaque nuit à 2h30 via cron)
```

## 7. Rappel sécurité (déjà appliquée)

- `DEBUG=False` dans `.env`
- `ALLOWED_HOSTS` = votre domaine
- HTTPS forcé + HSTS (car `USE_HTTPS=True`)
- Cookies session/CSRF en mode secure
- Uploads validés (type + 5 Mo max)
- `.env` et `backups/` exclus du dépôt Git

---

**Fichiers fournis dans le projet :**

| Fichier                    | Rôle                              |
|----------------------------|-----------------------------------|
| `deploy_ovh.sh`            | Script d'installation automatique |
| `deploy/techshop.service`  | Service Gunicorn (systemd)        |
| `deploy/techshop.nginx`    | Configuration Nginx               |

En cas de souci pendant l'installation, copiez l'erreur affichée : je pourrai vous aider.


## Variables d'environnement importantes

Voir `.env.example`. Points clés :

- `SECRET_KEY` est **obligatoire** quand `DEBUG=False` (le site refuse de démarrer sinon).
- Derrière Nginx, activer `USE_PROXY_HEADERS=True` avec `USE_HTTPS=True`, sinon la redirection HTTPS boucle et la limitation de tentatives voit l'IP de Nginx.
- `REDIS_URL` (paquet `redis` à installer) rend la limitation de tentatives fiable avec plusieurs workers Gunicorn.
- Paiement en ligne : renseigner `CINETPAY_API_KEY` et `CINETPAY_SITE_ID`, puis déclarer dans CinetPay l'URL de notification `https://votre-domaine/paiement/notification/`. Sans ces clés, seul le paiement à la livraison est proposé.

## Tests

```bash
python manage.py test
```
