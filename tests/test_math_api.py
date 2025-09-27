import unittest
import json
from fastapi.testclient import TestClient
from app.main import app


class TestMathAPI(unittest.TestCase):
    """Tests for Math operations API endpoint."""

    @classmethod
    def setUpClass(cls):
        """Setup before all tests."""
        cls.client = TestClient(app)

    def test_math_add_operation(self):
        """Test successful addition operation."""
        payload = {
            "operation": "add",
            "num1": 5,
            "num2": 3
        }
        response = self.client.post("/api/v1/math", json=payload)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        
        response_data = response.json()
        self.assertEqual(response_data["operation"], "add")
        self.assertEqual(response_data["num1"], 5)
        self.assertEqual(response_data["num2"], 3)
        self.assertEqual(response_data["result"], 8)

    def test_math_subtract_operation(self):
        """Test successful subtraction operation."""
        payload = {
            "operation": "subtract",
            "num1": 10,
            "num2": 4
        }
        response = self.client.post("/api/v1/math", json=payload)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["operation"], "subtract")
        self.assertEqual(response_data["result"], 6)

    def test_math_multiply_operation(self):
        """Test successful multiplication operation."""
        payload = {
            "operation": "multiply",
            "num1": 7,
            "num2": 6
        }
        response = self.client.post("/api/v1/math", json=payload)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["operation"], "multiply")
        self.assertEqual(response_data["result"], 42)

    def test_math_divide_operation(self):
        """Test successful division operation."""
        payload = {
            "operation": "divide",
            "num1": 15,
            "num2": 3
        }
        response = self.client.post("/api/v1/math", json=payload)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["operation"], "divide")
        self.assertEqual(response_data["result"], 5.0)

    def test_math_divide_by_zero_error(self):
        """Test division by zero returns 400 error."""
        payload = {
            "operation": "divide",
            "num1": 10,
            "num2": 0
        }
        response = self.client.post("/api/v1/math", json=payload)
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data["detail"], "Division by zero is not allowed")

    def test_math_invalid_operation(self):
        """Test invalid operation returns 422 error."""
        payload = {
            "operation": "invalid_operation",
            "num1": 5,
            "num2": 3
        }
        response = self.client.post("/api/v1/math", json=payload)
        
        self.assertEqual(response.status_code, 422)  # Validation error

    def test_math_missing_fields(self):
        """Test missing required fields returns 422 error."""
        payload = {
            "operation": "add",
            "num1": 5
            # Missing num2
        }
        response = self.client.post("/api/v1/math", json=payload)
        
        self.assertEqual(response.status_code, 422)

    def test_math_invalid_number_types(self):
        """Test invalid number types returns 422 error."""
        payload = {
            "operation": "add",
            "num1": "not_a_number",
            "num2": 3
        }
        response = self.client.post("/api/v1/math", json=payload)
        
        self.assertEqual(response.status_code, 422)

    def test_math_float_numbers(self):
        """Test operations with float numbers."""
        payload = {
            "operation": "add",
            "num1": 3.5,
            "num2": 2.2
        }
        response = self.client.post("/api/v1/math", json=payload)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertAlmostEqual(response_data["result"], 5.7, places=1)

    def test_math_negative_numbers(self):
        """Test operations with negative numbers."""
        payload = {
            "operation": "multiply",
            "num1": -5,
            "num2": 3
        }
        response = self.client.post("/api/v1/math", json=payload)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["result"], -15)

    def test_math_get_method_not_allowed(self):
        """Test that GET method is not allowed on math endpoint."""
        response = self.client.get("/api/v1/math")
        self.assertEqual(response.status_code, 405)  # Method Not Allowed


if __name__ == "__main__":
    unittest.main()