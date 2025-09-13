# Политики безопасности

## Управление секретами

### Обязательные правила
- **НИКОГДА** не используй секреты напрямую в коде
- **ВСЕГДА** используй функцию `secret_store.get_secret(key)`  
- **НЕ ЛОГИРУЙ** значения секретов — только `***REDACTED***`
- **ПРОВЕРЯЙ** наличие секрета через `secret_store.has_secret(key)`

### Карта секретов
```python
# Админка
secret_store.get_secret("admin.ui.username")
secret_store.get_secret("admin.ui.password") 
secret_store.get_secret("admin.api.token")

# База данных
secret_store.get_secret("database.url")
secret_store.get_secret("database.test.url")

# LLM провайдеры
secret_store.get_secret("llm.openai.api_key")
secret_store.get_secret("llm.anthropic.api_key")
secret_store.get_secret("llm.local.endpoint")

# SSL/TLS
secret_store.get_secret("ssl.cert.path")
secret_store.get_secret("ssl.key.path")
```

## Логирование безопасности

### Обязательная редакция
- Все секреты, токены, пароли → `***REDACTED***`
- PII данные пользователей → `***PII_REDACTED***`
- API ключи и подписи → `***REDACTED***`

### Формат security логов
```json
{
  "ts": "2025-01-13T10:30:00Z",
  "level": "INFO", 
  "event": "secret_access",
  "secret_key": "admin.ui.password",
  "value": "***REDACTED***",
  "correlation_id": "CORR_123456"
}
```

## Доступ к файлам

### Разрешенные директории
- `/opt/feature-factory/artifacts/`
- `/opt/feature-factory/data/`  
- `/opt/feature-factory/tmp/`
- `/opt/feature-factory/backups/`

### Запрещенные операции
- Чтение `/etc/passwd`, `/etc/shadow`
- Доступ к `/home/*` кроме `/home/feature`
- Запись в системные директории `/usr`, `/bin`, `/sbin`
- Модификация критических конфигов без sudo

## Git безопасность

### SSH ключи
- Использовать только `~/.ssh/id_ed25519_ff`
- Настроить `IdentitiesOnly yes` в SSH config
- Никогда не коммитить приватные ключи

### Commit правила  
- Обязательная проверка секретов перед коммитом
- Подписывание коммитов при наличии GPG ключа
- Никогда не форсировать push в защищенные ветки