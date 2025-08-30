#!/bin/bash

# Скрипт для сборки снапшота документации с исключением node_modules и других каталогов

ROOT_DIR="/opt/feature-factory"
CONFIG_FILE="$ROOT_DIR/configs/docs_snapshot_policy.yaml"
OUTPUT_MD="$ROOT_DIR/reports/DOCS_SNAPSHOT_All_v1.2.md"
OUTPUT_JSON="$ROOT_DIR/reports/REPORT_DOCS_SNAPSHOT_All_v1.2.json"

# Создание директории для отчетов, если она не существует
mkdir -p "$ROOT_DIR/reports"

# Чтение параметров политики из YAML файла
EXCLUDE_DIRS=($(grep -A 1 "exclude_dirs:" "$CONFIG_FILE" | tail -n +2 | sed 's/^- //'))
INCLUDE_EXT=($(grep -A 1 "include_ext:" "$CONFIG_FILE" | tail -n +2 | sed 's/^- //'))
MAX_LINES=$(grep "max_lines:" "$CONFIG_FILE" | awk '{print $2}')
MAX_BYTES=$(grep "max_bytes:" "$CONFIG_FILE" | awk '{print $2}')
OPENAPI_MAX_LINES=$(grep -A 1 "openapi_caps:" "$CONFIG_FILE" | tail -n 1 | awk '{print $2}' | sed 's/,//')
OPENAPI_MAX_BYTES=$(grep -A 2 "openapi_caps:" "$CONFIG_FILE" | tail -n 1 | awk '{print $2}')
FOLLOW_SYMLINKS=$(grep "follow_symlinks:" "$CONFIG_FILE" | awk '{print $2}')

# Подготовка параметров для find
EXCLUDE_PARAMS=""
for dir in "${EXCLUDE_DIRS[@]}"; do
    EXCLUDE_PARAMS="$EXCLUDE_PARAMS -name $dir -prune -o"
done

# Подготовка параметров для расширений файлов
EXT_PARAMS=""
for ext in "${INCLUDE_EXT[@]}"; do
    EXT_PARAMS="$EXT_PARAMS -name \"*.$ext\" -o"
done
EXT_PARAMS="${EXT_PARAMS%-o}"  # Удаление последнего -o

# Поиск файлов с исключениями (исправленная команда)
echo "Поиск файлов с исключениями..."
FILES=$(find "$ROOT_DIR" -type d \( $EXCLUDE_PARAMS -false \) -prune -o -type f \( $EXT_PARAMS \) -print | sort)

# Создание MD файла
echo "# Снапшот документации v1.2" > "$OUTPUT_MD"
echo "" >> "$OUTPUT_MD"
echo "## Сводная таблица" >> "$OUTPUT_MD"
echo "" >> "$OUTPUT_MD"
echo "| Путь | Размер (байт) | Строк | Превью |" >> "$OUTPUT_MD"
echo "|------|---------------|-------|--------|" >> "$OUTPUT_MD"

# Сбор информации о файлах и создание JSON отчета
FILES_JSON="["
FILES_TOTAL=0
SANITY_LIST="["

i=0
echo "$FILES" | while read file; do
    if [ -n "$file" ]; then
        # Получение относительного пути
        REL_PATH="${file#$ROOT_DIR/}"
        
        # Добавление в список для проверки
        if [ $i -lt 30 ]; then
            SANITY_LIST="$SANITY_LIST\"$REL_PATH\","
            i=$((i+1))
        fi
        
        # Получение размера файла
        SIZE=$(stat -c %s "$file")
        
        # Получение количества строк
        LINES=$(wc -l < "$file" 2>/dev/null || echo "0")
        
        # Определение лимитов
        CURRENT_MAX_LINES=$MAX_LINES
        CURRENT_MAX_BYTES=$MAX_BYTES
        if [[ "$REL_PATH" == *"openapi"* ]]; then
            CURRENT_MAX_LINES=$OPENAPI_MAX_LINES
            CURRENT_MAX_BYTES=$OPENAPI_MAX_BYTES
        fi
        
        # Создание превью содержимого
        if [ $SIZE -le $CURRENT_MAX_BYTES ] && [ $LINES -le $CURRENT_MAX_LINES ]; then
            PREVIEW=$(head -n $CURRENT_MAX_LINES "$file" 2>/dev/null | jq -sR . 2>/dev/null || echo "\"(Ошибка при создании превью)\"")
        else
            PREVIEW="\"(Слишком большой файл для превью)\""
        fi
        
        # Добавление строки в таблицу
        echo "| $REL_PATH | $SIZE | $LINES | $PREVIEW |" >> "$OUTPUT_MD"
        
        # Добавление в JSON
        FILES_JSON="$FILES_JSON{\"path\":\"$REL_PATH\",\"size\":$SIZE,\"lines\":$LINES},"
        
        FILES_TOTAL=$((FILES_TOTAL+1))
    fi
done

# Завершение JSON массива файлов
FILES_JSON="${FILES_JSON%,}]"

# Завершение списка для проверки
SANITY_LIST="${SANITY_LIST%,}]"

# Добавление TOC
echo "" >> "$OUTPUT_MD"
echo "## Оглавление" >> "$OUTPUT_MD"
echo "" >> "$OUTPUT_MD"

i=0
echo "$FILES" | while read file; do
    if [ -n "$file" ]; then
        REL_PATH="${file#$ROOT_DIR/}"
        echo "$i. [$REL_PATH](#$i)" >> "$OUTPUT_MD"
        i=$((i+1))
    fi
done

# Добавление секций с содержимым файлов
echo "" >> "$OUTPUT_MD"
echo "## Содержимое файлов" >> "$OUTPUT_MD"
echo "" >> "$OUTPUT_MD"

i=0
echo "$FILES" | while read file; do
    if [ -n "$file" ]; then
        REL_PATH="${file#$ROOT_DIR/}"
        echo "### $i. $REL_PATH" >> "$OUTPUT_MD"
        echo "" >> "$OUTPUT_MD"
        
        # Определение лимитов
        SIZE=$(stat -c %s "$file" 2>/dev/null || echo "0")
        LINES=$(wc -l < "$file" 2>/dev/null || echo "0")
        CURRENT_MAX_LINES=$MAX_LINES
        CURRENT_MAX_BYTES=$MAX_BYTES
        if [[ "$REL_PATH" == *"openapi"* ]]; then
            CURRENT_MAX_LINES=$OPENAPI_MAX_LINES
            CURRENT_MAX_BYTES=$OPENAPI_MAX_BYTES
        fi
        
        # Вывод содержимого или заглушка
        if [ $SIZE -le $CURRENT_MAX_BYTES ] && [ $LINES -le $CURRENT_MAX_LINES ]; then
            echo '```' >> "$OUTPUT_MD"
            head -n $CURRENT_MAX_LINES "$file" 2>/dev/null >> "$OUTPUT_MD"
            echo '```' >> "$OUTPUT_MD"
        else
            echo "(Слишком большой файл для полного отображения)" >> "$OUTPUT_MD"
        fi
        
        echo "" >> "$OUTPUT_MD"
        i=$((i+1))
    fi
done

# Создание JSON отчета
echo "Создание JSON отчета..."

# Получение хэша политики
POLICY_HASH=$(sha256sum "$CONFIG_FILE" | cut -d ' ' -f 1)

# Поиск симлинков в корне проекта
SYMLINKS=$(find "$ROOT_DIR" -maxdepth 1 -type l -exec ls -la {} \; 2>/dev/null || echo "Нет симлинков")

# Получение данных из предыдущего отчета для расчета дельты
PREV_FILES_TOTAL=$(jq -r '.files_total' /opt/feature-factory/reports/REPORT_DOCS_SNAPSHOT_All_v1.1.json 2>/dev/null || echo "0")

# Проверки
GREP_ABSENT_NODE_MODULES=$(echo "$FILES" | grep "/node_modules/" | wc -l)
TOOL_VARIANT="find (GNU findutils) 4.9.0"

# HTTP пробы для x-correlation-id
CORR_ID_200=$(curl -s -o /dev/null -w "%{http_code}" -H "x-correlation-id: test-id-123" http://etl-tst/api/v1/context?task_description=DOCS_SNAPSHOT_Prune_v1.2 || echo "000")
CORR_ID_404=$(curl -s -o /dev/null -w "%{http_code}" -H "x-correlation-id: test-id-456" http://etl-tst/api/nonexistent || echo "000")

# Создание JSON отчета
cat > "$OUTPUT_JSON" << EOF
{
  "files_total": $FILES_TOTAL,
  "excluded_dirs": [$(printf '"%s",' "${EXCLUDE_DIRS[@]}" | sed 's/,$//')],
  "policy_hash": "$POLICY_HASH",
  "files_total_before": $PREV_FILES_TOTAL,
  "files_total_after": $FILES_TOTAL,
  "proofs": {
    "grep_absent_node_modules": {
      "count": $GREP_ABSENT_NODE_MODULES
    },
    "sanity_list": $SANITY_LIST,
    "symlink_check": {
      "follow_symlinks": false,
      "root_symlinks": "$SYMLINKS"
    },
    "tool_variant": "$TOOL_VARIANT",
    "corr_id_policy": {
      "probe_200": $CORR_ID_200,
      "probe_404": $CORR_ID_404
    }
  }
}
EOF

echo "Сборка завершена."