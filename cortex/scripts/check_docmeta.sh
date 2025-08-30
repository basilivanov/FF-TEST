#!/bin/bash

# Скрипт проверки наличия FF-DocMeta в .md файлах
# Проверяет, что каждый .md содержит FF-DocMeta с purpose/owner/lifecycle

echo "Проверяю наличие FF-DocMeta в .md файлах..."

# Находим все .md файлы в cortex (кроме archive)
find /opt/feature-factory/cortex -type f -name '*.md' -not -path '*/archive/*' > /tmp/md_files.txt

missing_docmeta=0

while IFS= read -r file; do
    # Проверяем наличие FF-DocMeta
    if ! grep -q "<!-- FF-DocMeta" "$file"; then
        echo "ОШИБКА: В файле $file отсутствует FF-DocMeta"
        missing_docmeta=1
        continue
    fi
    
    # Проверяем наличие обязательных полей
    if ! grep -q "purpose:" "$file"; then
        echo "ОШИБКА: В файле $file отсутствует поле 'purpose' в FF-DocMeta"
        missing_docmeta=1
    fi
    
    if ! grep -q "owner:" "$file"; then
        echo "ОШИБКА: В файле $file отсутствует поле 'owner' в FF-DocMeta"
        missing_docmeta=1
    fi
    
    if ! grep -q "lifecycle:" "$file"; then
        echo "ОШИБКА: В файле $file отсутствует поле 'lifecycle' в FF-DocMeta"
        missing_docmeta=1
    fi
done < /tmp/md_files.txt

if [ $missing_docmeta -eq 1 ]; then
    echo ""
    echo "ОШИБКА: Найдены .md файлы без необходимых FF-DocMeta"
    rm -f /tmp/md_files.txt
    exit 1
else
    echo "Проверка FF-DocMeta пройдена: все .md файлы содержат необходимые метаданные"
    rm -f /tmp/md_files.txt
    exit 0
fi