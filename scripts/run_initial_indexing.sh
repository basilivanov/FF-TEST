#!/bin/bash

set -e

DB_PATH="/opt/feature-factory/data/test.db"
CORTEX_PATH="/opt/feature-factory/cortex/"
DOCS_PATH="/opt/feature-factory/docs/"
CONFIGS_PATH="/opt/feature-factory/configs/"
# В соответствии с Политикой Индексации v3.0 DocSync ограничен каталогами cortex, docs, configs
APP_PATH="/opt/feature-factory/app/"
TESTS_PATH="/opt/feature-factory/tests/"
TMP_PATH="/opt/feature-factory/tmp"
PYAN3_PATH="/opt/feature-factory/.venv/bin/pyan3"
API_BASE_URL="${FF_API_BASE_URL:-http://localhost:8081}"

# JS/TS (UI) paths
UI_SRC_PATH="/opt/feature-factory/app/ui/src"

mkdir -p "$TMP_PATH"

# Clean up previous run artifacts
rm -f $TMP_PATH/tags.json
rm -f $TMP_PATH/py_files.txt
rm -f $TMP_PATH/doc_files.txt

# 1. Очистка таблиц
echo "Очистка целевых таблиц..."
sqlite3 $DB_PATH "DELETE FROM doc_registry;"
sqlite3 $DB_PATH "DELETE FROM code_registry;"
sqlite3 $DB_PATH "DELETE FROM symbol_index;"
sqlite3 $DB_PATH "DELETE FROM call_graph_edges;"
echo "Таблицы очищены."

# 2. Индексация текстовых знаний (DocSync: только cortex, docs, configs; типы: .md, .yaml, .conf)
echo "Индексация текстовых знаний..."
find $CORTEX_PATH $DOCS_PATH $CONFIGS_PATH \
    -path '*/.venv' -prune -o \
    -path '*/node_modules' -prune -o \
    -path '*/__pycache__' -prune -o \
    -path '*/tmp' -prune -o \
    -path '*/reports' -prune -o \
    -path '*/.git' -prune -o \
    \( -name "*.md" -o -name "*.yaml" -o -name "*.conf" \) -print > $TMP_PATH/doc_files.txt

python3 <<END
import os
import hashlib
import sqlite3
from datetime import datetime

conn = sqlite3.connect("$DB_PATH")
cursor = conn.cursor()

with open("$TMP_PATH/doc_files.txt", "r") as f:
    for file_path in f:
        file_path = file_path.strip()
        if os.path.isfile(file_path):
            doc_name = os.path.basename(file_path)
            with open(file_path, "rb") as f_doc:
                content_hash = hashlib.sha256(f_doc.read()).hexdigest()
            cursor.execute("INSERT INTO doc_registry (doc_name, version, content_hash, updated_at) VALUES (?, ?, ?, ?)",
                           (doc_name, '1.0', content_hash, datetime.now()))

conn.commit()
conn.close()
END
echo "Текстовые знания проиндексированы."

# 3. Индексация кода (диспетчер)
echo "Определение присутствующих языков..."

# Собираем списки файлов
echo "Сбор списка Python файлов..."
find $APP_PATH $TESTS_PATH \
    -path '*/.venv' -prune -o \
    -path '*/node_modules*' -prune -o \
    -path '*/__pycache__' -prune -o \
    -path '*/tmp' -prune -o \
    -path '*/reports' -prune -o \
    -path '*/.git' -prune -o \
    -name "*.py" -print > $TMP_PATH/py_files.txt

echo "Сбор списка TS/TSX файлов..."
find $UI_SRC_PATH \
    -path '*/node_modules' -prune -o \
    -path '*/dist' -prune -o \
    -path '*/build' -prune -o \
    -name "*.ts" -o -name "*.tsx" -print 2>/dev/null | sed '/^$/d' > $TMP_PATH/js_files.txt || true

HAS_PY=false; [ -s "$TMP_PATH/py_files.txt" ] && HAS_PY=true
HAS_JS=false; [ -s "$TMP_PATH/js_files.txt" ] && HAS_JS=true

echo "HAS_PY=$HAS_PY, HAS_JS=$HAS_JS"

echo "Генерация ctags для всех доступных языков..."
{
  cat "$TMP_PATH/py_files.txt" 2>/dev/null || true
  cat "$TMP_PATH/js_files.txt" 2>/dev/null || true
} | sed '/^$/d' > "$TMP_PATH/code_files.txt"

if [ -s "$TMP_PATH/code_files.txt" ]; then
  ctags --fields=+n-f+K-l-m-s-z --languages=Python,TypeScript --output-format=json -o "$TMP_PATH/tags.json" -L "$TMP_PATH/code_files.txt"
else
  echo "Нет файлов кода для ctags" >&2
  : > "$TMP_PATH/tags.json"
fi

# Python: pyan3 для графа вызовов
if [ "$HAS_PY" = true ]; then
  echo "Генерация графа вызовов Python через pyan3..."
  if [ -f "$PYAN3_PATH" ]; then
    touch "$TMP_PATH/pyan.dot"
    while IFS= read -r file; do
      "$PYAN3_PATH" "$file" --uses --no-defines --annotated >> "$TMP_PATH/pyan.dot" 2>/dev/null || true
    done < "$TMP_PATH/py_files.txt"
  else
    echo "pyan3 не найден по пути $PYAN3_PATH, пропускаю генерацию графа Python" >&2
    touch "$TMP_PATH/pyan.dot"
  fi
else
  echo "Python файлы не найдены, пропускаю pyan3"
  touch "$TMP_PATH/pyan.dot"
fi

# JS/TS: dependency-cruiser через npx для зависимостей модулей
if [ "$HAS_JS" = true ]; then
  echo "Генерация графа зависимостей JS/TS через dependency-cruiser..."
  DEPCRUISE_JSON="$TMP_PATH/depcruise.json"
  # Пытаемся использовать локальный конфиг tsconfig/json, если есть
  TS_CONFIG=""
  if [ -f "/opt/feature-factory/app/ui/tsconfig.json" ]; then
    TS_CONFIG="--ts-config /opt/feature-factory/app/ui/tsconfig.json"
  elif [ -f "/opt/feature-factory/app/ui/tsconfig.app.json" ]; then
    TS_CONFIG="--ts-config /opt/feature-factory/app/ui/tsconfig.app.json"
  fi
  set +e
  # Пытаемся сначала с конфигом (.dependency-cruiser.cjs), при неуспехе фолбэк на --no-config
  (
    cd /opt/feature-factory/app/ui && \
    npx --yes dependency-cruiser --output-type json src
  ) > "$DEPCRUISE_JSON" 2> "$TMP_PATH/depcruise.err"
  STATUS=$?
  if [ $STATUS -ne 0 ] || [ ! -s "$DEPCRUISE_JSON" ]; then
    (
      cd /opt/feature-factory/app/ui && \
      npx --yes dependency-cruiser --no-config $TS_CONFIG --include-only "^src" --output-type json src
    ) > "$DEPCRUISE_JSON" 2>> "$TMP_PATH/depcruise.err"
    STATUS=$?
  fi
  set -e
  if [ $STATUS -ne 0 ] || [ ! -s "$DEPCRUISE_JSON" ]; then
    echo "Предупреждение: dependency-cruiser вернул код $STATUS или пустой вывод. См. $TMP_PATH/depcruise.err" >&2
  fi
else
  echo "JS/TS файлы не найдены, пропускаю dependency-cruiser"
  : > "$TMP_PATH/depcruise.json"
fi

echo "Код проиндексирован."

# 4. Загрузка в БД
echo "Загрузка данных в БД..."
python3 <<END
import os
import json
import sqlite3
import re
import hashlib
from datetime import datetime

conn = sqlite3.connect("$DB_PATH")
cursor = conn.cursor()

# Загрузка code_registry и symbol_index из ctags (языконезависимо)
tags_path = "$TMP_PATH/tags.json"
if os.path.exists(tags_path) and os.path.getsize(tags_path) > 0:
    with open(tags_path, "r") as f:
        for line in f:
            try:
                tag = json.loads(line)
                if tag.get("_type") == "tag":
                    file_path = tag.get("path")
                    if not file_path or not os.path.isfile(file_path):
                        continue
                    with open(file_path, "rb") as f_code:
                        sha256 = hashlib.sha256(f_code.read()).hexdigest()
                    cursor.execute(
                        "INSERT OR IGNORE INTO code_registry (file_path, sha256, indexed_at) VALUES (?, ?, ?)",
                        (file_path, sha256, datetime.now()),
                    )
                    cursor.execute(
                        "INSERT INTO symbol_index (file_path, symbol_name, symbol_type, line_start, line_end) VALUES (?, ?, ?, ?, ?)",
                        (
                            file_path,
                            tag.get("name", "<unknown>"),
                            tag.get("kind", "N/A"),
                            int(tag.get("line", 0) or 0),
                            int(tag.get("line", 0) or 0),
                        ),
                    )
            except (json.JSONDecodeError, FileNotFoundError, OSError):
                pass

# Загрузка call_graph_edges из pyan
if os.path.exists("$TMP_PATH/pyan.dot"):
    with open("$TMP_PATH/pyan.dot", "r") as f:
        for line in f:
            try:
                match = re.match(r'\s*"(.+)" -> "(.+)".*', line)
                if match:
                    caller = match.group(1)
                    callee = match.group(2)
                    # This is a simplification, as pyan does not provide file path and line number for the edge
                    cursor.execute(
                        "INSERT INTO call_graph_edges (source_symbol, target_symbol, file_path, line_number) VALUES (?, ?, ?, ?)",
                        (caller, callee, 'N/A', 0),
                    )
            except re.error:
                pass

"""
Попытка загрузить граф зависимостей JS/TS из dependency-cruiser. Если файл пустой
или инструмент недоступен, задействуем фолбэк: парсим import/require/export в .ts/.tsx
и создаём рёбра модульных зависимостей (source -> target).
"""
depcruise_path = "$TMP_PATH/depcruise.json"
inserted_js_edges = 0
if os.path.exists(depcruise_path) and os.path.getsize(depcruise_path) > 0:
    try:
        with open(depcruise_path, "r") as f:
            data = json.load(f)
            modules = data.get("modules") or []
            for mod in modules:
                source = mod.get("source")
                if not source or not (source.endswith(".ts") or source.endswith(".tsx")):
                    continue
                deps = mod.get("dependencies") or []
                for d in deps:
                    target = d.get("resolved") or d.get("module") or d.get("dependency")
                    if not target:
                        continue
                    cursor.execute(
                        "INSERT INTO call_graph_edges (source_symbol, target_symbol, file_path, line_number) VALUES (?, ?, ?, ?)",
                        (source, target, source, 0),
                    )
                    inserted_js_edges += 1
    except Exception:
        pass

if inserted_js_edges == 0:
    import re, os
    from pathlib import Path
    imports_re = re.compile(r"(?:import\s+[^'\"]*from\s*['\"]([^'\"]+)['\"]|import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)|require\(\s*['\"]([^'\"]+)['\"]\s*\)|export\s+[^'\"]*from\s*['\"]([^'\"]+)['\"])")
    def resolve_ts(from_file: Path, spec: str) -> str:
        if not spec.startswith(".") and not spec.startswith("/"):
            return spec
        base = (from_file.parent / spec).resolve()
        candidates = [
            base.with_suffix(".ts"),
            base.with_suffix(".tsx"),
            base / "index.ts",
            base / "index.tsx",
        ]
        for c in candidates:
            if c.exists():
                return str(c)
        return str(base)

    js_list = "$TMP_PATH/js_files.txt"
    if os.path.exists(js_list):
        with open(js_list, "r") as fl:
            for line in fl:
                src = line.strip()
                if not src or not (src.endswith(".ts") or src.endswith(".tsx")):
                    continue
                try:
                    with open(src, "r", encoding="utf-8", errors="ignore") as sf:
                        content = sf.read()
                    for m in imports_re.finditer(content):
                        spec = next((g for g in m.groups() if g), None)
                        if not spec:
                            continue
                        target = resolve_ts(Path(src), spec)
                        cursor.execute(
                            "INSERT INTO call_graph_edges (source_symbol, target_symbol, file_path, line_number) VALUES (?, ?, ?, ?)",
                            (src, target, src, 0),
                        )
                        inserted_js_edges += 1
                except Exception:
                    pass

# Гарантируем добавление всех файлов кода в code_registry, даже если ctags не создал тегов
code_list = "$TMP_PATH/code_files.txt"
if os.path.exists(code_list):
    with open(code_list, "r") as fcl:
        for fp in fcl:
            fp = fp.strip()
            if not fp or not os.path.isfile(fp):
                continue
            try:
                with open(fp, "rb") as fc:
                    sha = hashlib.sha256(fc.read()).hexdigest()
                cursor.execute(
                    "INSERT OR IGNORE INTO code_registry (file_path, sha256, indexed_at) VALUES (?, ?, ?)",
                    (fp, sha, datetime.now()),
                )
            except Exception:
                pass

conn.commit()
conn.close()
END
echo "Данные загружены в БД."

echo "Индексация завершена."

echo "Генерация спецификации OpenAPI..."
curl -sS "$API_BASE_URL/openapi.json" > /opt/feature-factory/cortex/api/openapi.spec.json
echo "Спецификация OpenAPI сгенерирована."
