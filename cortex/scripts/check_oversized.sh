#!/usr/bin/env bash
set -euo pipefail
echo "[docs-guard] Checking oversized files (cortex only)..."
oversized=$(find cortex -type f -size +1024k 2>/dev/null | wc -l || echo 0)
if [ "$oversized" -gt 0 ]; then
  echo "Found $oversized oversized files" >&2
  exit 1
fi
echo "[docs-guard] PASS"
exit 0

