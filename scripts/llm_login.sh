#!/usr/bin/env bash
set -euo pipefail

# One‑time login helper for CLI providers, to be run as user `feature`.
# Usage:
#   ./scripts/llm_login.sh
#
# Env you may want to export beforehand (example):
#   export GOOGLE_CLOUD_PROJECT=etl-marketplace

echo "[i] Starting interactive login for CLI providers (qwen/gemini/claude/codex)."
echo "[i] This runs as: $(id -un)"

echo "\n=== Qwen ==="
echo "[i] If Qwen CLI supports login, it will prompt a URL/code."
echo "[i] Accept EULA automatically with -y if supported."
{ qwen login -y || qwen auth login -y || true; }

echo "\n=== Gemini ==="
echo "[i] GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-<unset>}"
echo "[i] Gemini may open a URL for OAuth — follow the instructions."
{ gemini login -y || gemini auth login -y || true; }

echo "\n=== Claude ==="
echo "[i] Will skip permissions prompts for sandboxed envs."
{ claude login --dangerously-skip-permissions || true; }

echo "\n=== Codex ==="
echo "[i] Codex may require browser approval as well."
{ codex login --dangerously-bypass-approvals-and-sandbox || true; }

echo "\n=== Smoke versions ==="
for b in qwen gemini claude codex openai; do
  if command -v "$b" >/dev/null 2>&1; then
    echo -n "[$b] "; "$b" --version 2>/dev/null || echo "(no --version)"
  fi
done

echo "\n[ok] Login attempts completed. If you saw a URL, ensure you followed it in the browser."

