#!/bin/bash
# Скрипт для настройки автоматического обновления OAuth токенов

# Создаём systemd service
sudo tee /etc/systemd/system/oauth-refresh.service > /dev/null << 'EOF'
[Unit]
Description=OAuth Token Refresh Daemon for FeatureFabric
After=network.target

[Service]
Type=simple
User=feature
Group=feature
WorkingDirectory=/opt/feature-factory
Environment=HOME=/home/feature
Environment=PYTHONPATH=/opt/feature-factory
ExecStart=/opt/feature-factory/.venv/bin/python /opt/feature-factory/scripts/refresh_tokens_daemon.py
Restart=always
RestartSec=60
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd и запускаем сервис
sudo systemctl daemon-reload
sudo systemctl enable oauth-refresh.service
sudo systemctl start oauth-refresh.service
sudo systemctl status oauth-refresh.service

echo "OAuth token refresh daemon configured and started"
echo "To view logs: sudo journalctl -u oauth-refresh.service -f"
echo "To stop: sudo systemctl stop oauth-refresh.service"