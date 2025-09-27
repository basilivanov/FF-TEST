#!/bin/bash
# Тестовый скрипт для проверки загрузки переменных окружения

echo "Проверка переменных окружения GitHub App..."

# Проверим, доступны ли переменные в файле
if [ -f "/etc/feature-factory/ci-secrets.env" ]; then
    echo "Файл /etc/feature-factory/ci-secrets.env существует"
    
    # Проверим наличие переменных GitHub App в файле
    if grep -q "GITHUB_APP_ID" /etc/feature-factory/ci-secrets.env; then
        echo "✅ GITHUB_APP_ID найден в файле"
    else
        echo "❌ GITHUB_APP_ID не найден в файле"
    fi
    
    if grep -q "GITHUB_APP_INSTALLATION_ID" /etc/feature-factory/ci-secrets.env; then
        echo "✅ GITHUB_APP_INSTALLATION_ID найден в файле"
    else
        echo "❌ GITHUB_APP_INSTALLATION_ID не найден в файле"
    fi
    
else
    echo "❌ Файл /etc/feature-factory/ci-secrets.env не существует"
fi

echo ""
echo "Проверка через systemctl show..."
systemctl show feature-factory-test --property=Environment | grep -i github || echo "Нет переменных GitHub в выводе systemctl"