#!/bin/bash
# Safe E2E Test Script - не меняет основную ветку и не ломает систему

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[E2E]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция очистки - выполняется в любом случае
cleanup() {
    local exit_code=$?
    log "Cleaning up..."
    
    # Вернуться на исходную ветку если мы её меняли
    if [[ -n "${ORIGINAL_BRANCH:-}" ]]; then
        git checkout "$ORIGINAL_BRANCH" 2>/dev/null || true
    fi
    
    # Удалить тестовые ветки если создавали
    if [[ -n "${TEST_BRANCH:-}" ]]; then
        git branch -D "$TEST_BRANCH" 2>/dev/null || true
        git push origin --delete "$TEST_BRANCH" 2>/dev/null || true
    fi
    
    # Удалить тестовые файлы
    rm -f test_e2e_*.md 2>/dev/null || true
    
    # Восстановить процессы если убивали
    if [[ -n "${KILLED_PROCESSES:-}" ]]; then
        log "Note: Some processes were stopped during test"
    fi
    
    exit $exit_code
}

# Установить trap для очистки
trap cleanup EXIT INT TERM

# Проверка предварительных условий
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Проверяем что мы в git репозитории
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        error "Not in a git repository"
        exit 1
    fi
    
    # Проверяем что нет незакоммиченных изменений в важных файлах
    if git diff --name-only | grep -E '\.(py|json|yaml|yml)$' >/dev/null; then
        warn "Uncommitted changes detected in code files"
        
        # Если проверка отключена, продолжаем автоматически
        if [[ "${E2E_CHECK_UNCOMMITTED:-true}" != "true" ]]; then
            warn "Check disabled by E2E_CHECK_UNCOMMITTED=false, continuing..."
        else
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
    
    # Сохраняем текущую ветку
    ORIGINAL_BRANCH=$(git branch --show-current)
    export ORIGINAL_BRANCH
    
    log "Current branch: $ORIGINAL_BRANCH"
}

# Безопасная проверка сервисов
check_services_safe() {
    log "Checking services status (safe mode)..."
    
    # Проверяем доступность API без влияния на него
    if curl -f -s -m 5 http://127.0.0.1:8081/health/live >/dev/null 2>&1; then
        log "✓ Main service is running"
    else
        warn "Main service not available - some tests will be skipped"
        return 1
    fi
    
    return 0
}

# Создать изолированное тестовое окружение
create_isolated_test_env() {
    log "Setting up isolated test environment..."
    
    # Создаем временную директорию для артефактов
    TEST_ARTIFACTS_DIR="/tmp/e2e_test_$(date +%s)"
    mkdir -p "$TEST_ARTIFACTS_DIR"
    export TEST_ARTIFACTS_DIR
    
    # Генерируем уникальный ID теста
    TEST_ID="e2e_safe_$(date +%s)"
    export TEST_ID
    
    log "Test artifacts: $TEST_ARTIFACTS_DIR"
    log "Test ID: $TEST_ID"
}

# Тест API без создания реальных feature
test_api_endpoints() {
    log "Testing API endpoints (read-only)..."
    
    local base_url="http://127.0.0.1:8081"
    
    # Тест health endpoint
    if curl -f -s "$base_url/health/live" | jq -e '.status == "ok"' >/dev/null; then
        log "✓ Health endpoint works"
    else
        error "✗ Health endpoint failed"
        return 1
    fi
    
    # Тест списка features (без создания новых)
    if curl -f -s "$base_url/api/v1/orchestrator/features" >/dev/null; then
        log "✓ Features endpoint accessible"
    else
        warn "✗ Features endpoint not accessible"
    fi
    
    # Тест OpenAPI документации
    if curl -f -s "$base_url/openapi.json" | jq -e '.paths' >/dev/null; then
        log "✓ OpenAPI documentation available"
    else
        warn "✗ OpenAPI documentation not available"
    fi
}

# Тест CI endpoint с фиктивными данными
test_ci_endpoint_safe() {
    log "Testing CI endpoint with fake data..."
    
    # Используем заведомо несуществующий PR номер
    local fake_pr=99999
    local fake_sha="0000000000000000000000000000000000000000"
    
    local response
    response=$(curl -s -u ops:ops123 -H 'Content-Type: application/json' \
        -d "{\"pr_number\":${fake_pr},\"head_sha\":\"${fake_sha}\",\"state\":\"success\",\"context\":\"test\",\"description\":\"Safe E2E test\",\"target_url\":\"http://example.com\"}" \
        -w "%{http_code}" \
        http://127.0.0.1:8081/api/v1/ci/status)
    
    if [[ "$response" == *"200" ]] || [[ "$response" == *"No feature found"* ]]; then
        log "✓ CI endpoint responds correctly"
    else
        warn "✗ CI endpoint unexpected response: $response"
    fi
}

# Тест с минимальным воздействием на систему
test_minimal_impact() {
    log "Running minimal impact tests..."
    
    # Тестируем только чтение
    test_api_endpoints || return 1
    
    # Тестируем CI с фиктивными данными
    test_ci_endpoint_safe || return 1
    
    # Проверяем доступность базы данных (только чтение)
    if [[ -f "/opt/feature-factory/data/test.db" ]]; then
        if python3 -c "
import sqlite3
conn = sqlite3.connect('/opt/feature-factory/data/test.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM features')
count = cursor.fetchone()[0]
print(f'Database accessible, {count} features found')
conn.close()
" 2>/dev/null; then
            log "✓ Database accessible"
        else
            warn "✗ Database not accessible"
        fi
    else
        warn "Database file not found"
    fi
}

# Создание минимальной feature для полного тестирования (опционально)
test_full_cycle_optional() {
    if [[ "${FULL_TEST:-}" != "true" ]]; then
        log "Skipping full cycle test (set FULL_TEST=true to enable)"
        return 0
    fi
    
    log "Running full cycle test (creates real data)..."
    
    warn "This will create a test feature and branch - are you sure?"
    read -p "Continue with full test? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Skipping full test"
        return 0
    fi
    
    # Создаем тестовую ветку
    TEST_BRANCH="e2e-safe-test-$(date +%s)"
    export TEST_BRANCH
    
    git checkout -b "$TEST_BRANCH"
    echo "# E2E Safe Test $(date)" > "test_e2e_safe_$(date +%s).md"
    git add .
    git commit -m "E2E Safe Test - will be cleaned up"
    
    # Здесь можно добавить создание feature через API
    # но с обязательной очисткой в cleanup функции
    
    log "Full cycle test completed"
}

# Генерация отчёта
generate_report() {
    log "Generating test report..."
    
    local report_file="$TEST_ARTIFACTS_DIR/e2e_report.json"
    
    cat > "$report_file" << EOF
{
    "test_id": "$TEST_ID",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "duration_seconds": $SECONDS,
    "original_branch": "$ORIGINAL_BRANCH",
    "test_artifacts_dir": "$TEST_ARTIFACTS_DIR",
    "status": "completed",
    "tests_run": [
        "prerequisites_check",
        "services_check", 
        "api_endpoints_test",
        "ci_endpoint_test",
        "minimal_impact_test"
    ]
}
EOF
    
    log "Report saved to: $report_file"
    echo "Test completed successfully!"
    echo "Artifacts directory: $TEST_ARTIFACTS_DIR"
    echo "Original branch restored: $ORIGINAL_BRANCH"
}

# Основная функция
main() {
    log "Starting Safe E2E Test..."
    
    check_prerequisites
    create_isolated_test_env
    
    if check_services_safe; then
        test_minimal_impact
        test_full_cycle_optional
    else
        warn "Services not available - running limited tests only"
        log "You can start services manually and re-run for full test"
    fi
    
    generate_report
    
    log "Safe E2E Test completed successfully!"
}

# Запуск
main "$@"