#!/bin/bash
# Скрипт для добавления GitHub App конфигурации в сервис Orchestrator

echo "Adding GitHub App configuration to feature-factory-test service..."

# Создаем override файл для systemd сервиса
mkdir -p /etc/systemd/system/feature-factory-test.service.d/

cat > /etc/systemd/system/feature-factory-test.service.d/30-github-app.conf << 'EOF'
[Service]
EnvironmentFile=/opt/feature-factory/github_app_config.env
EOF

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Restarting feature-factory-test service..."
systemctl restart feature-factory-test

echo "Done. GitHub App configuration has been added."