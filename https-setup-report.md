# Отчет о текущем состоянии настройки HTTPS для etl-tst.chococraft.ru

## Текущее состояние

1. Домен etl-tst.chococraft.ru доступен по HTTP (порт 80)
2. Редирект с HTTP на HTTPS настроен, но не работает корректно
3. HTTPS (порт 443) недоступен из-за отсутствия SSL-сертификатов
4. Конфигурация Nginx требует обновления

## Необходимые действия для завершения настройки

### 1. Установка Certbot
```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Обновление конфигурации Nginx
Заменить содержимое `/etc/nginx/sites-enabled/etl-tst.chococraft.ru` на:
```
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

    # Обслуживание статических файлов UI
    location /admin/ {
        # Basic Authentication для админки
        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        alias /opt/feature-factory/app/ui/dist/;
        try_files $uri $uri/ /admin/index.html;
        
        # Кэширование статических файлов
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
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

    # Админские эндпоинты (с Basic Authentication)
    location /admin/api/ {
        auth_basic "Admin API";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Request-ID $http_x_request_id;
        proxy_set_header Authorization $http_authorization;
    }

    # Админский эндпоинт /admin (с Basic Authentication)
    location /admin {
        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        proxy_pass http://127.0.0.1:8081/admin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Request-ID $http_x_request_id;
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
```

### 3. Получение SSL-сертификата
```bash
sudo certbot --nginx -d etl-tst.chococraft.ru
```

### 4. Перезагрузка Nginx
```bash
sudo systemctl reload nginx
```

## Проверка результата

После выполнения всех шагов необходимо проверить:

1. Доступность домена по HTTPS:
   ```bash
   curl -I https://etl-tst.chococraft.ru
   ```

2. Работу BasicAuth для /admin:
   ```bash
   curl -I https://etl-tst.chococraft.ru/admin
   ```

3. Проксирование заголовков X-Request-ID и X-Forwarded-Proto=https

4. Наличие заголовков безопасности (HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)

5. Работу отдельных access/error логов домена