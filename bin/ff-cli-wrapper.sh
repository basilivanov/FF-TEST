#!/bin/bash
# Универсальная обертка для запуска CLI в полном login-окружении
set -euo pipefail

# Путь к реальному исполняемому файлу передается первым аргументом
REAL_BINARY_PATH="${1:-}"
if [[ -z "$REAL_BINARY_PATH" ]]; then
  echo "[ff-cli-wrapper] REAL_BINARY_PATH is required as the first argument" >&2
  exit 2
fi
shift # Убираем первый аргумент, чтобы "$@" содержал только аргументы для бинарника

# Запускаем команду в login-сессии от пользователя 'feature'
# 'bash -lc' гарантирует, что будут подгружены ~/.bashrc и ~/.profile
# 'exec' заменяет процесс обертки на процесс бинарника
env HOME=/home/feature bash -lc "exec \"$REAL_BINARY_PATH\" \"\$@\"" -- "$@"

