#!/bin/bash
# test_api.sh - Скрипт для тестирования API оркестратора через curl

set -e

# Параметры
API_BASE_URL="http://localhost:8000/api/v1/orchestrator"
CORRELATION_ID="test-correlation-$(date +%s)"

echo "Testing Orchestrator API..."
echo "Base URL: $API_BASE_URL"
echo "Correlation ID: $CORRELATION_ID"
echo ""

# 1. Тест создания фичи (POST /features)
echo "1. Testing POST /features"
FEATURE_RESPONSE=$(curl -s -X POST "$API_BASE_URL/features" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: $CORRELATION_ID" \
  -d '{
    "title": "Test Feature",
    "intent_json": "{\"intent\": \"test feature\"}",
    "priority": 1,
    "created_by": "test_user",
    "env": "TEST"
  }')

echo "Response:"
echo "$FEATURE_RESPONSE" | jq '.' 2>/dev/null || echo "$FEATURE_RESPONSE"
echo ""

# Извлекаем ID фичи из ответа (если удалось создать)
FEATURE_ID=$(echo "$FEATURE_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$FEATURE_ID" ]; then
  echo "Created feature with ID: $FEATURE_ID"
  
  # 2. Тест генерации плана (POST /features/{id}/plan)
  echo "2. Testing POST /features/$FEATURE_ID/plan"
  PLAN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/features/$FEATURE_ID/plan" \
    -H "Content-Type: application/json" \
    -H "X-Correlation-ID: $CORRELATION_ID")
  
  echo "Response:"
  echo "$PLAN_RESPONSE" | jq '.' 2>/dev/null || echo "$PLAN_RESPONSE"
  echo ""
  
  # 3. Тест запуска фичи (POST /features/{id}/run)
  echo "3. Testing POST /features/$FEATURE_ID/run"
  RUN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/features/$FEATURE_ID/run" \
    -H "Content-Type: application/json" \
    -H "X-Correlation-ID: $CORRELATION_ID")
  
  echo "Response:"
  echo "$RUN_RESPONSE" | jq '.' 2>/dev/null || echo "$RUN_RESPONSE"
  echo ""
else
  echo "Skipping plan and run tests - feature creation failed"
fi

# 4. Тест получения статуса графа (GET /graph/{run_id}/status)
# Для теста используем фиктивный run_id
echo "4. Testing GET /graph/test-run-id/status"
STATUS_RESPONSE=$(curl -s -X GET "$API_BASE_URL/graph/test-run-id/status" \
  -H "X-Correlation-ID: $CORRELATION_ID")

echo "Response:"
echo "$STATUS_RESPONSE" | jq '.' 2>/dev/null || echo "$STATUS_RESPONSE"
echo ""

echo "API testing completed."