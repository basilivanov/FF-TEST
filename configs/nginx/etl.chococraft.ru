server {
    listen 80;
    server_name etl.chococraft.ru;

    # Перенаправление на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name etl.chococraft.ru;

    # SSL конфигурация (замените пути к сертификатам на реальные)
    ssl_certificate /etc/ssl/certs/etl.chococraft.ru.crt;
    ssl_certificate_key /etc/ssl/private/etl.chococraft.ru.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Проксируем запросы к продакшн-приложению
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $http_x_request_id;
    }

    # Логи
    access_log /var/log/nginx/etl.chococraft.ru.access.log;
    error_log /var/log/nginx/etl.chococraft.ru.error.log;
}