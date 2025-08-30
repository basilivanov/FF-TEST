import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
import os
import tempfile
import sqlite3


class TestMaintainerAPI(unittest.TestCase):
    """Тесты для API maintainer, соответствующего спецификации API-Maintainer-001.md."""

    @classmethod
    def setUpClass(cls):
        """Подготовка перед всеми тестами."""
        # Создаем клиент для тестирования
        cls.client = TestClient(app)

    def test_generate_intent_success(self):
        """Тест успешной генерации intent."""
        # Подготавливаем данные для запроса
        intent_data = {
            "nl_text": "Создай фичу для импорта данных из Excel"
        }
        
        # Отправляем POST запрос
        response = self.client.post("/api/v1/maintainer/intent", json=intent_data)
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("nl_text", response_data)
        self.assertIn("intent_json", response_data)
        self.assertIn("issues", response_data)
        self.assertIn("suggestions", response_data)
        self.assertEqual(response_data["nl_text"], intent_data["nl_text"])
        
        # Проверяем, что intent_json не пустой
        self.assertIsInstance(response_data["intent_json"], dict)
        self.assertGreater(len(response_data["intent_json"]), 0)

    def test_generate_intent_empty_text(self):
        """Тест генерации intent с пустым текстом."""
        # Подготавливаем данные для запроса
        intent_data = {
            "nl_text": ""
        }
        
        # Отправляем POST запрос
        response = self.client.post("/api/v1/maintainer/intent", json=intent_data)
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 400)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("error", response_data)
        self.assertEqual(response_data["error"], "EMPTY_NL_TEXT")

    def test_generate_intent_missing_text(self):
        """Тест генерации intent с отсутствующим текстом."""
        # Подготавливаем данные для запроса
        intent_data = {}
        
        # Отправляем POST запрос
        response = self.client.post("/api/v1/maintainer/intent", json=intent_data)
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 422)  # Валидация Pydantic

    def test_generate_plan_success(self):
        """Тест успешной генерации плана."""
        # Подготавливаем данные для запроса
        plan_data = {
            "intent_json": {
                "intent": "create_feature",
                "title": "Импорт данных из Excel",
                "description": "Создай фичу для импорта данных из Excel",
                "priority": 1
            }
        }
        
        # Отправляем POST запрос
        response = self.client.post("/api/v1/maintainer/plan", json=plan_data)
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("intent_json", response_data)
        self.assertIn("dag", response_data)
        self.assertIn("package_contract", response_data)
        self.assertEqual(response_data["intent_json"], plan_data["intent_json"])
        
        # Проверяем, что dag не пустой
        self.assertIsInstance(response_data["dag"], list)
        self.assertGreater(len(response_data["dag"]), 0)
        
        # Проверяем структуру задач в DAG
        for task in response_data["dag"]:
            self.assertIn("id", task)
            self.assertIn("name", task)
            self.assertIn("kind", task)
            self.assertIn("role", task)
            self.assertIn("preconditions", task)
            self.assertIn("postconditions", task)
            self.assertIn("idempotency_key", task)
            self.assertIn("retry", task)
            self.assertIn("deadline", task)
            self.assertIn("models", task)
            self.assertIn("outputs", task)
            self.assertIn("dod", task)
            self.assertIn("severity", task)

    def test_generate_plan_empty_intent(self):
        """Тест генерации плана с пустым intent."""
        # Подготавливаем данные для запроса
        plan_data = {
            "intent_json": {}
        }
        
        # Отправляем POST запрос
        response = self.client.post("/api/v1/maintainer/plan", json=plan_data)
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 400)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("error", response_data)
        self.assertEqual(response_data["error"], "EMPTY_INTENT_JSON")

    def test_generate_plan_missing_intent(self):
        """Тест генерации плана с отсутствующим intent."""
        # Подготавливаем данные для запроса
        plan_data = {}
        
        # Отправляем POST запрос
        response = self.client.post("/api/v1/maintainer/plan", json=plan_data)
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 422)  # Валидация Pydantic

    def test_api_routes_exist(self):
        """Тест наличия всех маршрутов API."""
        # Проверяем, что маршруты существуют
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/api/v1/maintainer/intent",
            "/api/v1/maintainer/plan"
        ]
        
        for route in expected_routes:
            self.assertIn(route, routes, f"Route {route} should exist")


if __name__ == '__main__':
    unittest.main()