# Карта Доступа к Секретам

## Админка Feature Factory

### UI Доступ (Basic Auth)
- **Логин**: используй `secret_store.get_secret("admin.ui.username")`
- **Пароль**: используй `secret_store.get_secret("admin.ui.password")`
- **Контекст**: Для доступа к админке через браузер или API запросы к `/admin/*`

### API Ключи
- **Admin API Token**: используй `secret_store.get_secret("admin.api.token")`
- **Контекст**: Для программного доступа к административным эндпоинтам

## База данных

### Основная БД Feature Factory
- **URL подключения**: используй `secret_store.get_secret("database.url")`
- **Контекст**: Для прямого доступа к БД (миграции, бэкапы)

### Тестовая БД
- **URL подключения**: используй `secret_store.get_secret("database.test.url")`
- **Контекст**: Для выполнения интеграционных тестов

## Внешние сервисы

### LLM Provider Keys
- **OpenAI API Key**: используй `secret_store.get_secret("llm.openai.api_key")`
- **Anthropic API Key**: используй `secret_store.get_secret("llm.anthropic.api_key")`
- **Local LLM Endpoint**: используй `secret_store.get_secret("llm.local.endpoint")`

### SSL/TLS Сертификаты
- **SSL Cert Path**: используй `secret_store.get_secret("ssl.cert.path")`
- **SSL Key Path**: используй `secret_store.get_secret("ssl.key.path")`

## Правила использования

1. **НИКОГДА** не используй секреты напрямую в коде
2. **ВСЕГДА** используй функцию `secret_store.get_secret(key)`
3. **НЕ ЛОГИРУЙ** значения секретов в плейн-текст логи
4. **ПРОВЕРЯЙ** наличие секрета через `secret_store.has_secret(key)` перед использованием

## Импорт в коде

```python
from app.api.secrets import secret_store

# Правильно
password = secret_store.get_secret("admin.ui.password")

# Неправильно - НИКОГДА так не делай
password = "hardcoded_password"
```

## Примеры использования

### Доступ к админке через requests
```python
import requests
from app.api.secrets import secret_store

username = secret_store.get_secret("admin.ui.username")
password = secret_store.get_secret("admin.ui.password")

response = requests.get(
    "https://etl-tst.chococraft.ru/admin/api/jobs",
    auth=(username, password)
)
```

### Подключение к БД
```python
from sqlalchemy import create_engine
from app.api.secrets import secret_store

db_url = secret_store.get_secret("database.url")
engine = create_engine(db_url)
```