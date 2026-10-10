#!/bin/bash
# ============================================================
#  Script de déploiement TechShop sur VPS OVH (Ubuntu 22.04/24.04)
#  Usage : copier le projet sur le serveur puis :
#          sudo bash deploy_ovh.sh
# ============================================================
set -e

# ---------- 1. Variables ----------
APP_DIR="/home/techshop/techshop"
DOMAIN="sacko-tech.com"
DB_NAME="socktech"
DB_USER="techshop"
DB_PASS="Ha12,75@rouna"

echo "==> Mise à jour du système"
apt-get update -y && apt-get upgrade -y

echo "==> Installation des paquets"
apt-get install -y python3 python3-venv python3-pip nginx postgresql postgresql-contrib certbot python3-certbot-nginx curl git

echo "==> Création de l'utilisateur applicatif"
if ! id -u techshop > /dev/null 2>&1; then
    useradd -m -s /bin/bash techshop
fi
usermod -a -G www-data techshop

echo "==> Préparation du dossier applicatif"
mkdir -p "$APP_DIR"
cp -r ./* "$APP_DIR/" 2>/dev/null || true
cd "$APP_DIR"
chown -R techshop:www-data "$APP_DIR"

echo "==> Environnement virtuel + dépendances"
if [ ! -d venv ]; then
    sudo -u techshop python3 -m venv venv
fi
sudo -u techshop ./venv/bin/pip install --upgrade pip
sudo -u techshop ./venv/bin/pip install -r requirements.txt

echo "==> Configuration PostgreSQL"
sudo -u postgres psql <<SQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASS';
    ELSE
        ALTER ROLE $DB_USER WITH PASSWORD '$DB_PASS';
    END IF;
END
\$\$;
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
SQL

echo "==> Fichier .env"
cat > "$APP_DIR/.env" <<ENV
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,127.0.0.1,localhost
USE_HTTPS=True
USE_PROXY_HEADERS=True
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
DATABASE_URL=postgres://$DB_USER:$DB_PASS@127.0.0.1:5432/$DB_NAME
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=diassanaissiaka68@gmail.com
EMAIL_HOST_PASSWORD=tozo tkwi yqux xjun
ENV
chown techshop:techshop "$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"

echo "==> Build du frontend React"
if ! command -v node > /dev/null 2>&1; then
    echo "==> Installation de Node.js 20 LTS"
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
if [ -d "$APP_DIR/frontend" ]; then
    echo "==> Compilation du frontend"
    cd "$APP_DIR/frontend"
    npm install
    npm run build
    chown -R techshop:www-data "$APP_DIR/frontend/dist"
    cd "$APP_DIR"
fi

echo "==> Migrations + statiques"
sudo -u techshop ./venv/bin/python manage.py migrate --noinput
sudo -u techshop ./venv/bin/python manage.py collectstatic --noinput

echo "==> Création du super-utilisateur (si interactif)"
sudo -u techshop ./venv/bin/python manage.py createsuperuser || true

echo "==> Service Gunicorn (systemd)"
cp "$APP_DIR/deploy/techshop.service" /etc/systemd/system/techshop.service
systemctl daemon-reload
systemctl enable techshop
systemctl restart techshop

echo "==> Configuration Nginx"
sed -i "s/example.com/$DOMAIN/g" "$APP_DIR/deploy/techshop.nginx"
cp "$APP_DIR/deploy/techshop.nginx" /etc/nginx/sites-available/techshop
ln -sf /etc/nginx/sites-available/techshop /etc/nginx/sites-enabled/techshop
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "==> Pare-feu (UFW)"
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

echo "==> SSL (Let's Encrypt)"
certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --redirect --agree-tos --register-unsafely-without-email || echo "Attention: Certbot a échoué (veuillez vérifier la propagation DNS de $DOMAIN puis relancer: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN)"

echo "==> Sauvegarde automatique quotidienne (cron)"
(crontab -u techshop -l 2>/dev/null | grep -v backup_db; echo "30 2 * * * /home/techshop/techshop/venv/bin/python /home/techshop/techshop/manage.py backup_db") | crontab -u techshop -

echo ""
echo "==========================================="
echo "  Déploiement terminé !"
echo "  Site : https://$DOMAIN"
echo "  Vérifier : systemctl status techshop"
echo "==========================================="
