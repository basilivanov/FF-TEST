# Test Coverage Rules for FeatureFactory

## Minimum Coverage Requirements

### Critical Paths (95%+ coverage required)
- **Health endpoints**: `/health/live`, `/health/ready`
- **Authentication/Authorization**: Basic Auth, correlation ID validation
- **Feature CRUD**: Create, read, update feature operations
- **CI Status**: All CI webhook handlers
- **Database operations**: Alembic migrations, WAL mode checks

### High Priority (85%+ coverage required)
- **API endpoints**: All `/api/v1/` routes
- **LLM routing**: Provider selection, token management
- **Context packaging**: Content loading, role-specific context
- **Symbol indexing**: Search, call graph queries
- **Error handling**: 4xx, 5xx response scenarios

### Medium Priority (70%+ coverage required)
- **Admin UI endpoints**: Dashboard, metrics, agent status
- **Logging**: Structured logging, correlation ID tracking
- **Background tasks**: Runner loop, queue processing
- **Git operations**: Branch creation, PR management

### Low Priority (50%+ coverage required)
- **Development utilities**: Dev-only endpoints, debug tools
- **Legacy code**: Deprecated functions marked for removal

## Test Types and Distribution

### Unit Tests (60% of total tests)
```python
# Example: Test individual functions
def test_secret_store_get_secret():
    secret = secret_store.get_secret("test.key")
    assert secret is not None

def test_correlation_id_generation():
    corr_id = generate_correlation_id()
    assert corr_id.startswith("TASK_")
    assert len(corr_id) > 10
```

### Integration Tests (30% of total tests)
```python
# Example: Test component interactions
def test_feature_creation_with_db():
    feature = create_feature("Test Feature")
    db_feature = get_feature_from_db(feature.id)
    assert db_feature.title == "Test Feature"
```

### End-to-End Tests (10% of total tests)
```python
# Example: Full workflow tests
def test_complete_feature_pipeline():
    # Create -> Plan -> Execute -> CI -> Merge
    response = client.post("/api/v1/orchestrator/features", json={...})
    # ... full workflow validation
```

## Coverage Measurement

### Tools
- **Primary**: `pytest-cov` with HTML reports
- **CI Integration**: Coverage reports in GitHub Actions
- **Quality Gates**: Fail CI if coverage drops below thresholds

### Commands
```bash
# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Coverage for specific modules
pytest --cov=app.api --cov-report=term-missing

# Generate coverage report
coverage html -d htmlcov/
```

### Reporting
```bash
# Coverage thresholds in pytest.ini
[tool:pytest]
addopts = --cov=app --cov-fail-under=80 --cov-report=term-missing
```

## Branch Coverage Rules

### Critical Decision Points
- **Authentication checks**: Both success/failure paths
- **Validation logic**: Valid/invalid input scenarios  
- **Error handling**: All exception types and recovery paths
- **State transitions**: All possible feature status changes

### Example Branch Coverage
```python
def test_auth_validation_branches():
    # Test success path
    result = validate_auth("valid_token")
    assert result.success == True
    
    # Test failure paths
    result = validate_auth("invalid_token")
    assert result.success == False
    
    result = validate_auth(None)
    assert result.error == "missing_token"
    
    result = validate_auth("")
    assert result.error == "empty_token"
```

## Test Data Management

### Fixtures
```python
@pytest.fixture
def test_feature_data():
    return {
        "title": "Test Feature",
        "intent": {"action": "create"},
        "correlation_id": "TEST_123456"
    }

@pytest.fixture
def mock_database():
    # Return in-memory database for tests
    return create_engine("sqlite:///:memory:")
```

### Test Database
- **Isolation**: Each test gets fresh database state
- **Transactions**: Rollback after each test
- **Seed data**: Minimal required data for tests

## Performance Testing

### Response Time Thresholds
- **Health endpoints**: < 50ms
- **API endpoints**: < 200ms  
- **Database queries**: < 100ms
- **Complex operations**: < 1000ms

### Load Testing
```python
def test_concurrent_feature_creation():
    import concurrent.futures
    
    def create_feature():
        return client.post("/api/v1/orchestrator/features", ...)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_feature) for _ in range(50)]
        results = [f.result() for f in futures]
    
    success_count = sum(1 for r in results if r.status_code == 201)
    assert success_count >= 45  # 90% success rate under load
```

## Smoke Tests

### Critical Path Validation
```python
def test_smoke_complete_system():
    """Smoke test for critical system functionality"""
    
    # 1. Health checks pass
    assert client.get("/health/live").status_code == 200
    
    # 2. Database accessible
    assert client.get("/api/v1/features").status_code == 200
    
    # 3. Authentication works  
    auth_response = client.post("/api/v1/ci/status", 
                               headers=get_auth_headers(), 
                               json={"context": "test", "state": "success"})
    assert auth_response.status_code == 200
    
    # 4. Symbol index available
    assert client.get("/api/v1/index/symbol").status_code == 200
```

## QA Checklist Integration

### Pre-commit Hooks
- Run unit tests
- Check coverage thresholds
- Validate test naming conventions

### CI Pipeline Gates
- All tests pass
- Coverage meets minimum thresholds  
- No flaky tests (3+ consecutive runs)
- Performance tests within limits

### Release Criteria
- 95%+ coverage on critical paths
- All smoke tests pass
- No known test failures
- Performance regression checks pass

## Test Maintenance

### Review Schedule
- **Weekly**: Review flaky tests, update fixtures
- **Monthly**: Analyze coverage gaps, refactor slow tests
- **Release**: Full test suite audit, performance validation

### Test Hygiene
- Remove obsolete tests for deleted features
- Update tests when APIs change
- Maintain clear test documentation
- Regular fixture cleanup