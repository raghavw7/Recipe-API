server {
    listen ${LISTEN_PORT};
    server_name ${SERVER_NAME};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }


}

server {
    listen 443 ssl;
    server_name ${SERVER_NAME};

    ssl_certificate /etc/nginx/ssl/live/${SERVER_NAME}/fullchain.pem;
    ssl_certificate_key /etc/nginx/ss/live/${SERVER_NAME}/privkey.pem;

        location /static {
        alias /vol/static;
    }

    location / {
        uwsgi_pass              ${APP_HOST}:${APP_PORT};
        include                 /etc/nginx/uwsgi_params;
        client_max_body_size    10M;
    }
}