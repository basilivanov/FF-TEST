# API Testing Guide

## Обзор

Этот документ описывает подход к тестированию API Feature Factory.

## Стек тестирования

- pytest - фреймворк для тестирования Python
- pytest-cov - для измерения покрытия кода
- httpx - для асинхронных HTTP запросов
- respx - для мокирования HTTP запросов

## Структура тестов

Тесты организованы по следующей структуре:

```
tests/
  conftest.py          # Общая конфигурация тестов
  test_maintainer_api.py  # Тесты для Maintainer API
  test_ui_api.py       # Тесты для UI API (Stream, Logs, Tokens)
  test_orchestrator_api_v2.py  # Тесты для Orchestrator API
```

## Покрытие тестами

### Maintainer API

1. **POST /api/v1/maintainer/intent**
   - Успешная генерация интента
   - Ошибка при пустом тексте
   - Ошибка при превышении лимита токенов
   - Внутренняя ошибка сервера

2. **POST /api/v1/maintainer/plan**
   - Успешная генерация плана
   - Ошибка при пустом интенте
   - Ошибка при превышении лимита токенов
   - Внутренняя ошибка сервера

### UI API

1. **GET /api/v1/stream/events**
   - Успешное подключение к потоку событий
   - Отправка событий клиенту
   - Обработка отключения клиента

2. **GET /api/v1/logs/tail**
   - Успешное получение логов
   - Фильтрация логов по параметрам
   - Ограничение количества записей
   - Внутренняя ошибка сервера

3. **GET /admin/tokens**
   - Успешное получение статистики токенов
   - Внутренняя ошибка сервера

### Orchestrator API

1. **POST /api/v1/orchestrator/features**
   - Успешное создание фичи
   - Идемпотентность создания фичи
   - Ошибка при некорректных данных
   - Внутренняя ошибка сервера

2. **POST /api/v1/orchestrator/features/{id}/plan**
   - Успешное планирование фичи
   - Ошибка при несуществующей фиче
   - Ошибка при недопустимом статусе фичи
   - Внутренняя ошибка сервера

3. **POST /api/v1/orchestrator/features/{id}/run**
   - Успешный запуск фичи
   - Ошибка при несуществующей фиче
   - Ошибка при недопустимом статусе фичи
   - Внутренняя ошибка сервера

4. **GET /api/v1/orchestrator/graph/{run_id}/status**
   - Успешное получение статуса графа
   - Ошибка при несуществующем запуске графа
   - Внутренняя ошибка сервера

## Запуск тестов

### Запуск всех тестов

```bash
cd /opt/feature-factory
python -m pytest tests/
```

### Запуск тестов с coverage отчетом

```bash
cd /opt/feature-factory
python -m pytest tests/ --cov=app --cov-report=html
```

### Запуск отдельного теста

```bash
cd /opt/feature-factory
python -m pytest tests/test_maintainer_api.py::TestMaintainerAPI::test_generate_intent_success
```

## Покрытие кода

Цель покрытия кода тестами: 90% для критических API эндпоинтов.

Критические эндпоинты:
- POST /api/v1/maintainer/intent
- POST /api/v1/maintainer/plan
- POST /api/v1/orchestrator/features
- POST /api/v1/orchestrator/features/{id}/plan
- POST /api/v1/orchestrator/features/{id}/run
- GET /api/v1/orchestrator/graph/{run_id}/status

## Best Practices

### Тестирование поведения, а не реализации

- Фокусируйтесь на том, что делает API, а не как он это делает
- Проверяйте корректность ответов API
- Проверяйте обработку ошибок

### Мокирование внешних зависимостей

- Мокируйте вызовы LLM
- Мокируйте обращения к базе данных
- Мокируйте обращения к внешним API

### Использование фикстур

- Используйте фикстуры для создания тестовых данных
- Используйте фикстуры для настройки окружения
- Используйте фикстуры для очистки после тестов

### Тестирование пограничных случаев

- Пустые значения
- Некорректные данные
- Превышение лимитов
- Внутренние ошибки

### Асинхронное тестирование

- Используйте async/await для асинхронных тестов
- Тестируйте конкурентное выполнение
- Проверяйте таймауты

## Примеры тестов

### Тест API эндпоинта

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_generate_intent_success(client):
    # Подготавливаем данные для запроса
    intent_data = {
        "nl_text": "Создай фичу для импорта данных из Excel"
    }
    
    # Отправляем POST запрос
    response = client.post("/api/v1/maintainer/intent", json=intent_data)
    
    # Проверяем статус ответа
    assert response.status_code == 200
    
    # Проверяем структуру ответа
    response_data = response.json()
    assert "nl_text" in response_data
    assert "intent_json" in response_data
    assert "issues" in response_data
    assert "suggestions" in response_data
    assert response_data["nl_text"] == intent_data["nl_text"]
    
    # Проверяем, что intent_json не пустой
    assert isinstance(response_data["intent_json"], dict)
    assert len(response_data["intent_json"]) > 0
```

### Тестирование ошибок

```python
def test_generate_intent_empty_text(client):
    # Подготавливаем данные для запроса
    intent_data = {
        "nl_text": ""
    }
    
    # Отправляем POST запрос
    response = client.post("/api/v1/maintainer/intent", json=intent_data)
    
    # Проверяем статус ответа
    assert response.status_code == 400
    
    # Проверяем структуру ответа
    response_data = response.json()
    assert "error" in response_data
    assert response_data["error"] == "EMPTY_NL_TEXT"
```

### Мокирование внешних зависимостей

```python
import respx
from httpx import Response

@respx.mock
def test_generate_intent_llm_call(client):
    # Мокируем вызов LLM
    respx.post("http://localhost:4000/chat/completions").mock(
        return_value=Response(200, json={
            "choices": [{
                "message": {
                    "content": '{"action": "create_feature", "title": "Import Excel Data"}'
                }
            }]
        })
    )
    
    # Подготавливаем данные для запроса
    intent_data = {
        "nl_text": "Создай фичу для импорта данных из Excel"
    }
    
    # Отправляем POST запрос
    response = client.post("/api/v1/maintainer/intent", json=intent_data)
    
    # Проверяем статус ответа
    assert response.status_code == 200
```

## Отчеты о покрытии

После запуска тестов с флагом --cov будет сгенерирован отчет о покрытии кода тестами. Отчет будет доступен в директории htmlcov/.

## CI/CD интеграция

Тесты запускаются автоматически в CI pipeline при каждом пуше в репозиторий. Pipeline проваливается, если:
- Тесты не проходят
- Покрытие кода падает ниже порога (90% для критических API)