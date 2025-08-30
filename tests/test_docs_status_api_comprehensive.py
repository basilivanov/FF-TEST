#!/usr/bin/env python3
"""
Comprehensive tests for docs status API endpoints.
Tests all positive and negative scenarios with strict status code validation.
"""

import os
import json
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from datetime import datetime
import jsonschema

# Add project root to Python path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.main import app

class TestDocsStatusAPI:
    """Test suite for docs status API endpoints."""
    
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
            
            # Insert test data
            conn.execute(text("""
                INSERT INTO doc_registry (doc_name, version, content_hash, updated_at)
                VALUES 
                    ('docs/Architecture.md', '1.0.0', 'abc123def456', '2025-08-22T10:00:00'),
                    ('docs/Schema-000-base-tables.md', '1.1.0', 'def456ghi789', '2025-08-22T11:00:00')
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
    
    def test_get_docs_status_success(self):
        """Test GET /api/v1/docs/status returns 200 with valid data."""
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
        assert "docs/Schema-000-base-tables.md" in doc_names
        
        # Find and check specific document
        arch_doc = next(d for d in data["docs"] if d["doc_name"] == "docs/Architecture.md")
        assert arch_doc["version"] == "1.0.0"
    
    def test_get_docs_status_empty_registry(self):
        """Test GET /api/v1/docs/status with empty doc_registry returns 200 with empty list."""
        # Clear the table
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM doc_registry"))
            conn.commit()
        
        response = self.client.get("/api/v1/docs/status")
        
        assert response.status_code == 200
        data = response.json()
        self.validate_json_schema(data, "DocsStatusResponse")
        # Should return empty list when registry is empty
        assert len(data["docs"]) == 0
        
        # Restore test data
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO doc_registry (doc_name, version, content_hash, updated_at)
                VALUES 
                    ('docs/Architecture.md', '1.0.0', 'abc123def456', '2025-08-22T10:00:00'),
                    ('docs/Schema-000-base-tables.md', '1.1.0', 'def456ghi789', '2025-08-22T11:00:00')
            """))
            conn.commit()
    
    def test_post_rebuild_docs_success(self):
        """Test POST /api/v1/docs/rebuild returns 200 and updates documents."""
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
    
    def test_post_rebuild_docs_empty_registry(self):
        """Test POST /api/v1/docs/rebuild with empty registry returns 200."""
        # Clear the table
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM doc_registry"))
            conn.commit()
        
        response = self.client.post("/api/v1/docs/rebuild")
        
        assert response.status_code == 200
        data = response.json()
        self.validate_json_schema(data, "RebuildResponse")
        assert data["status"] == "success"
        # Note: docs_updated may not be 0 if files exist on disk
        assert data["docs_updated"] >= 0
        
        # Restore test data
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO doc_registry (doc_name, version, content_hash, updated_at)
                VALUES 
                    ('docs/Architecture.md', '1.0.0', 'abc123def456', '2025-08-22T10:00:00'),
                    ('docs/Schema-000-base-tables.md', '1.1.0', 'def456ghi789', '2025-08-22T11:00:00')
            """))
            conn.commit()
    
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
        
        # PUT/DELETE should return 405
        response3 = self.client.put("/api/v1/docs/status")
        assert response3.status_code == 405, f"Expected 405, got {response3.status_code}"
        
        response4 = self.client.delete("/api/v1/docs/rebuild")
        assert response4.status_code == 405, f"Expected 405, got {response4.status_code}"
    
    def test_correlation_id_handling(self):
        """Test that correlation IDs are properly handled."""
        correlation_id = "test-correlation-123"
        headers = {"x-correlation-id": correlation_id}
        
        response = self.client.get("/api/v1/docs/status", headers=headers)
        assert response.status_code == 200
        
        response2 = self.client.post("/api/v1/docs/rebuild", headers=headers)
        assert response2.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])