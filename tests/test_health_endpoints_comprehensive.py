#!/usr/bin/env python3
"""
Comprehensive tests for health check endpoints.
Tests all three health endpoints with proper error handling.
"""

import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from unittest.mock import patch, MagicMock
import subprocess

# Add project root to Python path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.main import app

class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        # Create temporary database
        cls.temp_db_fd, cls.temp_db_path = tempfile.mkstemp(suffix='.db')
        cls.database_url = f"sqlite:///{cls.temp_db_path}"
        
        # Set environment variable for the test
        os.environ["DATABASE_URL"] = cls.database_url
        
        # Create test client
        cls.client = TestClient(app)
        
        # Create database engine
        cls.engine = create_engine(cls.database_url)
        
        # Create alembic_version table for migration checks
        with cls.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL PRIMARY KEY
                )
            """))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('abc123')"))
            conn.commit()
    
    @classmethod
    def teardown_class(cls):
        """Clean up test environment."""
        os.close(cls.temp_db_fd)
        os.unlink(cls.temp_db_path)
    
    def test_health_live_always_returns_200(self):
        """Test GET /health/live always returns 200."""
        response = self.client.get("/health/live")
        
        # Strict status code check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Validate response structure
        data = response.json()
        assert data["status"] == "ok"
        assert data["component"] == "live"
    
    def test_health_ready_success_with_all_components_ok(self):
        """Test GET /health/ready returns 200 when all components are healthy."""
        # Create required index files for the test
        index_dir = Path("/opt/feature-factory/data")
        index_dir.mkdir(parents=True, exist_ok=True)
        
        # Create dummy index files
        test_files = ["code_registry.jsonl", "symbol_index.jsonl", "call_graph.dot"]
        created_files = []
        
        try:
            for file_name in test_files:
                file_path = index_dir / file_name
                file_path.write_text("test content")
                created_files.append(file_path)
            
            response = self.client.get("/health/ready")
            
            # Should return 200 when all components are healthy
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert data["status"] == "ok"
            assert data["component"] == "ready"
            assert "checks" in data
            assert len(data["checks"]) == 3  # database, migrations, index_files
            
            # All checks should be OK
            for check in data["checks"]:
                assert check["status"] == "ok"
                
        finally:
            # Clean up created files
            for file_path in created_files:
                try:
                    file_path.unlink()
                except FileNotFoundError:
                    pass
    
    def test_health_ready_failure_with_missing_index_files(self):
        """Test GET /health/ready returns 200 but error status when index files missing."""
        # Ensure index files don't exist
        index_dir = Path("/opt/feature-factory/data")
        test_files = ["code_registry.jsonl", "symbol_index.jsonl", "call_graph.dot"]
        
        for file_name in test_files:
            file_path = index_dir / file_name
            try:
                file_path.unlink()
            except FileNotFoundError:
                pass
        
        response = self.client.get("/health/ready")
        
        # Should still return 200 (endpoint accessible) but with error status
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["status"] == "error"
        assert data["component"] == "ready"
        
        # Find the index_files check
        index_check = next(check for check in data["checks"] if check["component"] == "index_files")
        assert index_check["status"] == "error"
        assert "missing" in index_check
    
    @patch('app.api.health.get_llm_providers')
    def test_health_deps_success_with_working_providers(self, mock_get_providers):
        """Test GET /health/deps returns 200 when providers are available."""
        # Mock providers configuration
        mock_get_providers.return_value = {
            "stub": {
                "cli_path": "python3",
                "config": {"cmd": ["python3", "-c", "print('test')"]}
            }
        }
        
        response = self.client.get("/health/deps")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["status"] == "ok"
        assert data["component"] == "deps"
        assert "checks" in data
        
        # Check LLM CLI component
        llm_check = data["checks"][0]
        assert llm_check["component"] == "llm_cli"
        assert llm_check["status"] == "ok"
        assert "providers" in llm_check
        assert llm_check["working_providers"] >= 1
    
    @patch('app.api.health.get_llm_providers')
    def test_health_deps_failure_with_no_providers(self, mock_get_providers):
        """Test GET /health/deps returns 200 but error status when no providers work."""
        # Mock providers with non-existent CLI paths
        mock_get_providers.return_value = {
            "nonexistent": {
                "cli_path": "nonexistent-cli-tool",
                "config": {"cmd": ["nonexistent-cli-tool"]}
            }
        }
        
        response = self.client.get("/health/deps")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["status"] == "error"
        assert data["component"] == "deps"
        
        # Check LLM CLI component shows error
        llm_check = data["checks"][0]
        assert llm_check["component"] == "llm_cli"
        assert llm_check["status"] == "error"
        assert llm_check["working_providers"] == 0
    
    def test_health_endpoints_never_return_500(self):
        """Test that health endpoints never return 500, even with errors."""
        # Test all three endpoints
        endpoints = ["/health/live", "/health/ready", "/health/deps"]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            
            # Must never return 500
            assert response.status_code != 500, f"Endpoint {endpoint} returned 500"
            
            # Should always return 200 for health endpoints
            assert response.status_code == 200, f"Expected 200 for {endpoint}, got {response.status_code}"
            
            # Should always have JSON response
            data = response.json()
            assert "status" in data
            assert "component" in data
    
    def test_health_endpoints_invalid_methods_return_405(self):
        """Test that invalid HTTP methods return 405."""
        endpoints = ["/health/live", "/health/ready", "/health/deps"]
        
        for endpoint in endpoints:
            # POST should return 405
            response = self.client.post(endpoint)
            assert response.status_code == 405, f"Expected 405 for POST {endpoint}"
            
            # PUT should return 405
            response = self.client.put(endpoint)
            assert response.status_code == 405, f"Expected 405 for PUT {endpoint}"
            
            # DELETE should return 405
            response = self.client.delete(endpoint)
            assert response.status_code == 405, f"Expected 405 for DELETE {endpoint}"


class TestHealthEndpointsE2ESmoke:
    """E2E smoke tests that check all three endpoints."""
    
    def setup_method(self):
        """Set up for each test method."""
        self.client = TestClient(app)
    
    def test_e2e_smoke_all_health_endpoints(self):
        """Smoke test that hits all three health endpoints and validates JSON."""
        endpoints = [
            ("/health/live", "live"),
            ("/health/ready", "ready"), 
            ("/health/deps", "deps")
        ]
        
        for endpoint, component in endpoints:
            response = self.client.get(endpoint)
            
            # Basic response validation
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
            
            data = response.json()
            assert data["component"] == component, f"Wrong component for {endpoint}"
            assert data["status"] in ["ok", "error"], f"Invalid status for {endpoint}"
            
            # Validate structure based on endpoint
            if component == "live":
                # Live endpoint is simple
                assert len(data) == 2  # status, component
                
            elif component in ["ready", "deps"]:
                # Ready and deps endpoints have checks
                assert "checks" in data, f"Missing checks in {endpoint}"
                assert isinstance(data["checks"], list), f"Checks not a list in {endpoint}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])