# Алерты дрейфа промптов

## Общие положения

Этот документ описывает настройку и обработку алертов о дрейфе промптов, которые возникают при несоответствии текущих промптов утвержденным версиям в файле блокировки.

## Обзор

При запуске Orchestrator система проверяет соответствие текущих промптов версиям, зафиксированным в `configs/prompts.lock.json`. При обнаружении расхождений генерируется событие `prompt_drift_detected`, которое должно приводить к отправке алерта ответственным лицам.

## Событие prompt_drift_detected

### Формат события

```json
{
  "event": "prompt_drift_detected",
  "role": "Dev",
  "expected_sha256": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7",
  "actual_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "file_path": "agents/prompts/dev.md",
  "timestamp": "2025-08-25T16:00:00Z"
}
```

### Поля события

- **event**: Тип события (всегда "prompt_drift_detected")
- **role**: Роль, для которой обнаружен дрейф
- **expected_sha256**: Ожидаемый SHA256 хэш из файла блокировки
- **actual_sha256**: Фактический SHA256 хэш текущего файла
- **file_path**: Путь к файлу промпта
- **timestamp**: Временная метка события

## Настройка алертов

### Slack алерты

#### Конфигурация в Slack

1. Создать канал #prompt-drift-alerts в Slack
2. Настроить интеграцию Incoming Webhooks для этого канала
3. Получить Webhook URL для использования в системе оповещений

#### Формат сообщения в Slack

```
🚨 Prompt Drift Detected 🚨

Role: Dev
File: agents/prompts/dev.md
Expected SHA256: f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7
Actual SHA256: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2
Timestamp: 2025-08-25T16:00:00Z

Please check the prompt file and update configs/prompts.lock.json if this change is intentional.
```

#### Реализация отправки в Slack

```python
import requests
import json
from typing import Dict, Any

def send_slack_alert(webhook_url: str, drift_data: Dict[str, Any]):
    """
    Отправка алерта о дрейфе промпта в Slack
    """
    message = {
        "text": "🚨 Prompt Drift Detected 🚨",
        "attachments": [
            {
                "color": "danger",
                "fields": [
                    {
                        "title": "Role",
                        "value": drift_data["role"],
                        "short": True
                    },
                    {
                        "title": "File",
                        "value": drift_data["file_path"],
                        "short": True
                    },
                    {
                        "title": "Expected SHA256",
                        "value": drift_data["expected_sha256"],
                        "short": False
                    },
                    {
                        "title": "Actual SHA256",
                        "value": drift_data["actual_sha256"],
                        "short": False
                    },
                    {
                        "title": "Timestamp",
                        "value": drift_data["timestamp"],
                        "short": True
                    }
                ],
                "footer": "Feature Factory Prompt Drift Alert"
            }
        ]
    }
    
    response = requests.post(webhook_url, json=message)
    return response.status_code == 200
```

### Email алерты

#### Конфигурация email

1. Настроить SMTP сервер для отправки уведомлений
2. Определить список получателей:
   - team-lead@example.com
   - architect@example.com
   - devops@example.com

#### Формат email сообщения

```
Subject: [ALERT] Prompt Drift Detected - Dev Role

🚨 Prompt Drift Detected 🚨

A prompt drift has been detected in the Feature Factory system.

Details:
- Role: Dev
- File: agents/prompts/dev.md
- Expected SHA256: f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7
- Actual SHA256: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2
- Timestamp: 2025-08-25T16:00:00Z

Please check the prompt file and update configs/prompts.lock.json if this change is intentional.

--
Feature Factory Monitoring System
```

#### Реализация отправки email

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List

def send_email_alert(smtp_config: Dict[str, str], recipients: List[str], drift_data: Dict[str, Any]):
    """
    Отправка алерта о дрейфе промпта по email
    """
    msg = MIMEMultipart()
    msg['From'] = smtp_config['from']
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = f"[ALERT] Prompt Drift Detected - {drift_data['role']} Role"
    
    body = f"""
🚨 Prompt Drift Detected 🚨

A prompt drift has been detected in the Feature Factory system.

Details:
- Role: {drift_data['role']}
- File: {drift_data['file_path']}
- Expected SHA256: {drift_data['expected_sha256']}
- Actual SHA256: {drift_data['actual_sha256']}
- Timestamp: {drift_data['timestamp']}

Please check the prompt file and update configs/prompts.lock.json if this change is intentional.

--
Feature Factory Monitoring System
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
    server.starttls()
    server.login(smtp_config['username'], smtp_config['password'])
    
    text = msg.as_string()
    server.sendmail(smtp_config['from'], recipients, text)
    server.quit()
```

## Интеграция с системой мониторинга

### Prometheus метрики

#### Метрика для Prometheus

```python
from prometheus_client import Counter, Gauge

# Счетчик событий дрейфа промптов
prompt_drift_events = Counter(
    'feature_factory_prompt_drift_events_total',
    'Total number of prompt drift events detected',
    ['role']
)

# ГаUGE для отслеживания последнего события дрейфа
last_prompt_drift_timestamp = Gauge(
    'feature_factory_last_prompt_drift_timestamp',
    'Timestamp of the last prompt drift event',
    ['role']
)

def record_prompt_drift(role: str, timestamp: str):
    """
    Запись метрик дрейфа промпта в Prometheus
    """
    prompt_drift_events.labels(role=role).inc()
    last_prompt_drift_timestamp.labels(role=role).set(
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").timestamp()
    )
```

### Grafana дашборд

#### Панель алертов

1. Создать дашборд "Prompt Drift Monitoring"
2. Добавить панель с графиком количества событий дрейфа по ролям
3. Добавить панель с таблицей последних событий дрейфа
4. Настроить алерты на основе метрик Prometheus

## Обработка алертов

### Процедура реагирования

1. **Получение алерта**: Алерт поступает в Slack канал и на email получателей
2. **Анализ ситуации**: Ответственные лица анализируют причину дрейфа
3. **Принятие решения**:
   - Если изменение intentional (намеренное), обновить `configs/prompts.lock.json`
   - Если изменение unintentional (случайное), откатить изменения
4. **Документирование**: Задокументировать причину и принятые меры

### Playbook для DevOps

#### Сценарий 1: Намеренное изменение промпта

1. Подтвердить, что изменение было намеренным
2. Вычислить SHA256 хэш нового промпта:
   ```bash
   sha256sum agents/prompts/dev.md
   ```
3. Обновить `configs/prompts.lock.json` с новым хэшем
4. Закоммитить и запушить изменения:
   ```bash
   git add configs/prompts.lock.json
   git commit -m "Update prompt lock for Dev role"
   git push origin main
   ```

#### Сценарий 2: Случайное изменение промпта

1. Подтвердить, что изменение было случайным
2. Откатить изменения в промпте:
   ```bash
   git checkout HEAD -- agents/prompts/dev.md
   ```
3. Проверить, что хэш соответствует ожидаемому:
   ```bash
   sha256sum agents/prompts/dev.md
   ```
4. Перезапустить Orchestrator для проверки

## Тестирование алертов

### Сценарий тестирования

1. Временно изменить содержимое промпта
2. Перезапустить Orchestrator
3. Проверить поступление алерта в Slack и на email
4. Проверить запись метрик в Prometheus
5. Откатить изменения и обновить файл блокировки

### Автоматическое тестирование

```python
import pytest
from unittest.mock import patch, MagicMock
import json

def test_prompt_drift_alert_slack():
    """Тест отправки алерта в Slack"""
    webhook_url = "https://hooks.slack.com/services/test"
    drift_data = {
        "role": "Dev",
        "expected_sha256": "expected_hash",
        "actual_sha256": "actual_hash",
        "file_path": "agents/prompts/dev.md",
        "timestamp": "2025-08-25T16:00:00Z"
    }
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        result = send_slack_alert(webhook_url, drift_data)
        assert result == True
        mock_post.assert_called_once()

def test_prompt_drift_alert_email():
    """Тест отправки алерта по email"""
    smtp_config = {
        "host": "smtp.example.com",
        "port": 587,
        "username": "user",
        "password": "pass",
        "from": "monitoring@example.com"
    }
    recipients = ["team@example.com"]
    drift_data = {
        "role": "Dev",
        "expected_sha256": "expected_hash",
        "actual_sha256": "actual_hash",
        "file_path": "agents/prompts/dev.md",
        "timestamp": "2025-08-25T16:00:00Z"
    }
    
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        send_email_alert(smtp_config, recipients, drift_data)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
```

## Мониторинг и улучшение

### KPI для алертов

1. **Время реакции**: Среднее время от поступления алерта до принятия мер
2. **Частота дрейфа**: Количество событий дрейфа в неделю
3. **Процент ложных срабатываний**: Доля алертов, которые оказались ложными

### Регулярные проверки

1. **Еженедельный аудит**: Проверка всех промптов на соответствие файлу блокировки
2. **Ежемесячный анализ**: Анализ частоты и причин дрейфа промптов
3. **Квартальное обновление**: Обновление процессов и документации на основе полученного опыта

## Best Practices

1. **Регулярное тестирование**: Регулярно тестировать систему алертов для проверки ее работоспособности
2. **Документирование изменений**: Все изменения промптов должны быть задокументированы
3. **Ограничение доступа**: Ограничьте доступ к промптам только авторизованным лицам
4. **Автоматизация**: Автоматизируйте процессы обновления файлов блокировки при намеренных изменениях
5. **Мониторинг метрик**: Регулярно отслеживайте метрики дрейфа промптов для выявления проблемных областей