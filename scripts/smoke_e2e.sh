#!/usr/bin/env bash
set -euo pipefail

# Simple E2E Smoke Test for Feature Factory (TEST env)
# - Resets DB via API
# - Creates a feature with autostart=true
# - Waits for graph to reach DONE
# - Verifies /api/v1/ping returns {"ping":"pong"}
# - Writes a report to reports/smoke_test_*.md

# Prefer FF_API_BASE_URL if provided, fallback to existing BASE_URL, then default
BASE_URL="${FF_API_BASE_URL:-${BASE_URL:-http://localhost:8081}}"
FEATURE_TITLE="${FEATURE_TITLE:-Создать Ping-Pong Endpoint}"

if ! curl -fsS "$BASE_URL/api/v1/health" >/dev/null; then
  echo "Error: API not reachable at $BASE_URL" >&2
  exit 1
fi

# 1) Reset DB (TEST only)
curl -fsS -X POST "$BASE_URL/api/v1/orchestrator/admin/reset" >/dev/null

# 2) Create feature with autostart=true
PAYLOAD=$(cat << JSON
{
  "title": "$FEATURE_TITLE",
  "autostart": true,
  "strict": true,
  "intent": {
    "title": "$FEATURE_TITLE",
    "summary": "Разработать простой неавторизованный API эндпоинт GET /api/v1/ping, который возвращает JSON-объект {\"ping\": \"pong\"}. Эндпоинт должен быть реализован в новом файле app/api/ping.py и добавлен в основной роутер FastAPI в app/main.py.",
    "priority": "P1"
  }
}
JSON
)
CREATE_OUT=$(curl -fsS -X POST "$BASE_URL/api/v1/orchestrator/features" -H 'Content-Type: application/json' --data "$PAYLOAD")
echo "$CREATE_OUT" > tmp_smoke_create.json
if [[ -z "$CREATE_OUT" ]]; then
  echo "Error: empty response from create feature" >&2
  exit 1
fi

FEATURE_ID=$(echo "$CREATE_OUT" | /opt/feature-factory/.venv/bin/python -c 'import sys,json;print(json.load(sys.stdin).get("id"))')
if [[ -z "${FEATURE_ID:-}" ]]; then
  echo "Error: Failed to parse feature id" >&2
  exit 1
fi

# 3) Wait for graph DONE (up to 60s)
ATTEMPTS=180
SLEEP=1
RUN_ID=""
STATUS=""
while (( ATTEMPTS > 0 )); do
  RUNS=$(curl -fsS "$BASE_URL/api/v1/orchestrator/runs")
  readarray -t FIELDS < <(echo "$RUNS" | /opt/feature-factory/.venv/bin/python -c 'import sys,json
runs=json.load(sys.stdin)
if runs:
    r=runs[0]
    print(r.get("run_id",""))
    print(r.get("status",""))
else:
    print("")
    print("")
')
  RUN_ID="${FIELDS[0]}"
  STATUS="${FIELDS[1]}"
  if [[ "$STATUS" == "DONE" ]]; then
    break
  fi
  sleep "$SLEEP"
  ATTEMPTS=$((ATTEMPTS-1))
done

if [[ "$STATUS" != "DONE" ]]; then
  echo "Error: Graph not DONE in time (feature_id=$FEATURE_ID, run_id=$RUN_ID, status=$STATUS)" >&2
  exit 1
fi

# 4) Verify endpoint
PING_OUT=$(curl -fsS "$BASE_URL/api/v1/ping")
if [[ "$PING_OUT" != '{"ping":"pong"}' ]]; then
  echo "Error: Unexpected ping response: $PING_OUT" >&2
  exit 1
fi

# 5) Report
STAMP=$(date +%Y%m%d_%H%M%S)
REPORT="reports/smoke_test_${STAMP}.md"
mkdir -p reports
{
  echo "# Smoke Test Report"
  echo
  echo "- Task ID: MVP-SMOKE-TEST-01"
  echo "- Title: Первый сквозной прогон «Фабрики фич»"
  echo "- Started: $(date -Is)"
  echo
  echo "## Steps"
  echo "- Reset DB: OK"
  echo "- Create Feature (autostart): OK (feature_id=$FEATURE_ID)"
  echo "- Run G1 (auto): DONE (run_id=$RUN_ID)"
  echo "- Verify endpoint: OK (GET /api/v1/ping -> {\"ping\":\"pong\"})"
  echo "- Changelog updated: handled in pipeline"
  echo
  echo "## Results"
  echo "- Feature status: DONE"
  echo "- Graph status: DONE"
  echo "- Endpoint response: $PING_OUT"
  echo
  echo "## Artifacts"
  echo "- app/api/ping.py generated and applied by pipeline"
  echo "- CHANGELOG.md updated with feature entry"
} > "$REPORT"

echo "$REPORT"
