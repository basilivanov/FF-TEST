# Отчёт: Диагностика и план хотфикса админки (ETL Test)

- Дата: 2025-08-24
- Хост: etl-tst.chococraft.ru
- Контекст: проверка статики `/assets`, SPA `/admin/`, BasicAuth, API/SSE

## Итог (root cause)
- UI раздаётся через `location /` с `root /opt/feature-factory/app/ui/dist` вместо `/admin/`; отсутствует корректная базовая конфигурация SPA на префиксе `/admin/`.
- Нет явного `location /assets/` с `alias` и кэшированием; на диске `/var/www/etl-tst.chococraft.ru/admin/` отсутствует каталог `assets/` и хэш‑артефакты.
- Прокси для API/SSE не полностью настроено: нет отдельного SSE‑location с `proxy_http_version 1.1`, `Connection ""`, `chunked_transfer_encoding on`; `X-Request-ID` лучше передавать как `$request_id`.
- BasicAuth присутствует, но требуется единый realm/правила для `/admin/` и `/api/`.
- Фактический upstream слушает на 8081 (а не 9090). SSE жив; эндпоинт `features` по GET возвращает 405 (ожидает другой метод), что подтверждает работоспособность приложения.

## Доказательства (snapshots)

### Внешние HTTP
```
$ curl -I https://etl-tst.chococraft.ru/admin/
HTTP/2 401
server: nginx/1.24.0 (Ubuntu)
date: Sun, 24 Aug 2025 21:10:51 GMT
content-type: text/html
content-length: 188
www-authenticate: Basic realm="Admin Area"
strict-transport-security: max-age=86400; includeSubDomains
x-frame-options: DENY
x-content-type-options: nosniff
referrer-policy: no-referrer
```

```
$ curl -I https://etl-tst.chococraft.ru/assets/index-*.css
HTTP/2 401
server: nginx/1.24.0 (Ubuntu)
date: Sun, 24 Aug 2025 21:10:51 GMT
content-type: text/html
content-length: 188
www-authenticate: Basic realm="Admin Area"
```

### Upstream (обход BasicAuth)
```
$ curl -D - -sS http://127.0.0.1:8081/api/v1/orchestrator/features?limit=1
HTTP/1.1 405 Method Not Allowed
date: Sun, 24 Aug 2025 21:11:02 GMT
server: uvicorn
allow: POST
content-length: 31
content-type: application/json
x-correlation-id: 7585d03f-5f93-4ac4-b678-56c0f3e43688

{"detail":"Method Not Allowed"}
```

```
$ curl -N --max-time 3 -sS http://127.0.0.1:8081/api/v1/stream/events
event: connection_opened
data: {"connection_id": "e7c58496-5aa5-4040-b00b-9029287c48ee"}

event: job_started
data: {"job_id": "job-1", "task_id": "task-1", "run_id": "run-1", "correlation_id": "e6236a23-e27d-4578-a29c-2108704ec892", "timestamp": 1756069862.630976}

event: job_finished
data: {"job_id": "job-1", "task_id": "task-1", "run_id": "run-1", "correlation_id": "ed3d0a54-854f-41a1-a3ff-f8eed89bd204", "timestamp": 1756069864.6318934, "result": "success"}
```

### FS (статика)
```
$ ls -la /var/www/etl-tst.chococraft.ru/admin/
total 16
drwxr-xr-x 2 feature feature 4096 авг 22 10:28 .
drwxr-xr-x 3 feature feature 4096 авг 22 10:28 ..
-rw-r--r-- 1 feature feature 6891 авг 22 10:28 index.html
```

```
$ ls -la /var/www/etl-tst.chococraft.ru/admin/assets
ls: cannot access '/var/www/etl-tst.chococraft.ru/admin/assets': No such file or directory
```

### Конфигурация Nginx (server{})
Файл: `/etc/nginx/sites-available/etl-tst.chococraft.ru`
```
server {
    listen 80;
    server_name etl-tst.chococraft.ru;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
        default_type text/plain;
    }

    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name etl-tst.chococraft.ru;

    ssl_certificate /etc/letsencrypt/live/etl-tst.chococraft.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/etl-tst.chococraft.ru/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=86400; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer" always;

    location / {
        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        root /opt/feature-factory/app/ui/dist;
        try_files $uri $uri/ /index.html;
        location = /index.html {
            add_header Cache-Control "no-store, no-cache, must-revalidate";
        }
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    location /api/ {
        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Request-ID $http_x_request_id;
        proxy_set_header Authorization $http_authorization;
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    location /admin {
        auth_basic "Admin Area"; 
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8081/admin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Request-ID $http_x_request_id;
        proxy_set_header Authorization $http_authorization;
    }

    access_log /var/log/nginx/etl-tst.chococraft.ru.access.log combined;
    error_log /var/log/nginx/etl-tst.chococraft.ru.error.log;
}
```

### Журналы Nginx
```
$ journalctl -u nginx -n 50 --no-pager
<нет новых записей>
```

### Контрольные суммы
```
$ sha256sum /etc/nginx/sites-available/*
ce0901350a021608139b5639cf4ccd7717bef8c3a9e4f79031eb46386b67b03f  /etc/nginx/sites-available/default
8c64ae7573b14090aee96c6975d19c8bd4f29debbbf4be493d57f0a7e06c8a91  /etc/nginx/sites-available/etl-tst.chococraft.ru
af7da98aae35fb9265d47a01701469c10c42b9f7e984edc3bf57c98e4d9c4de0  /etc/nginx/sites-available/etl-tst.chococraft.ru.backup_no_ssl
f6d5f097a9bb30a7f96094b3f6bd2e5679cea37fd96f023dd47378edd3efdd77  /etc/nginx/sites-available/etl-tst.chococraft.ru.backup_ssl
```

## Статус выполнения задач
- Диагностика (RO): выполнена полностью; артефакты и выводы выше.
- Хотфикс Nginx (WRITE): не применён (нет sudo); подготовлен детальный план правок.
- Smoke после хотфикса: не выполнялся (ожидает применения хотфикса/деплоя).
- Пересборка UI с base=/admin/: попытка выполнена, сборка упала на TypeScript‑ошибках; требуется исправление типизации или временное отключение `tsc` в скрипте prod‑сборки.

## План хотфикса (кратко)
- `location ^~ /admin/ { alias /var/www/etl-tst.chococraft.ru/admin/; try_files $uri $uri/ /admin/index.html; }`
- `location ^~ /assets/ { alias /var/www/etl-tst.chococraft.ru/admin/assets/; add_header Cache-Control "public, max-age=31536000, immutable"; }`
- `location ^~ /api/ { proxy_pass http://127.0.0.1:8081/; proxy_set_header X-Request-ID $request_id; proxy_set_header X-Forwarded-Proto https; proxy_set_header Authorization $http_authorization; proxy_buffering off; }`
- `location = /api/v1/stream/events { proxy_http_version 1.1; proxy_set_header Connection ""; proxy_buffering off; chunked_transfer_encoding on; }`
- Единый `auth_basic "Admin Area";` для `/admin/` и `/api/`.
- `nginx -t` и `systemctl reload nginx` после правок.

## Деплой UI (после фикса)
- Сборка: `vite build --base=/admin/` (или экспорт `VITE_BASE=/admin/`).
- Деплой: атомарно в `/var/www/etl-tst.chococraft.ru/admin/` (новая папка + symlink switch).
- Кэш: `index.html` — no-store/no-cache; `assets` — 1y immutable.

## Rollback (Nginx)
- Восстановить бэкап конфига и выполнить: `nginx -t && systemctl reload nginx`.

---

Примечания:
- `nginx -T` от рута не выполнен (sudo недоступен); вместо этого использованы файлы конфигурации и внешние curl‑проверки.
- Upstream доступен на `127.0.0.1:8081`; порт `9090` не слушает (по `ss -ltnp`).
