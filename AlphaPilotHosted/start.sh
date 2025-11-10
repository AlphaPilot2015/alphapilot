#!/usr/bin/env sh
set -e
: "${PORT:=8080}"

# Rellena la plantilla de Nginx con $PORT
envsubst < /etc/nginx/nginx.tmpl.conf > /etc/nginx/nginx.conf

# Arranca supervisor (api + nginx)
exec /usr/bin/supervisord -n
