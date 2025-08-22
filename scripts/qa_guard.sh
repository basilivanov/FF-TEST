#!/bin/bash

# QA Guard Script - Quality Rules Enforcement
# Task: E7-QA-LINTER (Dev)
# 
# This script enforces quality rules and prevents code violations.
# Returns exit code 1 if any violations are found.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Violation counter
VIOLATIONS=0

# Function to log violations
log_violation() {
    local file="$1"
    local line_num="$2"
    local rule="$3"
    local message="$4"
    
    echo -e "${RED}QA_POLICY_VIOLATION${NC}: $rule"
    echo -e "  File: ${YELLOW}$file${NC}"
    echo -e "  Line: ${YELLOW}$line_num${NC}"
    echo -e "  Message: $message"
    echo ""
    
    VIOLATIONS=$((VIOLATIONS + 1))
}

# Function to check files for violations
check_file() {
    local file="$1"
    
    # Skip non-existent files
    if [[ ! -f "$file" ]]; then
        return 0
    fi
    
    # Rule 1: assertIn(response.status_code, → FAIL
    if grep -n "assertIn(response\.status_code," "$file" > /dev/null 2>&1; then
        while IFS=: read -r line_num content; do
            log_violation "$file" "$line_num" "ASSERT_STATUS_CODE_IN" \
                "Use assertEqual(response.status_code, 200) instead of assertIn(response.status_code, [200, ...])"
        done < <(grep -n "assertIn(response\.status_code," "$file" 2>/dev/null || true)
    fi
    
    # Rule 2: :memory: или sqlite:///:memory: → FAIL
    if grep -n ":memory:" "$file" > /dev/null 2>&1; then
        while IFS=: read -r line_num content; do
            log_violation "$file" "$line_num" "MEMORY_DATABASE" \
                "In-memory databases are prohibited. Use proper test database isolation."
        done < <(grep -n ":memory:" "$file" 2>/dev/null || true)
    fi
    
    if grep -n "sqlite:///:memory:" "$file" > /dev/null 2>&1; then
        while IFS=: read -r line_num content; do
            log_violation "$file" "$line_num" "SQLITE_MEMORY_URL" \
                "SQLite memory URLs are prohibited. Use proper test database isolation."
        done < <(grep -n "sqlite:///:memory:" "$file" 2>/dev/null || true)
    fi
    
    # Rule 3: create_engine("sqlite:/// с конкатенацией пути → FAIL
    # Проверяем конкатенацию строк при создании sqlite URL
    if grep -n 'create_engine.*sqlite:///' "$file" > /dev/null 2>&1; then
        # Ищем строки с конкатенацией (+ или f-strings с переменными)
        while IFS=: read -r line_num content; do
            # Проверяем на конкатенацию с +
            if echo "$content" | grep 'create_engine.*sqlite://.*+' > /dev/null 2>&1; then
                log_violation "$file" "$line_num" "SQLITE_PATH_CONCAT" \
                    "SQLite URL path concatenation detected. Use proper path handling with get_db_connection_string()."
            fi
            # Проверяем на f-strings с переменными
            if echo "$content" | grep "create_engine.*f['\"]sqlite:///" > /dev/null 2>&1; then
                log_violation "$file" "$line_num" "SQLITE_FSTRING_PATH" \
                    "SQLite URL f-string path detected. Use proper path handling with get_db_connection_string()."
            fi
            # Проверяем на конкатенацию с .format() или %
            if echo "$content" | grep 'create_engine.*\.format' > /dev/null 2>&1; then
                log_violation "$file" "$line_num" "SQLITE_PATH_FORMAT" \
                    "SQLite URL path formatting detected. Use proper path handling with get_db_connection_string()."
            fi
        done < <(grep -n 'create_engine.*sqlite:///' "$file" 2>/dev/null || true)
    fi
}

# Main execution
echo -e "${GREEN}QA Guard${NC}: Checking quality rules..."

# If files are passed as arguments, check only those files
if [[ $# -gt 0 ]]; then
    for file in "$@"; do
        # Convert relative paths to absolute
        if [[ ! "$file" =~ ^/ ]]; then
            file="$PROJECT_ROOT/$file"
        fi
        check_file "$file"
    done
else
    # Check all Python and YAML files in the project
    echo "Checking all Python and YAML files..."
    find "$PROJECT_ROOT" -name "*.py" -o -name "*.yaml" -o -name "*.yml" | while read -r file; do
        # Skip virtual environments and hidden directories
        if [[ "$file" =~ /\.|venv|__pycache__|\.git ]]; then
            continue
        fi
        check_file "$file"
    done
fi

# Report results
echo ""
if [[ $VIOLATIONS -eq 0 ]]; then
    echo -e "${GREEN}✅ QA Guard: No violations found${NC}"
    exit 0
else
    echo -e "${RED}❌ QA Guard: Found $VIOLATIONS violation(s)${NC}"
    echo ""
    echo -e "${YELLOW}To fix these violations:${NC}"
    echo "1. For assertIn(response.status_code, ...) → Use assertEqual(response.status_code, 200)"
    echo "2. For :memory: databases → Use proper test database isolation"
    echo "3. For SQLite path concatenation → Use get_db_connection_string()"
    echo ""
    exit 1
fi