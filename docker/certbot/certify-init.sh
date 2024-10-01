#!/bin/sh

set -e

until nc -z -w 5 proxy 80; do
    echo "Waiting for proxy to be available at port 80!..."
    sleep 5s
done

echo "Getting certificate..."

certbot certonly \
    --webroot \
    --webroot-path "/vol/www/" \
    -d "$DOMAIN" \
    --email $EMAIL \
    --rsa-key-size 4096 \
    --agree-tos \
    --noninteractive