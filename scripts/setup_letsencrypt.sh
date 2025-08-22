#!/bin/bash

# Скрипт для настройки Let's Encrypt сертификатов для Feature Factory
# Использование: sudo ./setup_letsencrypt.sh

set -e

DOMAIN="etl-tst.chococraft.ru"
WEBROOT="/var/www/html"

echo "Настройка Let's Encrypt для домена $DOMAIN"

# Проверка, установлен ли certbot
if ! command -v certbot &> /dev/null; then
    echo "Certbot не найден. Устанавливаем..."
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# Создание директории для webroot, если она не существует
mkdir -p $WEBROOT

# Получение сертификата с использованием webroot
certbot certonly --webroot -w $WEBROOT -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Обновление конфигурации Nginx для использования полученных сертификатов
# Эта часть уже реализована в файле конфигурации

# Настройка автоматического обновления сертификатов
echo "Настройка автоматического обновления сертификатов"
crontab -l > /tmp/crontab.backup 2>/dev/null || true
echo "0 12 * * * /usr/bin/certbot renew --quiet" >> /tmp/crontab.backup
crontab /tmp/crontab.backup

echo "Настройка завершена успешно!"
echo "Пожалуйста, перезагрузите Nginx для применения изменений:"
echo "sudo systemctl reload nginx"