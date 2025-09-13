#!/bin/bash

# Скрипт проверки синхронизации TOC
# Проверяет, что все файлы в /cortex (кроме archive) присутствуют в reference/TOC.md

echo "Проверяю синхронизацию TOC..."

# Создаем список всех файлов в cortex (кроме archive)
find /opt/feature-factory/cortex -type f \( -name '*.md' -o -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) -not -path '*/archive/*' | sort > /tmp/all_cortex_files.txt

# Создаем список файлов из TOC
sed -n 's/^- //p' /opt/feature-factory/cortex/reference/TOC.md | sed 's|^|/opt/feature-factory/cortex/|' | sort > /tmp/toc_files.txt

# Находим сироты (файлы, которые есть в cortex, но отсутствуют в TOC)
orphans=$(comm -23 /tmp/all_cortex_files.txt /tmp/toc_files.txt)

if [ -n "$orphans" ]; then
    echo "НАЙДЕНЫ СИРОТЫ (файлы, отсутствующие в TOC):"
    echo "$orphans"
    echo ""
    echo "ОШИБКА: Найдены файлы в /cortex, которые отсутствуют в reference/TOC.md"
    rm -f /tmp/all_cortex_files.txt /tmp/toc_files.txt
    exit 1
else
    echo "Проверка TOC пройдена: все файлы в /cortex учтены в reference/TOC.md"
    rm -f /tmp/all_cortex_files.txt /tmp/toc_files.txt
    exit 0
fi