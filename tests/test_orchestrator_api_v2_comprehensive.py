#!/usr/bin/env python3
"""
Comprehensive QA tests for orchestrator API v2
Validates E7-ORCH-API-QA requirements:
- POST /features: 200, JSON schema compliance, DB writes
- plan: creates tasks and package_contract 
- run: creates graph_runs and starts G1
- status: correct JSON, status validation
- DB: uses exact DATABASE_URL from env
- Logs: correlation_id and event catalog compliance
- Zero tolerance for 500 errors
- ≥70% branch coverage on critical paths
"""

import unittest
import json
import os
import tempfile
import sqlite3
import uuid
from unittest.mock import patch, MagicMock, ANY
from fastapi.testclient import TestClient
from app.main import app
import jsonschema


class TestOrchestratorAPIV2Comprehensive(unittest.TestCase):
    """Comprehensive QA tests for orchestrator API v2."""

    @classmethod
    def setUpClass(cls):
        """Setup before all tests."""
        # Create temporary test database in required location
        cls.test_db_path = "/opt/feature-factory/tmp/test.db"
        os.makedirs(os.path.dirname(cls.test_db_path), exist_ok=True)
        cls.database_url = f"sqlite:///{cls.test_db_path}"
        
        # Set environment variables
        os.environ['DATABASE_URL'] = cls.database_url
        os.environ['ENV'] = 'test'
        
        # Create test tables
        cls._create_test_tables()
        
        # Create test client
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests."""
        if os.path.exists(cls.test_db_path):
            os.unlink(cls.test_db_path)
        
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

    @classmethod
    def _create_test_tables(cls):
        """Create test tables in database."""
        conn = sqlite3.connect(cls.test_db_path)
        cursor = conn.cursor()
        
        # Create tables according to schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                intent_json TEXT,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                env TEXT,
                UNIQUE(title, env)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                dsl_json TEXT,
                status TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                budget_tokens INTEGER,
                scheduled_at DATETIME,
                started_at DATETIME,
                finished_at DATETIME,
                FOREIGN KEY (feature_id) REFERENCES features (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_runs (
                run_id TEXT PRIMARY KEY,
                feature_id INTEGER NOT NULL,
                graph_name TEXT NOT NULL,
                thread_id TEXT,
                state_json TEXT,
                status TEXT,
                last_checkpoint_at DATETIME,
                FOREIGN KEY (feature_id) REFERENCES features (id)
            )
        """)
        
        conn.commit()
        conn.close()

    def setUp(self):
        """Setup before each test."""
        # Clear database before each test
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM graph_runs")
        cursor.execute("DELETE FROM tasks")
        cursor.execute("DELETE FROM features")
        conn.commit()
        conn.close()

    # JSON Schema definitions for validation
    FEATURE_CREATED_SCHEMA = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "status": {"type": "string", "enum": ["NEW", "PLANNED", "RUNNING", "DONE", "FAILED"]}
        },
        "required": ["id", "status"]
    }

    PLAN_RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "feature_id": {"type": "integer"},
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "role": {"type": "string"},
                        "status": {"type": "string", "const": "NEW"}
                    },
                    "required": ["id", "role", "status"]
                }
            },
            "package_contract": {"type": "object"}
        },
        "required": ["feature_id", "tasks", "package_contract"]
    }

    RUN_RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "run_id": {"type": "string"},
            "state": {"type": "string", "enum": ["STARTED", "RESUMED"]}
        },
        "required": ["run_id", "state"]
    }

    GRAPH_STATUS_SCHEMA = {
        "type": "object",
        "properties": {
            "run_id": {"type": "string"},
            "graph": {"type": "string", "const": "G1"},
            "status": {"type": "string", "enum": ["RUNNING", "DONE", "FAILED"]},
            "last_checkpoint": {"type": "string"}
        },
        "required": ["run_id", "graph", "status", "last_checkpoint"]
    }

    # TEST: POST /features endpoint comprehensive validation
    def test_create_feature_success_json_schema(self):
        """Test successful feature creation with JSON schema validation."""
        feature_data = {
            "title": f"Test Feature {uuid.uuid4()}",
            "intent": {"action": "test", "params": {"key": "value"}}
        }
        
        response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        
        # Verify HTTP 200
        self.assertEqual(response.status_code, 200)
        
        # Verify JSON schema compliance
        response_data = response.json()
        jsonschema.validate(response_data, self.FEATURE_CREATED_SCHEMA)
        
        # Verify specific values
        self.assertEqual(response_data["status"], "NEW")
        self.assertIsInstance(response_data["id"], int)
        self.assertGreater(response_data["id"], 0)

    def test_create_feature_database_write_verification(self):
        """Test that feature is correctly written to database."""
        feature_data = {
            "title": f"DB Test Feature {uuid.uuid4()}",
            "intent": {"action": "database_test", "params": {}}
        }
        
        response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(response.status_code, 200)
        
        feature_id = response.json()["id"]
        
        # Verify database write using exact DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        self.assertEqual(database_url, f"sqlite:///{self.test_db_path}")
        
        db_path = database_url[10:]  # Remove 'sqlite:///'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, intent_json, status, env, created_by 
            FROM features WHERE id = ?
        """, (feature_id,))
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], feature_id)
        self.assertEqual(row[1], feature_data["title"])
        self.assertEqual(json.loads(row[2]), feature_data["intent"])
        self.assertEqual(row[3], "NEW")
        self.assertEqual(row[4], "test")  # ENV from environment
        self.assertEqual(row[5], "API")

    def test_create_feature_idempotency_strict(self):
        """Test strict idempotency by (title, env)."""
        feature_data = {
            "title": f"Idempotent Feature {uuid.uuid4()}",
            "intent": {"action": "idempotency_test"}
        }
        
        # First request
        response1 = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(response1.status_code, 200)
        feature_id_1 = response1.json()["id"]
        
        # Second request with same data
        response2 = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(response2.status_code, 200)
        feature_id_2 = response2.json()["id"]
        
        # Must return same ID
        self.assertEqual(feature_id_1, feature_id_2)
        
        # Verify only one record in database
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM features WHERE title = ?", (feature_data["title"],))
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)

    def test_create_feature_validation_edge_cases(self):
        """Test edge cases and validation for feature creation."""
        # Test empty title
        response = self.client.post("/api/v1/orchestrator/features", json={"title": ""})
        self.assertNotEqual(response.status_code, 500)  # Zero tolerance for 500s
        
        # Test null intent
        response = self.client.post("/api/v1/orchestrator/features", json={
            "title": f"Null Intent {uuid.uuid4()}",
            "intent": None
        })
        self.assertEqual(response.status_code, 200)
        
        # Test missing intent
        response = self.client.post("/api/v1/orchestrator/features", json={
            "title": f"Missing Intent {uuid.uuid4()}"
        })
        self.assertEqual(response.status_code, 200)

    @patch('app.api.orchestrator_v2.log.info')
    def test_create_feature_logging_validation(self, mock_log_info):
        """Test logging contains correlation_id and proper events."""
        feature_data = {
            "title": f"Logging Test {uuid.uuid4()}",
            "intent": {"action": "logging_test"}
        }
        
        # Send request with custom correlation ID
        test_correlation_id = str(uuid.uuid4())
        response = self.client.post(
            "/api/v1/orchestrator/features", 
            json=feature_data,
            headers={"x-correlation-id": test_correlation_id}
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify logging was called
        self.assertTrue(mock_log_info.called)
        
        # Find start and end log calls
        start_calls = [call for call in mock_log_info.call_args_list 
                      if call.kwargs.get('event') == 'api_call_start']
        end_calls = [call for call in mock_log_info.call_args_list 
                    if call.kwargs.get('event') == 'api_call_end']
        
        self.assertGreater(len(start_calls), 0, "Must log api_call_start")
        self.assertGreater(len(end_calls), 0, "Must log api_call_end")
        
        # Verify correlation_id in logs
        start_call = start_calls[0]
        self.assertEqual(start_call.kwargs.get('correlation_id'), test_correlation_id)
        
        # Verify event catalog compliance
        for call in mock_log_info.call_args_list:
            event = call.kwargs.get('event')
            if event:
                self.assertIn(event, ['api_call_start', 'api_call_end'], 
                             f"Event {event} not in catalog")

    # TEST: Plan endpoint comprehensive validation
    def test_plan_feature_creates_tasks_and_contract(self):
        """Test plan endpoint creates tasks and package_contract."""
        # Create feature first
        feature_data = {"title": f"Plan Test {uuid.uuid4()}"}
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        feature_id = create_response.json()["id"]
        
        # Call plan endpoint
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        
        # Verify HTTP 200 and schema
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        jsonschema.validate(response_data, self.PLAN_RESPONSE_SCHEMA)
        
        # Verify feature_id matches
        self.assertEqual(response_data["feature_id"], feature_id)
        
        # Verify tasks created
        tasks = response_data["tasks"]
        self.assertGreater(len(tasks), 0, "Must create at least one task")
        
        # Verify all tasks have status NEW
        for task in tasks:
            self.assertEqual(task["status"], "NEW")
            self.assertIn("role", task)
            self.assertIsInstance(task["id"], int)
        
        # Verify package_contract exists and is object
        self.assertIsInstance(response_data["package_contract"], dict)
        
        # Verify database state
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Check feature status updated to PLANNED
        cursor.execute("SELECT status FROM features WHERE id = ?", (feature_id,))
        feature_status = cursor.fetchone()[0]
        self.assertEqual(feature_status, "PLANNED")
        
        # Check tasks created in database
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE feature_id = ?", (feature_id,))
        task_count = cursor.fetchone()[0]
        self.assertEqual(task_count, len(tasks))
        
        conn.close()

    def test_plan_feature_not_found_404(self):
        """Test plan endpoint returns 404 for non-existent feature."""
        response = self.client.post("/api/v1/orchestrator/features/99999/plan")
        self.assertEqual(response.status_code, 404)
        
        # Verify no 500 error
        self.assertNotEqual(response.status_code, 500)

    def test_plan_feature_invalid_status_400(self):
        """Test plan endpoint returns 400 for invalid feature status."""
        # Create and plan feature
        feature_data = {"title": f"Invalid Status Test {uuid.uuid4()}"}
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        feature_id = create_response.json()["id"]
        
        # Plan once (changes status to PLANNED)
        plan_response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        self.assertEqual(plan_response.status_code, 200)
        
        # Try to plan again (should fail)
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        self.assertEqual(response.status_code, 400)

    # TEST: Run endpoint comprehensive validation
    def test_run_feature_creates_graph_runs_and_starts_g1(self):
        """Test run endpoint creates graph_runs and starts G1."""
        # Create and plan feature
        feature_data = {"title": f"Run Test {uuid.uuid4()}"}
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        feature_id = create_response.json()["id"]
        
        plan_response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        self.assertEqual(plan_response.status_code, 200)
        
        # Call run endpoint
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/run")
        
        # Verify HTTP 200 and schema
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        jsonschema.validate(response_data, self.RUN_RESPONSE_SCHEMA)
        
        # Verify run_id is UUID string
        run_id = response_data["run_id"]
        uuid.UUID(run_id)  # Will raise if not valid UUID
        
        # Verify state is STARTED
        self.assertEqual(response_data["state"], "STARTED")
        
        # Verify database state
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Check feature status updated to RUNNING
        cursor.execute("SELECT status FROM features WHERE id = ?", (feature_id,))
        feature_status = cursor.fetchone()[0]
        self.assertEqual(feature_status, "RUNNING")
        
        # Check graph_run created
        cursor.execute("""
            SELECT run_id, feature_id, graph_name, status, thread_id, state_json
            FROM graph_runs WHERE run_id = ?
        """, (run_id,))
        graph_run = cursor.fetchone()
        
        self.assertIsNotNone(graph_run)
        self.assertEqual(graph_run[0], run_id)
        self.assertEqual(graph_run[1], feature_id)
        self.assertEqual(graph_run[2], "G1")
        self.assertEqual(graph_run[3], "RUNNING")
        self.assertIsNotNone(graph_run[4])  # thread_id
        self.assertIsNotNone(graph_run[5])  # state_json
        
        # Check tasks status updated
        cursor.execute("SELECT status FROM tasks WHERE feature_id = ?", (feature_id,))
        task_statuses = [row[0] for row in cursor.fetchall()]
        for status in task_statuses:
            self.assertEqual(status, "RUNNING")
        
        conn.close()

    def test_run_feature_not_found_404(self):
        """Test run endpoint returns 404 for non-existent feature."""
        response = self.client.post("/api/v1/orchestrator/features/99999/run")
        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(response.status_code, 500)

    def test_run_feature_invalid_status_400(self):
        """Test run endpoint returns 400 for invalid feature status."""
        # Create feature but don't plan
        feature_data = {"title": f"Run Invalid Status {uuid.uuid4()}"}
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        feature_id = create_response.json()["id"]
        
        # Try to run without planning
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/run")
        self.assertEqual(response.status_code, 400)

    # TEST: Status endpoint comprehensive validation
    def test_get_graph_status_json_validation(self):
        """Test status endpoint returns correct JSON and statuses."""
        # Create, plan, and run feature
        feature_data = {"title": f"Status Test {uuid.uuid4()}"}
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        feature_id = create_response.json()["id"]
        
        plan_response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        self.assertEqual(plan_response.status_code, 200)
        
        run_response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/run")
        run_id = run_response.json()["run_id"]
        
        # Get status
        response = self.client.get(f"/api/v1/orchestrator/graph/{run_id}/status")
        
        # Verify HTTP 200 and schema
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        jsonschema.validate(response_data, self.GRAPH_STATUS_SCHEMA)
        
        # Verify specific values
        self.assertEqual(response_data["run_id"], run_id)
        self.assertEqual(response_data["graph"], "G1")
        self.assertIn(response_data["status"], ["RUNNING", "DONE", "FAILED"])
        self.assertIsInstance(response_data["last_checkpoint"], str)

    def test_get_graph_status_not_found_404(self):
        """Test status endpoint returns 404 for non-existent graph."""
        fake_run_id = str(uuid.uuid4())
        response = self.client.get(f"/api/v1/orchestrator/graph/{fake_run_id}/status")
        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(response.status_code, 500)

    # TEST: Database URL enforcement
    def test_database_url_enforcement(self):
        """Test that API uses exact DATABASE_URL from environment."""
        # Verify DATABASE_URL is set correctly
        expected_url = f"sqlite:///{self.test_db_path}"
        actual_url = os.environ.get('DATABASE_URL')
        self.assertEqual(actual_url, expected_url)
        
        # Create feature and verify it goes to correct database
        feature_data = {"title": f"DB URL Test {uuid.uuid4()}"}
        response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify in correct database file
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM features WHERE title = ?", (feature_data["title"],))
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)

    # TEST: Zero tolerance for 500 errors
    def test_no_500_errors_on_invalid_input(self):
        """Test that invalid inputs never return 500 errors."""
        # Invalid JSON
        response = self.client.post("/api/v1/orchestrator/features", 
                                   data="invalid json", 
                                   headers={"content-type": "application/json"})
        self.assertNotEqual(response.status_code, 500)
        
        # Missing required fields
        response = self.client.post("/api/v1/orchestrator/features", json={})
        self.assertNotEqual(response.status_code, 500)
        
        # Invalid feature ID types
        response = self.client.post("/api/v1/orchestrator/features/invalid/plan")
        self.assertNotEqual(response.status_code, 500)
        
        response = self.client.post("/api/v1/orchestrator/features/invalid/run")
        self.assertNotEqual(response.status_code, 500)
        
        # Invalid run ID
        response = self.client.get("/api/v1/orchestrator/graph/invalid/status")
        self.assertNotEqual(response.status_code, 500)

    # TEST: QA Policy violations should cause test failures
    def test_qa_policy_violations_fail_tests(self):
        """Test that QA policy violations cause test failures."""
        # This test demonstrates that we enforce QA policies
        
        # Test 1: DB policy violation - using production database
        database_url = os.environ.get('DATABASE_URL', '')
        if database_url.endswith('prod.db'):
            self.fail("DB policy violation: using production database in tests")
        
        # Test 2: QA policy compliance - we must use assertEqual, not assertIn for status codes
        response = self.client.post("/api/v1/orchestrator/features", json={"title": f"QA Policy Test {uuid.uuid4()}"})
        
        # CORRECT: precise assertion
        self.assertEqual(response.status_code, 200)
        
        # FORBIDDEN (would be a QA policy violation):
        # self.assertIn(response.status_code, [200, 201])  # Too vague!
        
        # Test 3: Verify test database isolation
        self.assertTrue(database_url.endswith('test.db'), 
                       f"Must use test database, got: {database_url}")
        
        # Test 4: Verify no memory database usage (QA policy)
        self.assertNotIn(':memory:', database_url, 
                        "QA policy violation: :memory: databases forbidden in tests")

    def test_branch_coverage_critical_paths(self):
        """Test critical code paths for ≥70% branch coverage."""
        # Test all major branches in create_feature
        
        # Branch 1: New feature creation
        feature_data = {"title": f"Coverage Test 1 {uuid.uuid4()}"}
        response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(response.status_code, 200)
        
        # Branch 2: Existing feature (idempotency)
        response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(response.status_code, 200)
        
        # Branch 3: Feature with intent
        feature_with_intent = {"title": f"Coverage Test 2 {uuid.uuid4()}", "intent": {"key": "value"}}
        response = self.client.post("/api/v1/orchestrator/features", json=feature_with_intent)
        self.assertEqual(response.status_code, 200)
        
        # Branch 4: Feature without intent
        feature_no_intent = {"title": f"Coverage Test 3 {uuid.uuid4()}"}
        response = self.client.post("/api/v1/orchestrator/features", json=feature_no_intent)
        self.assertEqual(response.status_code, 200)
        
        # Test plan endpoint branches
        feature_id = response.json()["id"]
        
        # Branch 1: Valid planning
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        self.assertEqual(response.status_code, 200)
        
        # Branch 2: Invalid status for planning
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        self.assertEqual(response.status_code, 400)
        
        # Branch 3: Non-existent feature
        response = self.client.post("/api/v1/orchestrator/features/99999/plan")
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()