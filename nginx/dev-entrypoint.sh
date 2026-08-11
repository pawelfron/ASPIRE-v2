#!/bin/sh
set -eu

USER="${NGINX_ADMIN_USER:-admin}"
PASS="${NGINX_ADMIN_PASS:-admin}"
HASH="$(openssl passwd -apr1 "$PASS")"
echo "${USER}:${HASH}" > /etc/nginx/htpasswd

exec nginx -g "daemon off;"
