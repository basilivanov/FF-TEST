set -euo pipefail
export HOME=/opt/feature-factory
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# LTS как default
nvm install --lts >/dev/null
nvm alias default lts/* >/dev/null
nvm use default >/dev/null

echo "== npm view (latest) =="
for pkg in @google/gemini-cli @openai/codex @qwen-code/qwen-code @anthropic-ai/claude-code; do
  ver=$(npm view "$pkg" version 2>/dev/null || echo unknown)
  printf "%-28s -> %s\n" "$pkg" "$ver"
done

# Переустановка строго @latest
npm -g remove @google/gemini-cli @openai/codex codex-cli @qwen-code/qwen-code @anthropic-ai/claude-code >/dev/null 2>&1 || true
npm -g install @google/gemini-cli@latest @openai/codex@latest @qwen-code/qwen-code@latest @anthropic-ai/claude-code@latest

BIN=$(npm bin -g)
echo
echo "node: $(node -v)"
echo "npm:  $(npm -v)"
echo "BIN:  $BIN"
echo
echo "== binary --version =="
for c in gemini codex qwen qwen-code claude claude-code; do
  T="$BIN/$c"
  if [ -x "$T" ]; then
    printf "%-12s -> %s\n" "$c" "$T"
    "$T" --version 2>/dev/null || "$T" -v 2>/dev/null || true
  else
    printf "%-12s -> not found\n" "$c"
  fi
done
