import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


class TestStreamAPI(unittest.TestCase):
    """Тесты для API stream, соответствующего спецификации UI-000.md."""

    @classmethod
    def setUpClass(cls):
        """Подготовка перед всеми тестами."""
        # Создаем клиент для тестирования
        cls.client = TestClient(app)

    def test_stream_events_endpoint_exists(self):
        """Тест наличия эндпоинта stream events."""
        # Проверяем, что маршрут существует
        routes = [route.path for route in app.routes]
        self.assertIn("/api/v1/stream/events", routes, "Route /api/v1/stream/events should exist")


class TestLogsAPI(unittest.TestCase):
    """Тесты для API logs, соответствующего спецификации UI-000.md."""

    @classmethod
    def setUpClass(cls):
        """Подготовка перед всеми тестами."""
        # Создаем клиент для тестирования
        cls.client = TestClient(app)

    def test_get_logs_tail_success(self):
        """Тест успешного получения логов."""
        # Отправляем GET запрос
        response = self.client.get("/api/v1/logs/tail")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIsInstance(response_data, list)
        
        # Проверяем, что каждая запись имеет необходимые поля
        if len(response_data) > 0:
            log_entry = response_data[0]
            self.assertIn("ts", log_entry)
            self.assertIn("level", log_entry)
            self.assertIn("env", log_entry)
            self.assertIn("component", log_entry)
            self.assertIn("agent_role", log_entry)
            self.assertIn("run_id", log_entry)
            self.assertIn("task_id", log_entry)
            self.assertIn("correlation_id", log_entry)
            self.assertIn("event", log_entry)
            self.assertIn("kv", log_entry)

    def test_get_logs_tail_with_limit(self):
        """Тест получения логов с ограничением количества."""
        # Отправляем GET запрос с limit=10
        response = self.client.get("/api/v1/logs/tail?limit=10")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIsInstance(response_data, list)
        self.assertLessEqual(len(response_data), 10)

    def test_get_logs_tail_with_filters(self):
        """Тест получения логов с фильтрами."""
        # Отправляем GET запрос с фильтрами
        response = self.client.get("/api/v1/logs/tail?component=orchestrator&level=INFO&event=job_started&agent_role=Orchestrator")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIsInstance(response_data, list)

    def test_get_logs_tail_invalid_limit(self):
        """Тест получения логов с некорректным limit."""
        # Отправляем GET запрос с отрицательным limit
        response = self.client.get("/api/v1/logs/tail?limit=-1")
        
        # Проверяем статус ответа (валидация Pydantic должна вернуть 422)
        self.assertEqual(response.status_code, 422)

    def test_api_routes_exist(self):
        """Тест наличия всех маршрутов API."""
        # Проверяем, что маршруты существуют
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/api/v1/logs/tail"
        ]
        
        for route in expected_routes:
            self.assertIn(route, routes, f"Route {route} should exist")


class TestTokensAPI(unittest.TestCase):
    """Тесты для API tokens, соответствующего спецификации UI-000.md."""

    @classmethod
    def setUpClass(cls):
        """Подготовка перед всеми тестами."""
        # Создаем клиент для тестирования
        cls.client = TestClient(app)

    def test_get_token_usage_success(self):
        """Тест успешного получения статистики токенов."""
        # Отправляем GET запрос
        response = self.client.get("/admin/tokens")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIsInstance(response_data, list)
        
        # Проверяем, что каждая запись имеет необходимые поля
        if len(response_data) > 0:
            token_entry = response_data[0]
            self.assertIn("role", token_entry)
            self.assertIn("model", token_entry)
            self.assertIn("input_tokens", token_entry)
            self.assertIn("output_tokens", token_entry)
            self.assertIn("total_tokens", token_entry)
            self.assertIn("cost", token_entry)

    def test_api_routes_exist(self):
        """Тест наличия всех маршрутов API."""
        # Проверяем, что маршруты существуют
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/admin/tokens"
        ]
        
        for route in expected_routes:
            self.assertIn(route, routes, f"Route {route} should exist")


if __name__ == '__main__':
    unittest.main()