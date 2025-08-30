server {
    listen 80;
    server_name etl-tst.chococraft.ru;

    # ACME challenge для Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        default_type text/plain;
    }

    # Перенаправление на HTTPS для всех остальных запросов
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name etl-tst.chococraft.ru;

    # SSL конфигурация (пути будут обновлены после получения сертификата)
    ssl_certificate /etc/letsencrypt/live/etl-tst.chococraft.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/etl-tst.chococraft.ru/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Добавляем HSTS
    add_header Strict-Transport-Security "max-age=86400; includeSubDomains" always;
    
    # Минимальные безопасные заголовки для TEST
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer" always;

    # Assets первыми (высокий приоритет)
    location /assets/ {
        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        root /var/www/etl-tst.chococraft.ru;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA под /admin: все пути отдаем index.html (React Router)
    location = /admin { return 301 /admin/; }

    location /admin/ {
        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        alias /var/www/etl-tst.chococraft.ru/;
        index index.html;
        # Для SPA на подпрефиксе важно указывать полный путь /admin/index.html,
        # иначе internal redirect уйдет в location / и утащит в backend
        try_files $uri $uri/ /admin/index.html;
    }

    # API эндпоинты
    location /api/ {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Request-ID $http_x_request_id;
    }

    # Админские эндпоинты (без Basic Auth, так как уже под /admin/)
    location /api/v1/admin/ {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Request-ID $http_x_request_id;
    }

    # Health эндпоинты
    location /health/ {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Request-ID $http_x_request_id;
    }

    # Статические файлы в корне
    location = /favicon.ico {
        alias /var/www/etl-tst.chococraft.ru/favicon.ico;
        log_not_found off;
        access_log off;
    }

    location = /robots.txt {
        alias /var/www/etl-tst.chococraft.ru/robots.txt;
        log_not_found off;
        access_log off;
    }

    # Основное приложение (без Basic Auth для общедоступных эндпоинтов)
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Request-ID $http_x_request_id;
    }

    # Логи с X-Request-ID
    access_log /var/log/nginx/etl-tst.chococraft.ru.access.log combined;
    error_log /var/log/nginx/etl-tst.chococraft.ru.error.log;
}
