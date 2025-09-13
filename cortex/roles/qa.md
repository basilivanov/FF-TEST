# Правила для роли QA

## Основная ответственность
Валидация качества работы других ролей через проверку DoD критериев.

## Обязательные артефакты
- `qa_report.md` или `qa_report.json` с результатами всех проверок
- Детальные логи всех выполненных тестов
- Протоколы проверки критических функций

## Проверка DoD критериев
- Каждый критерий из DoD должен быть **фактически проверен**
- "PASS" только при наличии подтверждающих данных
- При FAIL — точное указание причин и рекомендации

## Обязательные проверки для Dev артефактов
- Валидность `artifact_manifest.yaml` против схемы
- Соответствие созданных файлов `package_contract`
- Отсутствие секретов в коде (паттерны ключей, паролей)
- Наличие `llm_call_end` событий в логах
- Правильность путей файлов (в пределах разрешенных директорий)

## Обязательные проверки для Architect артефактов
- Валидность `package_contract.yaml` и `plan.dsl.yaml`
- Наличие всех обязательных полей в контрактах
- Корректность ролей в DAG плана
- Отсутствие битых ссылок на артефакты

## Критичные ошибки (FAIL)
- Невалидный отчет по схеме
- "PASS" без фактических проверок
- Отсутствие журналов тестов
- Двусмысленные результаты проверки
- Критичные нарушения безопасности

## Формат QA отчета
```yaml
result: "PASS|FAIL"
checks:
  - name: "Название проверки"
    status: "PASS|FAIL"
    details: "Детали проверки"
    evidence: "Подтверждающие данные"
coverage_metrics:
  critical_paths: "85%"
test_protocols: "путь/к/протоколам"
```

## Тестовые паттерны и шаблоны

### API Endpoint тестирование
```python
# Паттерн тестирования FastAPI endpoints
def test_api_endpoint_success():
    response = client.get("/api/v1/endpoint")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_api_endpoint_validation():
    response = client.post("/api/v1/endpoint", json={"invalid": "data"})
    assert response.status_code == 422
    assert "validation error" in response.json()["detail"]
```

### Database операции тестирование
```python
# Паттерн тестирования CRUD операций  
def test_database_create_read():
    # Create
    new_record = create_record({"name": "test"})
    assert new_record.id is not None
    
    # Read
    retrieved = get_record(new_record.id)
    assert retrieved.name == "test"
```

### Alembic миграции тестирование
```python
# Паттерн тестирования миграций
def test_migration_upgrade_downgrade():
    # Apply migration
    result = subprocess.run(["alembic", "upgrade", "head"])
    assert result.returncode == 0
    
    # Check schema changes applied
    assert table_exists("new_table_name")
    
    # Test downgrade
    result = subprocess.run(["alembic", "downgrade", "-1"])  
    assert result.returncode == 0
    assert not table_exists("new_table_name")
```

### Integration тестирование
```python
# Паттерн E2E тестирования workflows
def test_complete_feature_workflow():
    # 1. Create feature
    response = client.post("/api/v1/features", json={
        "title": "Test Feature",
        "autostart": True
    })
    feature_id = response.json()["id"]
    
    # 2. Wait for processing
    wait_for_feature_status(feature_id, "COMPLETED")
    
    # 3. Verify results
    feature = client.get(f"/api/v1/features/{feature_id}").json()
    assert feature["status"] == "COMPLETED"
```

### Security тестирование  
```python
# Паттерн тестирования безопасности
def test_authentication_required():
    response = client.get("/api/v1/protected")
    assert response.status_code == 401
    
def test_authorization_enforced():
    response = client.get("/api/v1/admin", headers=get_user_headers())
    assert response.status_code == 403
    
def test_input_sanitization():
    malicious_input = "<script>alert('xss')</script>"
    response = client.post("/api/v1/data", json={"content": malicious_input})
    # Should not contain unescaped script
    assert "<script>" not in response.json().get("content", "")
```

### Performance тестирование
```python
# Паттерн тестирования производительности
def test_response_time_within_limits():
    import time
    start_time = time.time()
    
    response = client.get("/api/v1/health")
    
    end_time = time.time()
    response_time = end_time - start_time
    
    assert response.status_code == 200
    assert response_time < 0.1  # < 100ms
    
def test_concurrent_requests():
    import concurrent.futures
    
    def make_request():
        return client.get("/api/v1/features")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [f.result() for f in futures]
    
    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count >= 45  # 90% success rate
```

## Coverage требования по компонентам

### Критичные пути (95%+ coverage)
- Health endpoints: `/health/live`, `/health/ready`
- Authentication/Authorization middleware
- Feature CRUD operations
- Database connection management
- Correlation ID tracking

### Высокий приоритет (85%+ coverage)
- All API endpoints
- LLM router functionality  
- Context packager components
- Symbol index queries
- Error handling workflows

### Средний приоритет (70%+ coverage)
- Admin UI components
- Background tasks
- Git integration
- Metrics collection

## Инструменты и команды

### Запуск тестов с coverage
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
pytest --cov=app.api --cov-fail-under=85
coverage html -d htmlcov/
```

### Smoke тесты
```bash
# Health check smoke test
curl -f http://localhost:8081/health/live

# API smoke test
curl -f -X POST http://localhost:8081/api/v1/features \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: SMOKE_TEST" \
  -d '{"title": "Smoke Test Feature"}'
```

### Performance benchmarking
```bash
# Load testing with curl
seq 1 100 | xargs -P 10 -I {} curl -s http://localhost:8081/health/live

# Response time measurement
time curl http://localhost:8081/api/v1/features
```