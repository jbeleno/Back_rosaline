#!/usr/bin/env bash
#
# Script de despliegue para FastAPI en AWS EC2 (Ubuntu 22.04)
# Ejecutar con: bash deploy.sh
#
# Requisitos:
#  - Usuario con permisos sudo (ej. ubuntu)
#  - Repositorio ya clonado en /var/www/fastapi-ecommerce (o la ruta elegida)
#  - Archivo .env configurado con las credenciales de producción

set -euo pipefail

APP_USER="ubuntu"
APP_GROUP="www-data"
APP_ROOT="/var/www/fastapi-ecommerce"
APP_DIR="$APP_ROOT/backend_tienda"
VENV_PATH="$APP_DIR/.venv"
PYTHON_BIN="/usr/bin/python3.11"
SERVICE_NAME="fastapi-ecommerce"
SYSTEMD_UNIT="/etc/systemd/system/${SERVICE_NAME}.service"
NGINX_SITE="/etc/nginx/sites-available/${SERVICE_NAME}.conf"
NGINX_SITE_LINK="/etc/nginx/sites-enabled/${SERVICE_NAME}.conf"
SOCKET_PATH="/run/${SERVICE_NAME}.sock"
LOG_DIR="/var/log/${SERVICE_NAME}"

echo "[1/7] Actualizando paquetes del sistema..."
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

echo "[2/7] Instalando dependencias del sistema..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip build-essential \
    libpq-dev nginx git

echo "[3/7] Preparando estructura de directorios..."
sudo mkdir -p "$APP_ROOT" "$LOG_DIR" /run
sudo chown -R "$APP_USER":"$APP_GROUP" "$APP_ROOT" "$LOG_DIR"

echo "[4/7] Configurando entorno virtual..."
if [ ! -d "$VENV_PATH" ]; then
  sudo -u "$APP_USER" "$PYTHON_BIN" -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
pip install --upgrade pip wheel setuptools
pip install -r "$APP_DIR/requirements.txt"
pip install gunicorn "uvicorn[standard]"
deactivate

echo "[5/7] Copiando archivos de configuración..."
sudo install -o root -g root -m 640 "$APP_DIR/fastapi-ecommerce.service" "$SYSTEMD_UNIT"
sudo install -o root -g root -m 640 "$APP_DIR/nginx.conf" "$NGINX_SITE"

if [ ! -f "$APP_DIR/.env" ]; then
  echo "⚠️  No se encontró $APP_DIR/.env. Copiando env.production como base..."
  cp "$APP_DIR/env.production" "$APP_DIR/.env"
fi

echo "[6/7] Habilitando servicio systemd..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "[7/7] Configurando Nginx..."
sudo ln -sf "$NGINX_SITE" "$NGINX_SITE_LINK"
sudo nginx -t
sudo systemctl reload nginx

echo "✅ Despliegue completado. Revisa los logs en $LOG_DIR o con 'journalctl -u ${SERVICE_NAME} -f'"

