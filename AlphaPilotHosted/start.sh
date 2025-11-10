#!/usr/bin/env sh
set -e
: "${PORT:=8080}"
envsubst < /etc/nginx/nginx.tmpl.conf > /etc/nginx/nginx.conf
exec /usr/bin/supervisord -n

