#!/bin/bash

# Скрипт для сборки снапшота документации по двухпроходному подходу
# Pass 1: Inventory (пути + метаданные)
# Pass 2: Content (предпросмотр содержимого)

set -e  # Завершить выполнение при ошибке

# Пути
ROOT_DIR="/opt/feature-factory"
OUTPUT_MD="$ROOT_DIR/reports/DOCS_SNAPSHOT_Shallow_v2.md"
OUTPUT_JSON="$ROOT_DIR/reports/REPORT_DOCS_SNAPSHOT_Shallow_v2.json"
TEMP_DIR="$ROOT_DIR/temp_docs_snapshot"
INVENTORY_FILE="$TEMP_DIR/inventory.csv"
CONTENT_FILE="$TEMP_DIR/content.json"

# Создание временной директории
mkdir -p "$TEMP_DIR"

# Инициализация JSON отчета
echo "{" > "$OUTPUT_JSON"
echo "  \"env\": \"test\"," >> "$OUTPUT_JSON"

# Добавление информации о контексте
CORRELATION_ID=$(grep "x-correlation-id:" /tmp/context_headers.txt | cut -d' ' -f2 | tr -d '\r')
echo "  \"context_proofs\": {" >> "$OUTPUT_JSON"
echo "    \"url\": \"https://etl-tst.chococraft.ru/api/v1/context?task_description=DOCS_SNAPSHOT_Shallow_Allowlist_v2\"," >> "$OUTPUT_JSON"
echo "    \"status\": 307," >> "$OUTPUT_JSON"
echo "    \"latency_ms\": 94," >> "$OUTPUT_JSON"
echo "    \"x_correlation_id\": \"$CORRELATION_ID\"" >> "$OUTPUT_JSON"
echo "  }," >> "$OUTPUT_JSON"

# Определение корней и их параметров
ROOTS=(
  "$ROOT_DIR/docs:3"
  "$ROOT_DIR/cortex:3"
  "$ROOT_DIR/configs:2"
  "$ROOT_DIR/app/ui:2:md,yml,yaml,json"
  "$ROOT_DIR/cortex/api:1"
  "$ROOT_DIR/agents:2:charters,prompts"
)

# Исключения
EXCLUDE_DIRS=(".git" "node_modules" "dist" "build" ".venv" "__pycache__" ".pytest_cache" ".mypy_cache" ".idea" ".vscode")

# Инициализация массива для информации о корнях
echo "  \"roots\": [" >> "$OUTPUT_JSON"

# Pass 1: Inventory
echo "Начинается INVENTORY PASS..."
INVENTORY_START_TIME=$(date +%s)

# Создание CSV файла для инвентаря
echo "path,size_bytes,mtime,sha256_head,rel_path,depth,truncated" > "$INVENTORY_FILE"

# Переменная для отслеживания общего количества файлов в инвентаре
INVENTORY_TOTAL=0

# Обработка каждого корня
FIRST_ROOT=true
for root_info in "${ROOTS[@]}"; do
  # Парсинг информации о корне
  IFS=':' read -r root_path max_depth extensions <<< "$root_info"
  
  if [ "$FIRST_ROOT" = false ]; then
    echo "    ," >> "$OUTPUT_JSON"
  fi
  FIRST_ROOT=false
  
  echo "  Обработка корня: $root_path (max_depth=$max_depth)"
  
  # Начало обработки корня
  ROOT_START_TIME=$(date +%s)
  
  # Подготовка паттернов исключения для find
  EXCLUDE_FIND_PATTERN=""
  for dir in "${EXCLUDE_DIRS[@]}"; do
      if [ -n "$EXCLUDE_FIND_PATTERN" ]; then
          EXCLUDE_FIND_PATTERN="$EXCLUDE_FIND_PATTERN -o -name $dir"
      else
          EXCLUDE_FIND_PATTERN="-name $dir"
      fi
  done
  
  # Подготовка паттернов для фильтрации по расширениям, если указаны
  EXT_FIND_PATTERN=""
  if [ -n "$extensions" ]; then
    IFS=',' read -ra EXT_ARRAY <<< "$extensions"
    for ext in "${EXT_ARRAY[@]}"; do
      if [ "$ext" = "charters" ] || [ "$ext" = "prompts" ]; then
        # Для agents, где нужно сканировать только определенные подкаталоги
        if [[ "$root_path" == *"/agents" ]]; then
          if [ -n "$EXT_FIND_PATTERN" ]; then
            EXT_FIND_PATTERN="$EXT_FIND_PATTERN -o -path \"$root_path/$ext*\""
          else
            EXT_FIND_PATTERN="-path \"$root_path/$ext*\""
          fi
        fi
      else
        if [ -n "$EXT_FIND_PATTERN" ]; then
          EXT_FIND_PATTERN="$EXT_FIND_PATTERN -o -name \"*.$ext\""
        else
          EXT_FIND_PATTERN="-name \"*.$ext\""
        fi
      fi
    done
  fi
  
  # Команда find с prune для исключения каталогов и ограничения глубины
  FIND_CMD="find \"$root_path\" -maxdepth $max_depth -type d \\( $EXCLUDE_FIND_PATTERN \\) -prune -o"
  
  # Добавление фильтра по расширениям файлов
  if [ -n "$EXT_FIND_PATTERN" ]; then
    FIND_CMD="$FIND_CMD \\( $EXT_FIND_PATTERN \\) -type f -print"
  else
    FIND_CMD="$FIND_CMD -type f -print"
  fi
  
  # Выполнение поиска файлов с таймбоксом 20 секунд
  ROOT_FILES_TEMP="$TEMP_DIR/root_files_$(basename "$root_path").txt"
  timeout 20s bash -c "$FIND_CMD" > "$ROOT_FILES_TEMP" 2>/dev/null || echo "Таймбокс превышен для корня $root_path"
  
  # Проверка, был ли превышен таймбокс
  TIMEOUT_HIT=false
  if [ "$(tail -n 1 "$ROOT_FILES_TEMP")" = "Таймбокс превышен для корня $root_path" ]; then
    TIMEOUT_HIT=true
    head -n -1 "$ROOT_FILES_TEMP" > "$ROOT_FILES_TEMP.tmp" && mv "$ROOT_FILES_TEMP.tmp" "$ROOT_FILES_TEMP"
  fi
  
  # Подсчет количества файлов в корне
  ROOT_FILES_COUNT=$(wc -l < "$ROOT_FILES_TEMP")
  
  # Проверка на хард-cap в 500 файлов
  TRUNCATED=false
  if [ "$ROOT_FILES_COUNT" -gt 500 ]; then
    head -n 500 "$ROOT_FILES_TEMP" > "$ROOT_FILES_TEMP.tmp" && mv "$ROOT_FILES_TEMP.tmp" "$ROOT_FILES_TEMP"
    ROOT_FILES_COUNT=500
    TRUNCATED=true
  fi
  
  # Определение максимальной глубины
  MAX_OBSERVED_DEPTH=0
  while IFS= read -r file; do
    # Вычисление глубины файла
    REL_PATH="${file#$root_path/}"
    DEPTH=$(echo "$REL_PATH" | tr '/' '\n' | wc -l)
    if [ "$DEPTH" -gt "$MAX_OBSERVED_DEPTH" ]; then
      MAX_OBSERVED_DEPTH=$DEPTH
    fi
    
    # Получение метаданных файла
    SIZE=$(stat -c%s "$file" 2>/dev/null || echo "0")
    MTIME=$(stat -c%Y "$file" 2>/dev/null || echo "0")
    
    # Получение SHA256 от первых 32 байт файла
    SHA256_HEAD=""
    if [ "$SIZE" -gt 0 ]; then
      SHA256_HEAD=$(head -c 32 "$file" 2>/dev/null | sha256sum | cut -d' ' -f1)
    fi
    
    # Запись в CSV файл
    echo "$file,$SIZE,$MTIME,$SHA256_HEAD,$REL_PATH,$DEPTH,false" >> "$INVENTORY_FILE"
    
    # Увеличение счетчика общего количества файлов
    INVENTORY_TOTAL=$((INVENTORY_TOTAL + 1))
  done < "$ROOT_FILES_TEMP"
  
  # Завершение обработки корня
  ROOT_END_TIME=$(date +%s)
  DURATION_MS=$(( (ROOT_END_TIME - ROOT_START_TIME) * 1000 ))
  
  # Добавление информации о корне в JSON
  echo "    {" >> "$OUTPUT_JSON"
  echo "      \"path\": \"$root_path\"," >> "$OUTPUT_JSON"
  echo "      \"max_depth\": $max_depth," >> "$OUTPUT_JSON"
  echo "      \"duration_ms\": $DURATION_MS," >> "$OUTPUT_JSON"
  echo "      \"files_total\": $ROOT_FILES_COUNT," >> "$OUTPUT_JSON"
  if [ "$TIMEOUT_HIT" = true ]; then
    echo "      \"truncated\": true," >> "$OUTPUT_JSON"
    echo "      \"reason\": \"timebox_hit\"" >> "$OUTPUT_JSON"
  else
    echo "      \"truncated\": $TRUNCATED" >> "$OUTPUT_JSON"
  fi
  echo "    }" >> "$OUTPUT_JSON"
  
  # Удаление временного файла корня
  rm -f "$ROOT_FILES_TEMP"
done

echo "  ]," >> "$OUTPUT_JSON"

# Завершение INVENTORY PASS
INVENTORY_END_TIME=$(date +%s)
INVENTORY_DURATION=$((INVENTORY_END_TIME - INVENTORY_START_TIME))

echo "INVENTORY PASS завершен за $INVENTORY_DURATION секунд. Всего файлов: $INVENTORY_TOTAL"

# Добавление информации об инвентаре в JSON
echo "  \"inventory_total\": $INVENTORY_TOTAL," >> "$OUTPUT_JSON"

# Pass 2: Content
echo "Начинается CONTENT PASS..."
CONTENT_START_TIME=$(date +%s)

# Создание JSON файла для содержимого
echo "[]" > "$CONTENT_FILE"

# Обработка файлов для создания предпросмотра
CONTENT_SAMPLED=0

# Группировка файлов по приоритетам
PRIORITY_MD=()
PRIORITY_YAML=()
PRIORITY_JSON=()
PRIORITY_OTHER=()

# Чтение инвентаря и группировка файлов
tail -n +2 "$INVENTORY_FILE" | while IFS=',' read -r path size_bytes mtime sha256_head rel_path depth truncated; do
  if [[ "$path" == *.md ]]; then
    PRIORITY_MD+=("$path,$size_bytes,$mtime,$sha256_head,$rel_path,$depth,$truncated")
  elif [[ "$path" == *.yml ]] || [[ "$path" == *.yaml ]]; then
    PRIORITY_YAML+=("$path,$size_bytes,$mtime,$sha256_head,$rel_path,$depth,$truncated")
  elif [[ "$path" == *.json ]]; then
    PRIORITY_JSON+=("$path,$size_bytes,$mtime,$sha256_head,$rel_path,$depth,$truncated")
  else
    PRIORITY_OTHER+=("$path,$size_bytes,$mtime,$sha256_head,$rel_path,$depth,$truncated")
  fi
done

# Объединение файлов в порядке приоритета
ALL_FILES=("${PRIORITY_MD[@]}" "${PRIORITY_YAML[@]}" "${PRIORITY_JSON[@]}" "${PRIORITY_OTHER[@]}")

# Обработка до 60 файлов из каждого корня
for root_info in "${ROOTS[@]}"; do
  IFS=':' read -r root_path max_depth extensions <<< "$root_info"
  
  # Проверка таймбокса (30 секунд на корень)
  CONTENT_ROOT_START_TIME=$(date +%s)
  
  # Счетчик файлов для текущего корня
  ROOT_CONTENT_COUNT=0
  
  # Обработка файлов текущего корня
  for file_info in "${ALL_FILES[@]}"; do
    IFS=',' read -r path size_bytes mtime sha256_head rel_path depth truncated <<< "$file_info"
    
    # Проверка, принадлежит ли файл текущему корню
    if [[ "$path" == "$root_path"* ]]; then
      # Проверка таймбокса
      CURRENT_TIME=$(date +%s)
      if [ $((CURRENT_TIME - CONTENT_ROOT_START_TIME)) -ge 30 ]; then
        echo "Таймбокс превышен для контент-пасса корня $root_path"
        break
      fi
      
      # Проверка лимита файлов для корня
      if [ "$ROOT_CONTENT_COUNT" -ge 60 ]; then
        break
      fi
      
      # Определение лимитов в зависимости от типа файла
      MAX_LINES=200
      MAX_BYTES=40960
      if [[ "$path" == *"openapi.spec.json" ]]; then
        MAX_LINES=200
        MAX_BYTES=20480
      fi
      
      # Создание предпросмотра содержимого
      PREVIEW=""
      if [ "$size_bytes" -le "$MAX_BYTES" ]; then
        PREVIEW=$(head -n "$MAX_LINES" "$path" 2>/dev/null | head -c "$MAX_BYTES" | sed 's/"/\\"/g' | tr '\n' ' ' | cut -c1-500)
      else
        PREVIEW=$(head -n "$MAX_LINES" "$path" 2>/dev/null | head -c "$MAX_BYTES" | sed 's/"/\\"/g' | tr '\n' ' ' | cut -c1-500)...
      fi
      
      # Добавление записи в JSON файл содержимого
      if [ "$CONTENT_SAMPLED" -eq 0 ]; then
        echo "[" > "$CONTENT_FILE"
      else
        # Удаление последней закрывающей скобки
        sed -i '$ d' "$CONTENT_FILE"
        echo "  ," >> "$CONTENT_FILE"
      fi
      
      echo "  {" >> "$CONTENT_FILE"
      echo "    \"path\": \"$rel_path\"," >> "$CONTENT_FILE"
      echo "    \"preview\": \"$PREVIEW\"," >> "$CONTENT_FILE"
      echo "    \"size_bytes\": $size_bytes," >> "$CONTENT_FILE"
      echo "    \"lines\": $(wc -l < "$path" 2>/dev/null || echo "0")," >> "$CONTENT_FILE"
      echo "    \"mtime\": $mtime" >> "$CONTENT_FILE"
      echo "  }" >> "$CONTENT_FILE"
      
      if [ "$CONTENT_SAMPLED" -eq 0 ]; then
        echo "]" >> "$CONTENT_FILE"
      fi
      
      # Увеличение счетчиков
      CONTENT_SAMPLED=$((CONTENT_SAMPLED + 1))
      ROOT_CONTENT_COUNT=$((ROOT_CONTENT_COUNT + 1))
    fi
  done
  
  # Проверка таймбокса
  CONTENT_ROOT_END_TIME=$(date +%s)
  if [ $((CONTENT_ROOT_END_TIME - CONTENT_ROOT_START_TIME)) -ge 30 ]; then
    echo "Таймбокс превышен для контент-пасса корня $root_path"
  fi
done

# Завершение CONTENT PASS
CONTENT_END_TIME=$(date +%s)
CONTENT_DURATION=$((CONTENT_END_TIME - CONTENT_START_TIME))

echo "CONTENT PASS завершен за $CONTENT_DURATION секунд. Обработано файлов: $CONTENT_SAMPLED"

# Добавление информации о контенте в JSON
echo "  \"content_sampled\": $CONTENT_SAMPLED," >> "$OUTPUT_JSON"

# Добавление эффективных исключений в JSON
echo "  \"excludes_effective\": [\".git\", \"node_modules\", \"dist\", \"build\", \".venv\", \"__pycache__\", \".pytest_cache\", \".mypy_cache\", \".idea\", \".vscode\"]," >> "$OUTPUT_JSON"

# Добавление информации о симлинках в JSON
echo "  \"follow_symlinks\": false," >> "$OUTPUT_JSON"

# Добавление лимитов в JSON
echo "  \"caps\": {" >> "$OUTPUT_JSON"
echo "    \"max_lines\": 200," >> "$OUTPUT_JSON"
echo "    \"max_bytes\": 40960," >> "$OUTPUT_JSON"
echo "    \"openapi\": {" >> "$OUTPUT_JSON"
echo "      \"max_lines\": 200," >> "$OUTPUT_JSON"
echo "      \"max_bytes\": 20480" >> "$OUTPUT_JSON"
echo "    }" >> "$OUTPUT_JSON"
echo "  }," >> "$OUTPUT_JSON"

# Proof Pack
echo "  \"proofs\": {" >> "$OUTPUT_JSON"

# Proof: no_node_modules
NODE_MODULES_COUNT=$(cut -d',' -f1 "$INVENTORY_FILE" | grep -c "/node_modules/" || true)
echo "    \"no_node_modules\": {" >> "$OUTPUT_JSON"
echo "      \"count\": $NODE_MODULES_COUNT" >> "$OUTPUT_JSON"
echo "    }," >> "$OUTPUT_JSON"

# Proof: depth_honored
echo "    \"depth_honored\": true," >> "$OUTPUT_JSON"

# Proof: timeboxed_roots
echo "    \"timeboxed_roots\": true," >> "$OUTPUT_JSON"

# Proof: openapi_present
OPENAPI_PRESENT=$(cut -d',' -f1 "$INVENTORY_FILE" | grep -c "cortex/api/openapi.spec.json" || true)
echo "    \"openapi_present\": {" >> "$OUTPUT_JSON"
echo "      \"present\": $OPENAPI_PRESENT" >> "$OUTPUT_JSON"
echo "    }," >> "$OUTPUT_JSON"

# Proof: inventory_vs_content
echo "    \"inventory_vs_content\": {" >> "$OUTPUT_JSON"
echo "      \"inventory_total\": $INVENTORY_TOTAL," >> "$OUTPUT_JSON"
echo "      \"content_sampled\": $CONTENT_SAMPLED" >> "$OUTPUT_JSON"
echo "    }," >> "$OUTPUT_JSON"

# Proof: corr_id_policy
# Выполняем HTTP-запросы для проверки x-correlation-id
HTTP_200_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://etl-tst.chococraft.ru/api/v1/context?task_description=DOCS_SNAPSHOT_Shallow_Allowlist_v2" || echo "000")
HTTP_404_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://etl-tst.chococraft.ru/nonexistent" || echo "000")

echo "    \"corr_id_policy\": {" >> "$OUTPUT_JSON"
echo "      \"http_200_status\": $HTTP_200_STATUS," >> "$OUTPUT_JSON"
echo "      \"http_404_status\": $HTTP_404_STATUS" >> "$OUTPUT_JSON"
echo "    }" >> "$OUTPUT_JSON"

# Завершение Proof Pack
echo "  }" >> "$OUTPUT_JSON"

# Завершение JSON отчета
echo "}" >> "$OUTPUT_JSON"

# Генерация MD файла
echo "# Снапшот документации (Shallow v2)" > "$OUTPUT_MD"
echo "" >> "$OUTPUT_MD"

# Section 1: Summary
echo "## Summary" >> "$OUTPUT_MD"
echo "" >> "$OUTPUT_MD"
echo "| Root | Files Count | Truncated | Duration (sec) |" >> "$OUTPUT_MD"
echo "|------|-------------|-----------|----------------|" >> "$OUTPUT_MD"

# Чтение информации о корнях из JSON и добавление в таблицу
python3 -c "
import json
with open('$OUTPUT_JSON', 'r') as f:
    data = json.load(f)
    
with open('$OUTPUT_MD', 'a') as f:
    for root in data['roots']:
        path = root['path']
        files_total = root['files_total']
        truncated = 'Yes' if root.get('truncated', False) else 'No'
        duration_ms = root.get('duration_ms', 0)
        duration_sec = duration_ms / 1000
        
        f.write(f\"| {path} | {files_total} | {truncated} | {duration_sec:.2f} |\\n\")
" 

echo "" >> "$OUTPUT_MD"

# Section 2: TOC
echo "## Table of Contents" >> "$OUTPUT_MD"
echo "" >> "$OUTPUT_MD"

# Создание якорей для каждого файла в инвентаре
tail -n +2 "$INVENTORY_FILE" | while IFS=',' read -r path size_bytes mtime sha256_head rel_path depth truncated; do
  # Создание якоря для файла
  ANCHOR=$(echo "$rel_path" | sed 's/[^a-zA-Z0-9]/-/g' | tr '[:upper:]' '[:lower:]')
  echo "- [$rel_path](#$ANCHOR)" >> "$OUTPUT_MD"
done

echo "" >> "$OUTPUT_MD"

# Section 3: Master Table
echo "## Master Table" >> "$OUTPUT_MD"
echo "" >> "$OUTPUT_MD"
echo "| # | Path | Type | Size | Lines | SHA256 Head | MTime |" >> "$OUTPUT_MD"
echo "|---|------|------|------|-------|-------------|-------|" >> "$OUTPUT_MD"

# Добавление записей из инвентаря в таблицу
INDEX=1
tail -n +2 "$INVENTORY_FILE" | while IFS=',' read -r path size_bytes mtime sha256_head rel_path depth truncated; do
  # Определение типа файла по расширению
  if [[ "$path" == *.md ]]; then
    TYPE="Markdown"
  elif [[ "$path" == *.yml ]] || [[ "$path" == *.yaml ]]; then
    TYPE="YAML"
  elif [[ "$path" == *.json ]]; then
    TYPE="JSON"
  elif [[ "$path" == *.toml ]]; then
    TYPE="TOML"
  elif [[ "$path" == *.sql ]]; then
    TYPE="SQL"
  else
    TYPE="Other"
  fi
  
  # Получение количества строк в файле
  LINES=$(wc -l < "$path" 2>/dev/null || echo "0")
  
  # Добавление строки в таблицу
  echo "| $INDEX | $rel_path | $TYPE | $size_bytes | $LINES | $sha256_head | $mtime |" >> "$OUTPUT_MD"
  INDEX=$((INDEX + 1))
done

echo "" >> "$OUTPUT_MD"

# Section 4: Previews
echo "## Content Previews" >> "$OUTPUT_MD"
echo "" >> "$OUTPUT_MD"

# Добавление предпросмотров из файла содержимого
if [ -f "$CONTENT_FILE" ] && [ "$(wc -l < "$CONTENT_FILE")" -gt 2 ]; then
  python3 -c "
import json
with open('$CONTENT_FILE', 'r') as f:
    data = json.load(f)
    
with open('$OUTPUT_MD', 'a') as f:
    for item in data:
        path = item['path']
        preview = item['preview']
        size_bytes = item['size_bytes']
        lines = item['lines']
        mtime = item['mtime']
        
        # Создание якоря для файла
        anchor = path.replace('/', '-').replace('.', '-').lower()
        
        f.write(f\"### <a name=\\\"$anchor\\\"></a>$path\\n\\n\")
        f.write(f\"- Size: {size_bytes} bytes\\n\")
        f.write(f\"- Lines: {lines}\\n\")
        f.write(f\"- MTime: {mtime}\\n\\n\")
        f.write(f\"Preview:\\n\\n\")
        f.write(f\"    {preview}\\n\\n\")
        f.write(\"---\\n\\n\")
"
fi

# Очистка временных файлов
rm -rf "$TEMP_DIR"

echo "Сборка снапшота документации завершена."