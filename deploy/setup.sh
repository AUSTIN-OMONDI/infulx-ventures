#!/usr/bin/env bash
# Influx Ventures - one-time server setup for Ubuntu (Oracle Cloud, or any VPS).
# Run as the default user (ubuntu), NOT as root:
#   bash setup.sh yourdomain.co.ke you@email.com
set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-}"
REPO="https://github.com/AUSTIN-OMONDI/infulx-ventures.git"
APP_DIR="$HOME/influx"

if [ -z "$DOMAIN" ]; then
  echo "Usage: bash setup.sh yourdomain.co.ke you@email.com"
  exit 1
fi

echo "==> Installing packages"
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip git nginx ufw

echo "==> Getting the code"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO" "$APP_DIR"
fi

echo "==> Python environment"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/infulx/requirements.txt" gunicorn

echo "==> First-time data load (skipped if products already exist)"
cd "$APP_DIR/infulx" && "$APP_DIR/venv/bin/python" seed.py || true

echo "==> Service"
sudo cp "$APP_DIR/deploy/influx.service" /etc/systemd/system/influx.service
sudo sed -i "s|__USER__|$USER|g; s|__APPDIR__|$APP_DIR|g" /etc/systemd/system/influx.service
sudo systemctl daemon-reload
sudo systemctl enable --now influx
sudo systemctl restart influx

echo "==> Web server"
sudo cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/influx
sudo sed -i "s|__DOMAIN__|$DOMAIN|g; s|__APPDIR__|$APP_DIR|g" /etc/nginx/sites-available/influx
sudo ln -sf /etc/nginx/sites-available/influx /etc/nginx/sites-enabled/influx
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

echo "==> Firewall (Ubuntu side; also open 80/443 in the Oracle console)"
sudo ufw allow OpenSSH || true
sudo ufw allow 'Nginx Full' || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT || true
sudo netfilter-persistent save 2>/dev/null || true

if [ -n "$EMAIL" ]; then
  echo "==> Free HTTPS certificate"
  sudo apt-get install -y certbot python3-certbot-nginx
  sudo certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect || \
    echo "Certificate step failed - check the domain points here, then run: sudo certbot --nginx"
fi

echo
echo "Done. Site: http://$DOMAIN  (https after the certificate step)"
echo "Admin password: set it once with"
echo "  sudo systemctl edit influx     # add:  [Service]"
echo "                                 #       Environment=ADMIN_PASSWORD=yourpassword"
echo "  sudo systemctl restart influx"
