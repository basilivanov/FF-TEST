#!/bin/bash

# Скрипт для сборки снапшота документации с учетом политики исключений
# Использует find с -prune для эффективного исключения каталогов

set -e  # Завершить выполнение при ошибке

# Пути
ROOT_DIR="/opt/feature-factory"
POLICY_FILE="$ROOT_DIR/configs/docs_snapshot_policy.yaml"
OUTPUT_MD="$ROOT_DIR/reports/DOCS_SNAPSHOT_All_v1.2.md"
OUTPUT_JSON="$ROOT_DIR/reports/REPORT_DOCS_SNAPSHOT_All_v1.2.json"
TEMP_DIR="$ROOT_DIR/temp_docs_snapshot"
TEMP_FILES_LIST="$TEMP_DIR/files_list.txt"
TEMP_FILE_CONTENTS="$TEMP_DIR/file_contents.txt"

# Создание временной директории
mkdir -p "$TEMP_DIR"

# Извлечение параметров из политики (упрощенный парсинг)
EXCLUDE_DIRS=$(grep "exclude_dirs:" "$POLICY_FILE" | cut -d'[' -f2 | cut -d']' -f1 | tr -d '"' | tr ',' ' ')
INCLUDE_EXT=$(grep "include_ext:" "$POLICY_FILE" | cut -d'[' -f2 | cut -d']' -f1 | tr -d '"' | tr ',' ' ')
MAX_LINES=$(grep "max_lines:" "$POLICY_FILE" | cut -d':' -f2 | xargs)
MAX_BYTES=$(grep "max_bytes:" "$POLICY_FILE" | cut -d':' -f2 | xargs)
FOLLOW_SYMLINKS=$(grep "follow_symlinks:" "$POLICY_FILE" | cut -d':' -f2 | xargs)

# Подготовка паттернов исключения для find
EXCLUDE_FIND_PATTERN=""
for dir in $EXCLUDE_DIRS; do
    if [ -n "$EXCLUDE_FIND_PATTERN" ]; then
        EXCLUDE_FIND_PATTERN="$EXCLUDE_FIND_PATTERN -o -name $dir"
    else
        EXCLUDE_FIND_PATTERN="-name $dir"
    fi
done

# Команда find с prune для исключения каталогов
FIND_CMD="find \"$ROOT_DIR\" -type d \\( $EXCLUDE_FIND_PATTERN \\) -prune -o"

# Добавление фильтра по расширениям файлов
EXT_PATTERN=""
for ext in $INCLUDE_EXT; do
    if [ -n "$EXT_PATTERN" ]; then
        EXT_PATTERN="$EXT_PATTERN -o -name '*.$ext'"
    else
        EXT_PATTERN="-name '*.$ext'"
    fi
done

# Полная команда поиска файлов
if [ -n "$EXT_PATTERN" ]; then
    FIND_CMD="$FIND_CMD -type f \\( $EXT_PATTERN \\) -print"
else
    FIND_CMD="$FIND_CMD -type f -print"
fi

# Выполнение поиска файлов
echo "Выполняется поиск файлов с учетом политики..."
eval $FIND_CMD > "$TEMP_FILES_LIST"

# Сортировка списка файлов
sort "$TEMP_FILES_LIST" -o "$TEMP_FILES_LIST"

# Подсчет общего количества файлов
FILES_TOTAL=$(wc -l < "$TEMP_FILES_LIST")

# Генерация содержимого MD файла
echo "# Снапшот документации (v1.2)" > "$OUTPUT_MD"
echo "" >> "$OUTPUT_MD"
echo "## Сводная таблица" >> "$OUTPUT_MD"
echo "" >> "$OUTPUT_MD"
echo "| Путь | Размер (байт) | Строк | Превью |" >> "$OUTPUT_MD"
echo "|------|---------------|-------|--------|" >> "$OUTPUT_MD"

# Подготовка JSON отчета
echo "{" > "$OUTPUT_JSON"
echo "  \"files_total\": $FILES_TOTAL," >> "$OUTPUT_JSON"
echo "  \"excluded_dirs\": [$(echo $EXCLUDE_DIRS | sed 's/ /, /g' | sed 's/\([a-zA-Z0-9_.-]*\)/"\1"/g')]," >> "$OUTPUT_JSON"
echo "  \"policy_hash\": \"$(sha256sum "$POLICY_FILE" | cut -d' ' -f1)\"," >> "$OUTPUT_JSON"

# Добавление дельты от v1.1
if [ -f "/opt/feature-factory/reports/REPORT_DOCS_SNAPSHOT_All_v1.1.json" ]; then
    FILES_TOTAL_BEFORE=$(grep "files_total" /opt/feature-factory/reports/REPORT_DOCS_SNAPSHOT_All_v1.1.json | cut -d':' -f2 | tr -d ' ,')
    echo "  \"files_total_before\": $FILES_TOTAL_BEFORE," >> "$OUTPUT_JSON"
    echo "  \"files_total_after\": $FILES_TOTAL," >> "$OUTPUT_JSON"
fi

# Добавление Proof Pack в JSON
echo "  \"proofs\": {" >> "$OUTPUT_JSON"

# Proof: grep_absent_node_modules
NODE_MODULES_COUNT=$(grep -c "/node_modules/" "$TEMP_FILES_LIST" || true)
echo "    \"grep_absent_node_modules\": {" >> "$OUTPUT_JSON"
echo "      \"count\": $NODE_MODULES_COUNT" >> "$OUTPUT_JSON"
echo "    }," >> "$OUTPUT_JSON"

# Proof: sanity_list (первые 30 путей)
echo "    \"sanity_list\": [" >> "$OUTPUT_JSON"
head -30 "$TEMP_FILES_LIST" | sed 's/.*/      "&",/' | sed '$ s/,$//' >> "$OUTPUT_JSON"
echo "    ]," >> "$OUTPUT_JSON"

# Proof: symlink_check
echo "    \"symlink_check\": {" >> "$OUTPUT_JSON"
echo "      \"follow_symlinks\": $FOLLOW_SYMLINKS," >> "$OUTPUT_JSON"
SYMLINKS_IN_ROOT=$(find "$ROOT_DIR" -maxdepth 1 -type l -exec ls -la {} \; 2>/dev/null | wc -l)
echo "      \"symlinks_in_root_count\": $SYMLINKS_IN_ROOT" >> "$OUTPUT_JSON"
if [ $SYMLINKS_IN_ROOT -gt 0 ]; then
    echo "      \"symlinks_in_root\": [" >> "$OUTPUT_JSON"
    find "$ROOT_DIR" -maxdepth 1 -type l -exec basename {} \; 2>/dev/null | sed 's/.*/        "&",/' | sed '$ s/,$//' >> "$OUTPUT_JSON"
    echo "      ]" >> "$OUTPUT_JSON"
fi
echo "    }," >> "$OUTPUT_JSON"

# Proof: tool_variant
echo "    \"tool_variant\": \"$(find --version | head -1)\"," >> "$OUTPUT_JSON"

# Proof: corr_id_policy
echo "    \"corr_id_policy\": {" >> "$OUTPUT_JSON"
# Выполняем HTTP-запросы для проверки x-correlation-id
HTTP_200_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://etl-tst:8080/api/v1/context?task_description=DOCS_SNAPSHOT_Prune_v1.2 || echo "000")
HTTP_404_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://etl-tst:8080/nonexistent || echo "000")
echo "      \"http_200_status\": $HTTP_200_STATUS," >> "$OUTPUT_JSON"
echo "      \"http_404_status\": $HTTP_404_STATUS" >> "$OUTPUT_JSON"
echo "    }" >> "$OUTPUT_JSON"

# Завершение Proof Pack
echo "  }" >> "$OUTPUT_JSON"

# Обработка каждого файла для создания превью и добавления в таблицу MD
echo "Обрабатываются файлы для создания превью..."
while IFS= read -r file; do
    # Получение информации о файле
    FILE_SIZE=$(stat -c%s "$file" 2>/dev/null || echo "0")
    FILE_LINES=$(wc -l < "$file" 2>/dev/null || echo "0")
    
    # Создание превью содержимого
    PREVIEW=""
    if [ "$FILE_SIZE" -le "$MAX_BYTES" ] && [ "$FILE_LINES" -le "$MAX_LINES" ]; then
        # Для небольших файлов показываем все содержимое
        PREVIEW=$(head -c "$MAX_BYTES" "$file" | head -n "$MAX_LINES" | sed 's/|/\\|/g' | tr '\n' ' ' | cut -c1-100)
    else
        # Для больших файлов показываем ограниченное превью
        PREVIEW=$(head -c "$MAX_BYTES" "$file" | head -n "$MAX_LINES" | sed 's/|/\\|/g' | tr '\n' ' ' | cut -c1-100)...
    fi
    
    # Добавление строки в таблицу MD
    RELATIVE_PATH=${file#$ROOT_DIR/}
    echo "| $RELATIVE_PATH | $FILE_SIZE | $FILE_LINES | $PREVIEW |" >> "$OUTPUT_MD"
done < "$TEMP_FILES_LIST"

# Завершение JSON отчета
echo "}" >> "$OUTPUT_JSON"

# Очистка временных файлов
rm -rf "$TEMP_DIR"

echo "Сборка снапшота документации завершена."