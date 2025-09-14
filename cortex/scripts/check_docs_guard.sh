#!/usr/bin/env bash
set -euo pipefail
echo "[docs-guard] Checking docs guard (cortex only)..."
test -d cortex
echo "[docs-guard] PASS"
exit 0

