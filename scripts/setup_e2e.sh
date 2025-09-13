#!/bin/bash
# Setup E2E Testing Environment
# Устанавливает и настраивает всё необходимое для безопасного E2E тестирования

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[SETUP]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка и установка зависимостей
install_dependencies() {
    log "Installing missing Python dependencies..."
    
    cd "$PROJECT_ROOT"
    
    # Список необходимых пакетов
    REQUIRED_PACKAGES=(
        "PyYAML"
        "tiktoken" 
        "jsonschema"
        "sqladmin"
        "langgraph"
        "requests"
    )
    
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if ! .venv/bin/python -c "import ${package,,}" 2>/dev/null; then
            log "Installing $package..."
            .venv/bin/pip install "$package"
        else
            log "✓ $package already installed"
        fi
    done
}

# Исправление схемы базы данных
fix_database_schema() {
    log "Fixing database schema..."
    
    if [[ -f "/opt/feature-factory/data/test.db" ]]; then
        .venv/bin/python -c "
import sqlite3
conn = sqlite3.connect('/opt/feature-factory/data/test.db')
cursor = conn.cursor()

# Проверяем есть ли колонка intent_json
cursor.execute('PRAGMA table_info(features)')
columns = [row[1] for row in cursor.fetchall()]

if 'intent_json' not in columns:
    print('Adding intent_json column...')
    cursor.execute('ALTER TABLE features ADD COLUMN intent_json TEXT')
    conn.commit()
    print('✓ Added intent_json column')
else:
    print('✓ intent_json column already exists')

conn.close()
"
    else
        warn "Database not found - will be created on first run"
    fi
}

# Создание директорий
setup_directories() {
    log "Setting up directories..."
    
    # Создаём необходимые директории
    mkdir -p "$PROJECT_ROOT"/{scripts,data,artifacts,logs}
    
    # Создаём директорию для temporary E2E артефактов
    mkdir -p /tmp/e2e_artifacts
    
    log "✓ Directories created"
}

# Проверка Git конфигурации
check_git_config() {
    log "Checking Git configuration..."
    
    cd "$PROJECT_ROOT"
    
    # Проверяем что мы в git репозитории
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        error "Not in a Git repository"
        return 1
    fi
    
    # Проверяем remote
    if ! git remote get-url origin >/dev/null 2>&1; then
        warn "No Git remote 'origin' configured"
    else
        log "✓ Git remote configured: $(git remote get-url origin)"
    fi
    
    # Проверяем текущую ветку
    current_branch=$(git branch --show-current)
    log "✓ Current branch: $current_branch"
    
    # Предупреждаем если мы не на main
    if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
        warn "Not on main branch - E2E tests may create branches from current state"
    fi
}

# Проверка сервисов
check_services() {
    log "Checking services..."
    
    # Проверяем основное приложение
    if curl -f -s -m 5 http://127.0.0.1:8081/health/live >/dev/null 2>&1; then
        log "✓ Main application running on port 8081"
    else
        warn "Main application not running - start with: uvicorn app.main:app --host 0.0.0.0 --port 8081"
    fi
    
    # Проверяем базу данных
    if [[ -f "/opt/feature-factory/data/test.db" ]]; then
        log "✓ Database file exists"
    else
        warn "Database file not found - will be created automatically"
    fi
}

# Установка прав доступа
set_permissions() {
    log "Setting permissions..."
    
    # Делаем скрипты исполняемыми
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;
    
    # Проверяем что пользователь может писать в нужные директории
    if [[ ! -w "$PROJECT_ROOT/data" ]]; then
        warn "No write access to data directory - some tests may fail"
    fi
    
    log "✓ Permissions set"
}

# Тестирование конфигурации
test_configuration() {
    log "Testing E2E configuration..."
    
    # Запускаем простой тест Python утилит
    if .venv/bin/python "$SCRIPT_DIR/e2e_utils.py" 2>/dev/null; then
        log "✓ Python E2E utilities working"
    else
        warn "Python E2E utilities test failed - check dependencies"
    fi
    
    # Тестируем bash скрипт (dry run)
    if E2E_MODE=safe bash "$SCRIPT_DIR/e2e_safe_test.sh" --dry-run 2>/dev/null; then
        log "✓ Bash E2E script working"
    else
        warn "Bash E2E script test failed"
    fi
}

# Создание примера конфигурации
create_sample_config() {
    local config_file="$PROJECT_ROOT/.e2erc.example"
    
    if [[ ! -f "$config_file" ]]; then
        log "Creating example configuration..."
        
        cat > "$config_file" << 'EOF'
# E2E Test Configuration Example
# Копируйте в .e2erc и настройте под свои нужды

# Основные настройки
export E2E_MODE="safe"                    # safe, full, mock
export E2E_BASE_URL="http://127.0.0.1:8081"
export E2E_TIMEOUT="30"

# Безопасность
export E2E_CLEANUP_ENABLED="true"        # всегда убирать за собой
export E2E_BRANCH_PROTECTION="true"      # защита main веток
export E2E_REQUIRE_CONFIRMATION="true"   # спрашивать подтверждение

# Лимиты
export E2E_MAX_TEST_FEATURES="3"
export E2E_MAX_TEST_BRANCHES="2"

# Исключения
export E2E_SKIP_BRANCHES="main,master,develop"
export E2E_SKIP_DESTRUCTIVE_TESTS="true"

# Отчёты
export E2E_REPORT_FORMAT="json,text"
export E2E_LOG_LEVEL="info"
export E2E_SAVE_ARTIFACTS="true"
EOF
        log "✓ Example config created: $config_file"
        log "  Copy to .e2erc and customize as needed"
    fi
}

# Главная функция
main() {
    log "🚀 Setting up E2E testing environment..."
    
    # Проверяем что мы в правильной директории
    if [[ ! -f "$PROJECT_ROOT/app/main.py" ]]; then
        error "Not in Feature Factory project root"
        exit 1
    fi
    
    # Выполняем установку
    setup_directories
    install_dependencies
    fix_database_schema
    check_git_config
    check_services
    set_permissions
    create_sample_config
    
    # Исправляем проблемы с runner
    log "Fixing runner issues..."
    .venv/bin/python "$SCRIPT_DIR/fix_runner.py"
    
    # Тестируем конфигурацию
    test_configuration
    
    log "✅ E2E setup completed!"
    
    # Показываем как использовать
    echo ""
    echo "🧪 Now you can run E2E tests:"
    echo "  ./scripts/e2e_safe_test.sh           # Safe mode (read-only)"
    echo "  FULL_TEST=true ./scripts/e2e_safe_test.sh  # Full test with cleanup"
    echo "  python3 ./scripts/e2e_utils.py      # Python utilities"
    echo ""
    echo "📖 See scripts/README_E2E.md for detailed documentation"
    
    if [[ ! -f "$PROJECT_ROOT/.e2erc" ]]; then
        echo ""
        echo "💡 Tip: Copy .e2erc.example to .e2erc and customize configuration"
    fi
}

# Обработка аргументов
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  --help, -h    Show this help"
        echo "  --check       Only check configuration, don't install"
        exit 0
        ;;
    --check)
        log "Checking configuration only..."
        check_git_config
        check_services
        test_configuration
        exit 0
        ;;
esac

# Запуск
main "$@"