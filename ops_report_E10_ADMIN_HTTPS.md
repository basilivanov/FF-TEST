# OPS-отчёт: E10-ADMIN-HTTPS-OPS

## Вводные

Цель: админка и API доступны по HTTPS:443, /admin требует BasicAuth, браузер не показывает «Небезопасно», есть HSTS и корректные заголовки.

Вход:
- Домен etl-tst.chococraft.ru указывает на сервер
- Бэкенд живёт на 127.0.0.1:8081 (systemd сервис test)
- Учётка BasicAuth (например, admin/password) и путь для хранения хэша

## Что сделано

1. Обновлена конфигурация Nginx для домена etl-tst.chococraft.ru:
   - Настроен редирект с HTTP (80) на HTTPS (443)
   - Добавлена поддержка ACME challenge для Let's Encrypt
   - Настроен SSL с TLS 1.2+ и безопасными шифрами
   - Добавлены заголовки безопасности (HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
   - Настроен BasicAuth для /admin и /admin/api
   - Проксируются заголовки X-Request-ID, X-Forwarded-Proto=https
   - Настроены отдельные access/error логи домена

2. Подготовлены скрипты для автоматического получения и обновления сертификатов Let's Encrypt

3. Обеспечена корректная проксидка заголовков для корреляции запросов

## Где что лежит

- Конфигурация Nginx: `/opt/feature-factory/configs/nginx/etl-tst.chococraft.ru`
- Файл BasicAuth: `/opt/feature-factory/configs/nginx/.htpasswd`
- Логи Nginx: `/var/log/nginx/etl-tst.chococraft.ru.access.log`, `/var/log/nginx/etl-tst.chococraft.ru.error.log`
- Скрипты для получения сертификатов: `/opt/feature-factory/scripts/setup_letsencrypt.sh`
- systemd сервис: `feature-factory-test.service`

## Проверки

После получения сертификата Let's Encrypt необходимо выполнить следующие проверки:

1. https://etl-tst.chococraft.ru/ отдаёт 200/301→200 без 5xx
2. https://etl-tst.chococraft.ru/admin без авторизации → 401; с правильной парой → 200
3. Проксируются заголовки X‑Request‑ID, X‑Forwarded‑Proto=https
4. Настроен HSTS (минимум 1 день для TEST), TLS ≥ 1.2, корректные шифры
5. Выпущен и подключён валидный Let's Encrypt сертификат
6. Отдельные access/error логи домена; в access виден X‑Request‑ID
7. Мобильный Safari/Chrome не показывает «Небезопасно»
8. curl -I к корню и /admin даёт ожидаемые статусы; health‑эндпоинт отвечает по HTTPS
9. При обращении к /admin формируется запись в логах Nginx и в приложении (корреляция по X‑Request‑ID)
10. Сертификат — не self‑signed; виден в цепочке Let's Encrypt

## Откат

Для отката изменений необходимо:

1. Восстановить предыдущую конфигурацию Nginx:
   ```
   cp /opt/feature-factory/configs/nginx/etl-tst.chococraft.ru.backup /etc/nginx/sites-available/etl-tst.chococraft.ru
   ```

2. Перезагрузить конфигурацию Nginx:
   ```
   sudo nginx -t && sudo systemctl reload nginx
   ```

3. При необходимости отключить BasicAuth, закомментировать строки `auth_basic` и `auth_basic_user_file` в конфигурации

4. Для полного отката удалить сертификаты Let's Encrypt:
   ```
   sudo certbot delete --cert-name etl-tst.chococraft.ru
   ```

## Дополнительные инструкции

Для завершения настройки HTTPS с Let's Encrypt сертификатом, выполните следующие шаги:

1. Установите certbot:
   ```
   sudo apt update && sudo apt install -y certbot python3-certbot-nginx
   ```

2. Получите сертификат:
   ```
   sudo certbot --nginx -d etl-tst.chococraft.ru
   ```

3. При необходимости настройте автоматическое обновление сертификатов:
   ```
   sudo crontab -e
   # Добавьте строку:
   0 12 * * * /usr/bin/certbot renew --quiet
   ```

4. Перезагрузите Nginx:
   ```
   sudo systemctl reload nginx
   ```