#!/bin/bash
if [ ! -f "/etc/nginx/.htpasswd" ]
then
  echo "Creating basic auth credentials..."
  echo "$NGINX_PASSWORD" | htpasswd -c -i /etc/nginx/.htpasswd "$NGINX_USER"
else
  echo "Auth file already exists."
fi
