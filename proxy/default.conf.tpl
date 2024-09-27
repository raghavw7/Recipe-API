server {
    listen 80;
    server_name ${SERVER_NAME};

    location / {
        return 200 'Proxy is running!';
        add_header Content-Type text/plain;
    }
}
