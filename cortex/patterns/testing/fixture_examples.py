# Pytest Fixtures for FeatureFactory Testing

import pytest
import os
import tempfile
import time
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.utils.secret_store import secret_store
from app.context.packager import ContextPackager
from app.llm.router import LLMRouter

# Database Fixtures
@pytest.fixture(scope="function")
def test_db_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Create database session for testing"""
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def clean_db(db_session):
    """Ensure clean database state for each test"""
    # Truncate all tables
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
    yield db_session

# API Client Fixtures
@pytest.fixture(scope="function")
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture(scope="function")
def authenticated_client():
    """FastAPI test client with authentication headers"""
    client = TestClient(app)
    client.headers.update(get_basic_auth_headers())
    return client

@pytest.fixture(scope="function")
def correlation_id():
    """Generate unique correlation ID for tests"""
    return f"TEST_{int(time.time() * 1000)}"

@pytest.fixture(scope="function")
def request_headers(correlation_id):
    """Standard request headers for API calls"""
    return {
        "X-Correlation-Id": correlation_id,
        "Content-Type": "application/json"
    }

# Authentication Fixtures
@pytest.fixture(scope="function")
def mock_secret_store():
    """Mock secret store with test values"""
    original_get_secret = secret_store.get_secret
    
    def mock_get_secret(key):
        mock_secrets = {
            "admin.ui.username": "test_admin",
            "admin.ui.password": "test_password",
            "database.url": "sqlite:///:memory:",
            "llm.openai.api_key": "test_openai_key",
            "llm.anthropic.api_key": "test_anthropic_key",
            "ssl.cert.path": "/tmp/test_cert.pem",
            "ssl.key.path": "/tmp/test_key.pem"
        }
        return mock_secrets.get(key, f"mock_value_for_{key}")
    
    secret_store.get_secret = mock_get_secret
    yield secret_store
    secret_store.get_secret = original_get_secret

def get_basic_auth_headers():
    """Generate Basic Auth headers for CI endpoints"""
    import base64
    credentials = base64.b64encode(b"ops:ops123").decode("utf-8")
    return {"Authorization": f"Basic {credentials}"}

@pytest.fixture
def auth_headers():
    """Basic Auth headers fixture"""
    return get_basic_auth_headers()

# Data Fixtures
@pytest.fixture
def sample_feature_data():
    """Sample feature data for testing"""
    return {
        "title": "Test Feature Implementation",
        "intent": {
            "action": "create",
            "type": "api_endpoint",
            "description": "Add new health check endpoint"
        },
        "autostart": False
    }

@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "task": "Implement health check endpoint",
        "corr_id": f"TASK_{int(time.time())}",
        "context": ["/opt/feature-factory/app/api/", "FastAPI", "health"],
        "prechecks": ["Check FastAPI is running", "Verify database connectivity"],
        "plan": [
            "Create health check route",
            "Add database status check",
            "Write tests for endpoint",
            "Update API documentation"
        ],
        "dod": [
            "GET /health/live returns 200 status",
            "Response includes database status", 
            "Tests achieve >90% coverage",
            "Documentation updated"
        ],
        "artifacts_dir": "/opt/feature-factory/artifacts/test_health_check/"
    }

@pytest.fixture
def sample_ci_status():
    """Sample CI status data"""
    return {
        "context": "tests",
        "state": "success",
        "description": "All tests passed successfully"
    }

# File System Fixtures
@pytest.fixture
def temp_directory():
    """Create temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def temp_artifacts_dir():
    """Create temporary artifacts directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        artifacts_dir = os.path.join(temp_dir, "artifacts")
        os.makedirs(artifacts_dir, exist_ok=True)
        yield artifacts_dir

@pytest.fixture
def mock_cortex_files(temp_directory):
    """Create mock cortex files for testing"""
    cortex_dir = os.path.join(temp_directory, "cortex")
    os.makedirs(f"{cortex_dir}/core", exist_ok=True)
    os.makedirs(f"{cortex_dir}/roles", exist_ok=True)
    
    # Create mock files
    with open(f"{cortex_dir}/core/invariants.md", "w") as f:
        f.write("# Test Invariants\nSample content for testing")
    
    with open(f"{cortex_dir}/roles/dev.md", "w") as f:
        f.write("# Dev Role Rules\nTest content for dev role")
    
    yield cortex_dir

# Context and LLM Fixtures
@pytest.fixture
def mock_context_packager(mock_cortex_files):
    """Mock context packager with test data"""
    with patch.object(ContextPackager, '_load_playbook') as mock_load:
        mock_load.return_value = "Mock playbook content"
        packager = ContextPackager()
        yield packager

@pytest.fixture
def mock_llm_router():
    """Mock LLM router for testing"""
    router = Mock(spec=LLMRouter)
    router.route.return_value = {
        "provider": "mock",
        "model": "test-model",
        "response": "Mock LLM response",
        "usage": {"input_tokens": 100, "output_tokens": 50}
    }
    yield router

@pytest.fixture
def mock_symbol_index():
    """Mock symbol index data"""
    return [
        {
            "id": 1,
            "file_path": "/opt/feature-factory/app/api/health.py",
            "symbol_name": "health_live",
            "symbol_type": "function",
            "line_start": 10,
            "line_end": 15
        },
        {
            "id": 2,
            "file_path": "/opt/feature-factory/app/context/packager.py", 
            "symbol_name": "ContextPackager",
            "symbol_type": "class",
            "line_start": 38,
            "line_end": 200
        }
    ]

@pytest.fixture
def mock_call_graph():
    """Mock call graph data"""
    return [
        {
            "id": 1,
            "source_symbol": "health_live",
            "target_symbol": "db_health_check",
            "file_path": "/opt/feature-factory/app/api/health.py",
            "line_number": 12
        }
    ]

# Environment Fixtures
@pytest.fixture
def test_environment():
    """Set up test environment variables"""
    original_env = os.environ.copy()
    
    os.environ.update({
        "ENV": "TEST",
        "DATABASE_URL": "sqlite:///:memory:",
        "FF_BASE_URL": "http://localhost:8081",
        "CI": "true",
        "NO_COLOR": "1"
    })
    
    yield
    
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def mock_git_environment(temp_directory):
    """Mock git environment for testing"""
    git_dir = os.path.join(temp_directory, ".git")
    os.makedirs(git_dir, exist_ok=True)
    
    # Mock git config
    with open(f"{git_dir}/config", "w") as f:
        f.write("""[core]
    repositoryformatversion = 0
[remote "origin"]
    url = git@github.com:test/repo.git
""")
    
    yield temp_directory

# Performance Testing Fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()

# Database Seed Data Fixtures
@pytest.fixture
def seed_features(db_session):
    """Seed database with test features"""
    from app.db.models import Feature
    
    features = [
        Feature(
            id=1,
            title="Test Feature 1",
            status="NEW",
            correlation_id="TEST_FEATURE_1"
        ),
        Feature(
            id=2,
            title="Test Feature 2", 
            status="RUNNING",
            correlation_id="TEST_FEATURE_2"
        )
    ]
    
    for feature in features:
        db_session.add(feature)
    db_session.commit()
    
    yield features

@pytest.fixture
def seed_tasks(db_session, seed_features):
    """Seed database with test tasks"""
    from app.db.models import Task
    
    tasks = [
        Task(
            id=1,
            feature_id=1,
            role="Dev",
            status="NEW",
            correlation_id="TEST_TASK_1"
        ),
        Task(
            id=2,
            feature_id=2,
            role="QA", 
            status="COMPLETED",
            correlation_id="TEST_TASK_2"
        )
    ]
    
    for task in tasks:
        db_session.add(task)
    db_session.commit()
    
    yield tasks

# Cleanup Fixtures
@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Automatic cleanup of temporary files after tests"""
    yield
    # Cleanup logic runs after each test
    temp_files = [f for f in os.listdir("/tmp") if f.startswith("pytest_")]
    for temp_file in temp_files:
        try:
            os.remove(f"/tmp/{temp_file}")
        except (OSError, FileNotFoundError):
            pass