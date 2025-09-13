#!/bin/bash

# Скрипт проверки guard для docs - падает, если в /docs есть файлы кроме README.md

echo "Проверяю наличие файлов в /opt/feature-factory/docs (кроме README.md)..."

# Находим все файлы в /docs, исключая README.md и каталоги
files=$(find /opt/feature-factory/docs -type f -not -name "README.md")

if [ -n "$files" ]; then
    echo "НАЙДЕНЫ НОВЫЕ ФАЙЛЫ В /opt/feature-factory/docs (кроме README.md):"
    echo "$files"
    echo ""
    echo "ОШИБКА: Новые файлы не должны добавляться в /opt/feature-factory/docs"
    echo "Документация теперь находится в /opt/feature-factory/cortex"
    exit 1
else
    echo "Проверка пройдена: в /opt/feature-factory/docs нет новых файлов (кроме README.md)"
    exit 0
fi