#!/bin/bash

# Общий скрипт для запуска всех проверок CI

echo "=== ЗАПУСК ВСЕХ ПРОВЕРОК CI ==="
echo

# Проверка guard для docs
echo "1. Проверка guard для docs:"
if /opt/feature-factory/cortex/scripts/check_docs_guard.sh; then
    echo "✓ Проверка guard для docs пройдена"
else
    echo "✗ Проверка guard для docs НЕ ПРОЙДЕНА"
    exit 1
fi
echo

# Проверка синхронизации TOC
echo "2. Проверка синхронизации TOC:"
if /opt/feature-factory/cortex/scripts/check_toc_sync.sh; then
    echo "✓ Проверка TOC пройдена"
else
    echo "✗ Проверка TOC НЕ ПРОЙДЕНА"
    exit 1
fi
echo

# Проверка FF-DocMeta
echo "3. Проверка FF-DocMeta:"
if /opt/feature-factory/cortex/scripts/check_docmeta.sh; then
    echo "✓ Проверка FF-DocMeta пройдена"
else
    echo "✗ Проверка FF-DocMeta НЕ ПРОЙДЕНА"
    exit 1
fi
echo

# Проверка oversized файлов
echo "4. Проверка oversized файлов:"
if /opt/feature-factory/cortex/scripts/check_oversized.sh; then
    echo "✓ Проверка oversized файлов пройдена"
else
    echo "✗ Проверка oversized файлов НЕ ПРОЙДЕНА"
    exit 1
fi
echo

echo "=== ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО ==="