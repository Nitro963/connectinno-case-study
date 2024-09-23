#!/bin/bash
if [ ! -f "/etc/nginx/sites-enabled/site" ]
then
  echo "Evaluating site template..."
  export DOLLAR="$"
  envsubst < /etc/nginx/conf.d/site.conf.template > /etc/nginx/sites-enabled/site
else
  echo "Site configs already exists."
fi
