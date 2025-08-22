#!/bin/bash
# Скрипт для настройки доменов и HTTPS для test/prod окружений

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Настройка доменов и HTTPS для Feature Factory${NC}"

# Проверяем, что скрипт запущен от root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Этот скрипт должен быть запущен от root${NC}" 
   exit 1
fi

# Создаем директории для SSL сертификатов
echo -e "${YELLOW}Создаем директории для SSL сертификатов...${NC}"
mkdir -p /etc/ssl/certs
mkdir -p /etc/ssl/private

# Копируем конфигурационные файлы Nginx
echo -e "${YELLOW}Копируем конфигурационные файлы Nginx...${NC}"
cp /opt/feature-factory/configs/nginx/etl-tst.chococraft.ru /etc/nginx/sites-available/
cp /opt/feature-factory/configs/nginx/etl.chococraft.ru /etc/nginx/sites-available/

# Создаем символические ссылки для включения сайтов
echo -e "${YELLOW}Создаем символические ссылки для включения сайтов...${NC}"
ln -sf /etc/nginx/sites-available/etl-tst.chococraft.ru /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/etl.chococraft.ru /etc/nginx/sites-enabled/

# Копируем systemd сервисы
echo -e "${YELLOW}Копируем systemd сервисы...${NC}"
cp /opt/feature-factory/configs/feature-factory-prod.service /etc/systemd/system/
cp /opt/feature-factory/configs/feature-factory-test.service /etc/systemd/system/

# Копируем файлы окружения
echo -e "${YELLOW}Копируем файлы окружения...${NC}"
cp /opt/feature-factory/configs/feature-factory-prod.env /etc/default/feature-factory-prod
cp /opt/feature-factory/configs/feature-factory-test.env /etc/default/feature-factory-test

# Перезагружаем systemd
echo -e "${YELLOW}Перезагружаем systemd...${NC}"
systemctl daemon-reload

# Запускаем и включаем сервисы
echo -e "${YELLOW}Запускаем и включаем сервисы...${NC}"
systemctl enable feature-factory-prod.service
systemctl enable feature-factory-test.service
systemctl start feature-factory-prod.service
systemctl start feature-factory-test.service

# Перезагружаем Nginx
echo -e "${YELLOW}Перезагружаем Nginx...${NC}"
systemctl reload nginx

echo -e "${GREEN}Настройка завершена!${NC}"
echo -e "${YELLOW}Не забудьте установить SSL сертификаты в следующие директории:${NC}"
echo -e "  - /etc/ssl/certs/etl-tst.chococraft.ru.crt"
echo -e "  - /etc/ssl/private/etl-tst.chococraft.ru.key"
echo -e "  - /etc/ssl/certs/etl.chococraft.ru.crt"
echo -e "  - /etc/ssl/private/etl.chococraft.ru.key"