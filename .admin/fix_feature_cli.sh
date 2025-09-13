set -euo pipefail

# Загружаем nvm и выставляем LTS по умолчанию
export HOME=/opt/feature-factory
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

nvm install --lts >/dev/null
nvm alias default lts/* >/dev/null
nvm use default >/dev/null

# 1) Почистить конфликтные ключи в userconfig (~/.npmrc)
UC="$(npm config get userconfig 2>/dev/null || echo "$HOME/.npmrc")"
[ -f "$UC" ] && sed -i.bak -E '/^[[:space:]]*(prefix|globalconfig)[[:space:]]*=.*/d' "$UC" || true
[ -f "$HOME/.npmrc" ] && sed -i.bak -E '/^[[:space:]]*(prefix|globalconfig)[[:space:]]*=.*/d' "$HOME/.npmrc" || true

# 2) Сброс возможных ENV-переопределений
unset NPM_CONFIG_PREFIX npm_config_prefix npm_config_globalconfig PREFIX || true
npm config delete prefix       >/dev/null 2>&1 || true
npm config delete globalconfig >/dev/null 2>&1 || true

# 3) Немного тишины (без вмешательства в prefix)
grep -q '^fund=false' "$HOME/.npmrc" 2>/dev/null || echo fund=false >>"$HOME/.npmrc"
grep -q '^update-notifier=false' "$HOME/.npmrc" 2>/dev/null || echo update-notifier=false >>"$HOME/.npmrc"

# 4) Попросить nvm забыть старый префикс, если был
nvm use --delete-prefix default --silent || true

# 5) Переустановка CLI (latest)
npm -g remove @google/gemini-cli @openai/codex codex-cli @qwen-code/qwen-code @anthropic-ai/claude-code >/dev/null 2>&1 || true
npm -g install @google/gemini-cli@latest @openai/codex@latest @qwen-code/qwen-code@latest @anthropic-ai/claude-code@latest

# 6) Печать чистой диагностики - реальные бинарники из npm bin -g
BIN="$(npm bin -g)"
echo "node: $(node -v)"
echo "npm:  $(npm -v)"
echo "BIN:  $BIN"

for c in gemini codex qwen qwen-code claude claude-code; do
  T="$BIN/$c"
  if [ -x "$T" ]; then
    printf "%-12s -> %s\n" "$c" "$T"
    "$T" --version 2>/dev/null || "$T" -v 2>/dev/null || true
  else
    printf "%-12s -> not found\n" "$c"
  fi
done
