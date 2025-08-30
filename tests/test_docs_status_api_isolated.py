#!/usr/bin/env python3
"""
Isolated tests for docs status API endpoints.
Uses only test environment with mocked database.
"""

import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from datetime import datetime
import jsonschema

# Add project root to Python path
import sys
sys.path.append(str(Path(__file__).parent.parent))

# Import before setting up test client to avoid import conflicts
from app.api.docs_status import router
from fastapi import FastAPI

class TestDocsStatusAPIIsolated:
    """Isolated test suite for docs status API endpoints."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        # Create temporary database
        cls.temp_db_fd, cls.temp_db_path = tempfile.mkstemp(suffix='.db')
        cls.database_url = f"sqlite:///{cls.temp_db_path}"
        
        # Create isolated test app
        cls.app = FastAPI()
        cls.app.include_router(router)
        
        # Create test client
        cls.client = TestClient(cls.app)
        
        # Create database engine
        cls.engine = create_engine(cls.database_url)
        
        # Create tables
        with cls.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS doc_registry (
                    doc_name TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """))
            conn.commit()
        
        # Load JSON schemas
        schema_path = Path(__file__).parent / "schemas" / "docs_status.json"
        with open(schema_path) as f:
            cls.schemas = json.load(f)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test environment."""
        os.close(cls.temp_db_fd)
        os.unlink(cls.temp_db_path)
    
    def validate_json_schema(self, response_data, schema_name):
        """Validate response against JSON schema."""
        # Create a complete schema with definitions included
        full_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            **self.schemas["definitions"][schema_name],
            "definitions": self.schemas["definitions"]
        }
        jsonschema.validate(response_data, full_schema)
    
    @patch.dict(os.environ, clear=True)
    def test_get_docs_status_empty_registry(self):
        """Test GET /api/v1/docs/status with empty registry returns 200 with empty list."""
        # Set test database URL in environment
        os.environ["DATABASE_URL"] = self.database_url
        
        # Clear any existing data
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM doc_registry"))
            conn.commit()
        
        response = self.client.get("/api/v1/docs/status")
        
        assert response.status_code == 200
        data = response.json()
        self.validate_json_schema(data, "DocsStatusResponse")
        assert data["docs"] == []
    
    @patch.dict(os.environ, clear=True)
    def test_get_docs_status_with_data(self):
        """Test GET /api/v1/docs/status returns 200 with valid data."""
        # Set test database URL in environment
        os.environ["DATABASE_URL"] = self.database_url
        
        # Insert test data
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT OR REPLACE INTO doc_registry (doc_name, version, content_hash, updated_at)
                VALUES 
                    ('docs/Architecture.md', '1.0.0', 'abc123def456', '2025-08-22T10:00:00'),
                    ('docs/Schema.md', '1.1.0', 'def456ghi789', '2025-08-22T11:00:00')
            """))
            conn.commit()
        
        response = self.client.get("/api/v1/docs/status")
        
        # Strict status code check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Validate JSON structure
        data = response.json()
        self.validate_json_schema(data, "DocsStatusResponse")
        
        # Verify content
        assert len(data["docs"]) == 2
        
        # Check documents (order may vary)
        doc_names = [doc["doc_name"] for doc in data["docs"]]
        assert "docs/Architecture.md" in doc_names
        assert "docs/Schema.md" in doc_names
    
    @patch.dict(os.environ, clear=True)
    def test_post_rebuild_docs_success(self):
        """Test POST /api/v1/docs/rebuild returns 200 and updates documents."""
        # Set test database URL in environment
        os.environ["DATABASE_URL"] = self.database_url
        
        # Clear existing data and insert fresh test data
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM doc_registry"))
            conn.execute(text("""
                INSERT INTO doc_registry (doc_name, version, content_hash, updated_at)
                VALUES 
                    ('docs/test1.md', '1.0.0', 'old_hash_1', '2025-08-22T10:00:00'),
                    ('docs/test2.md', '1.1.0', 'old_hash_2', '2025-08-22T11:00:00')
            """))
            conn.commit()
        
        response = self.client.post("/api/v1/docs/rebuild")
        
        # Strict status code check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Validate JSON structure
        data = response.json()
        self.validate_json_schema(data, "RebuildResponse")
        
        # Verify response content
        assert data["status"] == "success"
        assert "rebuilt successfully" in data["message"]
        assert data["docs_updated"] == 2
    
    def test_nonexistent_endpoint_returns_404(self):
        """Test that non-existent endpoints return 404, not 500."""
        response = self.client.get("/api/v1/docs/nonexistent")
        
        # Strict status code check - must be 404, not 500
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        response2 = self.client.post("/api/v1/docs/invalid")
        assert response2.status_code == 404, f"Expected 404, got {response2.status_code}"
    
    def test_invalid_http_methods_return_405(self):
        """Test that invalid HTTP methods return 405, not 500."""
        # POST to GET-only endpoint
        response = self.client.post("/api/v1/docs/status")
        assert response.status_code == 405, f"Expected 405, got {response.status_code}"
        
        # GET to POST-only endpoint  
        response2 = self.client.get("/api/v1/docs/rebuild")
        assert response2.status_code == 405, f"Expected 405, got {response2.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])