#!/bin/bash

# Скрипт проверки oversized файлов
# Проверяет, что нет файлов >200KB вне archive

echo "Проверяю наличие oversized файлов вне archive..."

# Находим файлы >200KB вне каталога archive
oversized_files=$(find /opt/feature-factory/cortex -type f -not -path '*/archive/*' -size +200k)

if [ -n "$oversized_files" ]; then
    echo "НАЙДЕНЫ OVERSIZED ФАЙЛЫ ВНЕ ARCHIVE:"
    echo "$oversized_files"
    echo ""
    echo "ОШИБКА: Найдены файлы >200KB вне каталога archive"
    exit 1
else
    echo "Проверка oversized файлов пройдена: нет файлов >200KB вне archive"
    exit 0
fi