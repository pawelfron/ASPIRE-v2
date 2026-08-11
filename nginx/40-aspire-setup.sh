#!/bin/sh
set -eu

USER="${NGINX_ADMIN_USER:-admin}"
PASS="${NGINX_ADMIN_PASS:-admin}"
HASH="$(openssl passwd -apr1 "$PASS")"
echo "${USER}:${HASH}" > /etc/nginx/htpasswd

DOMAIN_NAME="${DOMAIN:-localhost}"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN_NAME}"
if [ ! -f "${CERT_DIR}/fullchain.pem" ] || [ ! -f "${CERT_DIR}/privkey.pem" ]; then
  echo "Bootstrapping self-signed certificate for ${DOMAIN_NAME}"
  mkdir -p "${CERT_DIR}"
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "${CERT_DIR}/privkey.pem" \
    -out "${CERT_DIR}/fullchain.pem" \
    -subj "/CN=${DOMAIN_NAME}"
fi
