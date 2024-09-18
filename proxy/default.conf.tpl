server {
    listen 8080;

    location /static {
        alias /vol/static;
    }

    location / {
        uwsgi_pass              app:8000;
        include                 /etc/nginx/uwsgi_params;
        client_max_body_size    10M;
    }
}
