#!/bin/bash
# Скрипт для проверки доступности доменов и правильности настройки HTTPS

echo "Проверка доступности доменов..."

# Проверяем тестовый домен
echo "Проверка etl-tst.chococraft.ru..."
curl -I -s -o /dev/null -w "HTTP код ответа: %{http_code}\n" https://etl-tst.chococraft.ru/admin || echo "Ошибка доступа к etl-tst.chococraft.ru"

# Проверяем продакшн-домен
echo "Проверка etl.chococraft.ru..."
curl -I -s -o /dev/null -w "HTTP код ответа: %{http_code}\n" https://etl.chococraft.ru/admin || echo "Ошибка доступа к etl.chococraft.ru"

echo "Проверка завершена."