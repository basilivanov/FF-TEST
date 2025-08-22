#!/bin/bash

# Скрипт для обновления конфигурации Nginx
# Использование: sudo ./update-nginx-config.sh

echo "Остановка Nginx..."
systemctl stop nginx

echo "Копирование новой конфигурации..."
cp /opt/feature-factory/nginx-config/correct-config.conf /etc/nginx/sites-enabled/etl-tst.chococraft.ru

echo "Проверка конфигурации Nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Конфигурация корректна. Запуск Nginx..."
    systemctl start nginx
    echo "Nginx успешно перезапущен."
else
    echo "Ошибка в конфигурации. Восстановление предыдущей конфигурации..."
    # Восстановление предыдущей конфигурации (если была создана резервная копия)
    if [ -f /etc/nginx/sites-enabled/etl-tst.chococraft.ru.backup ]; then
        cp /etc/nginx/sites-enabled/etl-tst.chococraft.ru.backup /etc/nginx/sites-enabled/etl-tst.chococraft.ru
        systemctl start nginx
        echo "Восстановлена предыдущая конфигурация."
    else
        echo "Не удалось восстановить предыдущую конфигурацию. Требуется ручное вмешательство."
    fi
fi