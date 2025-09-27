import unittest
import json
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime


class TestHelloAPI(unittest.TestCase):
    """Tests for Hello World API endpoint."""

    @classmethod
    def setUpClass(cls):
        """Setup before all tests."""
        cls.client = TestClient(app)

    def test_hello_endpoint_success(self):
        """Test successful Hello World response."""
        # Send GET request to /api/v1/hello
        response = self.client.get("/api/v1/hello")
        
        # Check response status code
        self.assertEqual(response.status_code, 200)
        
        # Check response content type
        self.assertEqual(response.headers["content-type"], "application/json")
        
        # Parse response JSON
        response_data = response.json()
        
        # Validate response structure
        self.assertIn("message", response_data)
        self.assertIn("timestamp", response_data)
        
        # Validate message content
        self.assertEqual(response_data["message"], "Hello World")
        
        # Validate timestamp format (ISO 8601 UTC format)
        timestamp = response_data["timestamp"]
        self.assertTrue(timestamp.endswith("+00:00"))
        
        # Parse timestamp to ensure it's valid ISO format
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp)
            self.assertIsInstance(parsed_timestamp, datetime)
            # Ensure it's in UTC
            self.assertEqual(parsed_timestamp.tzinfo.utcoffset(None).total_seconds(), 0)
        except ValueError:
            self.fail(f"Timestamp {timestamp} is not in valid ISO format")

    def test_hello_endpoint_returns_different_timestamps(self):
        """Test that consecutive calls return different timestamps."""
        # Make first request
        response1 = self.client.get("/api/v1/hello")
        timestamp1 = response1.json()["timestamp"]
        
        # Small delay to ensure different timestamp
        import time
        time.sleep(0.001)
        
        # Make second request
        response2 = self.client.get("/api/v1/hello")
        timestamp2 = response2.json()["timestamp"]
        
        # Timestamps should be different
        self.assertNotEqual(timestamp1, timestamp2)

    def test_hello_endpoint_method_not_allowed(self):
        """Test that POST method is not allowed on hello endpoint."""
        response = self.client.post("/api/v1/hello")
        self.assertEqual(response.status_code, 405)  # Method Not Allowed


if __name__ == "__main__":
    unittest.main()