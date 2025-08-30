# Nginx Configuration Guide for Feature Factory Admin UI

## Обзор

Этот документ описывает, как настроить Nginx для обслуживания Feature Factory Admin UI с Basic Authentication.

## Требования

- Nginx установлен и запущен
- Feature Factory приложение запущено на порту 8081
- SSL сертификаты (для HTTPS)

## Конфигурация Nginx

### 1. Создание конфигурационного файла

Создайте файл конфигурации в `/etc/nginx/sites-available/etl-tst.chococraft.ru`:

```nginx
server {
    listen 80;
    server_name etl-tst.chococraft.ru;

    # Перенаправление на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name etl-tst.chococraft.ru;

    # SSL конфигурация (замените пути к сертификатам на реальные)
    ssl_certificate /etc/ssl/certs/etl-tst.chococraft.ru.crt;
    ssl_certificate_key /etc/ssl/private/etl-tst.chococraft.ru.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Обслуживание статических файлов UI
    location /admin/ {
        # Basic Authentication для админки
        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        alias /var/www/etl-tst.chococraft.ru/;
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
        proxy_set_header X-Forwarded-Proto $scheme;
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
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $http_x_request_id;
        proxy_set_header Authorization $http_authorization;
    }

    # Основное приложение (без Basic Auth для общедоступных эндпоинтов)
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $http_x_request_id;
    }

    # Логи
    access_log /var/log/nginx/etl-tst.chococraft.ru.access.log;
    error_log /var/log/nginx/etl-tst.chococraft.ru.error.log;
}
```

### 2. Создание символической ссылки

Создайте символическую ссылку в `/etc/nginx/sites-enabled/`:

```bash
sudo ln -s /etc/nginx/sites-available/etl-tst.chococraft.ru /etc/nginx/sites-enabled/
```

### 3. Создание файла с учетными данными

Создайте файл `/etc/nginx/.htpasswd` с учетными данными для Basic Authentication:

```bash
# Создание файла с пользователем ops и паролем ops123
echo "ops:$apr1$OaFo6Diy$r1JZ07DfD4ni8rMr6t.UF0" > /etc/nginx/.htpasswd

# Установка прав доступа
sudo chmod 644 /etc/nginx/.htpasswd
sudo chown www-data:www-data /etc/nginx/.htpasswd
```

### 4. Проверка конфигурации

Проверьте конфигурацию Nginx:

```bash
sudo nginx -t
```

### 5. Перезапуск Nginx

Перезапустите Nginx для применения изменений:

```bash
sudo systemctl reload nginx
```

## Доступ к админке

После настройки админка будет доступна по адресу:

```
https://etl-tst.chococraft.ru/admin
```

Учетные данные для входа:
- Логин: `ops`
- Пароль: `ops123`

## Безопасность

### SSL сертификаты

Для production окружения рекомендуется использовать Let's Encrypt сертификаты:

```bash
sudo certbot --nginx -d etl-tst.chococraft.ru
```

### Учетные данные

Для production окружения рекомендуется изменить учетные данные:

```bash
# Создание нового пользователя
sudo htpasswd /etc/nginx/.htpasswd newuser

# Удаление пользователя
sudo htpasswd -D /etc/nginx/.htpasswd olduser
```

## Устранение неполадок

### 401 Unauthorized

Проверьте файл `/etc/nginx/.htpasswd`:
- Убедитесь, что файл существует
- Проверьте правильность учетных данных
- Убедитесь, что файл имеет правильные права доступа

### 404 Not Found

Проверьте конфигурацию Nginx:
- Убедитесь, что файл конфигурации существует в `/etc/nginx/sites-available/`
- Проверьте, что символическая ссылка создана в `/etc/nginx/sites-enabled/`
- Убедитесь, что статические файлы UI находятся в правильной директории

### 502 Bad Gateway

Проверьте приложение Feature Factory:
- Убедитесь, что приложение запущено на порту 8081
- Проверьте логи приложения на наличие ошибок

### Проблемы с SSL

Проверьте SSL сертификаты:
- Убедитесь, что сертификаты существуют по указанным путям
- Проверьте права доступа к файлам сертификатов
- Убедитесь, что сертификаты не истекли

## Логи

Логи Nginx находятся в:
- `/var/log/nginx/etl-tst.chococraft.ru.access.log` - логи доступа
- `/var/log/nginx/etl-tst.chococraft.ru.error.log` - логи ошибок

Для просмотра логов в реальном времени:

```bash
# Просмотр логов доступа
sudo tail -f /var/log/nginx/etl-tst.chococraft.ru.access.log

# Просмотр логов ошибок
sudo tail -f /var/log/nginx/etl-tst.chococraft.ru.error.log
```