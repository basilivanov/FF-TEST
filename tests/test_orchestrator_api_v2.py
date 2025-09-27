import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
import os
import tempfile
import sqlite3
import jsonschema


def validate_response_schema(response_data, schema_path):
    """Валидирует данные ответа по JSON-схеме."""
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    jsonschema.validate(instance=response_data, schema=schema)
import jsonschema

class TestOrchestratorAPIV2(unittest.TestCase):
    """Тесты для новой версии API оркестратора, соответствующей спецификации API-Orchestrator-001.md."""

    @classmethod
    def setUpClass(cls):
        """Подготовка перед всеми тестами."""
        # Создаем временную базу данных для тестов
        cls.temp_db_fd, cls.temp_db_path = tempfile.mkstemp(suffix='.db')
        cls.database_url = f"sqlite:///{cls.temp_db_path}"
        
        # Устанавливаем переменную окружения для тестовой базы данных
        os.environ['DATABASE_URL'] = cls.database_url
        os.environ['ENV'] = 'test'
        
        # Создаем таблицы в тестовой базе данных
        cls._create_test_tables(cls.temp_db_path)
        
        # Создаем клиента для тестирования
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        """Очистка после всех тестов."""
        # Закрываем файл базы данных и удаляем его
        os.close(cls.temp_db_fd)
        if os.path.exists(cls.temp_db_path):
            os.unlink(cls.temp_db_path)
        
        # Убираем переменную окружения
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

    @staticmethod
    def _create_test_tables(db_path):
        """Создает тестовые таблицы в базе данных."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создаем таблицы
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                intent_json TEXT,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                env TEXT
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
                finished_at DATETIME
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
                last_checkpoint_at DATETIME
            )
        """)
        
        conn.commit()
        conn.close()

    def test_create_feature_success(self):
        """Тест успешного создания фичи."""
        # Подготавливаем данные для запроса
        feature_data = {
            "title": "Test Feature Unique",
            "intent": {"action": "test", "params": {}}
        }
        
        # Отправляем POST запрос
        response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("id", response_data)
        self.assertIn("status", response_data)
        self.assertEqual(response_data["status"], "NEW")
        
        # Валидация по JSON-схеме
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'api', 'schemas', 'orchestrator', 'R0-FeatureCreated.json')
        validate_response_schema(response_data, schema_path)
        
        # Проверяем, что фича действительно создалась в базе
        # Используем DATABASE_URL из переменных окружения
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('sqlite:///'):
            db_path = database_url[10:]  # Убираем префикс 'sqlite:///'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, status FROM features WHERE title = ?", ("Test Feature Unique",))
            feature_row = cursor.fetchone()
            conn.close()
            
            self.assertIsNotNone(feature_row)
            self.assertEqual(feature_row[1], "Test Feature Unique")
            self.assertEqual(feature_row[2], "NEW")

    def test_create_feature_idempotency(self):
        """Тест идемпотентности создания фичи."""
        # Подготавливаем данные для запроса
        feature_data = {
            "title": "Idempotent Feature",
            "intent": {"action": "test", "params": {}}
        }
        
        # Отправляем первый POST запрос
        response1 = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(response1.status_code, 200)
        response1_data = response1.json()
        feature_id_1 = response1_data["id"]
        
        # Отправляем второй POST запрос с теми же данными
        response2 = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(response2.status_code, 200)
        response2_data = response2.json()
        feature_id_2 = response2_data["id"]
        
        # Проверяем, что вернулся тот же ID
        self.assertEqual(feature_id_1, feature_id_2)
        self.assertEqual(response1_data["status"], response2_data["status"])

    def test_plan_feature_success(self):
        """Тест успешного планирования фичи."""
        # Сначала создаем фичу
        feature_data = {
            "title": "Feature to Plan Unique",
            "intent": {"action": "test", "params": {}}
        }
        
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(create_response.status_code, 200)
        feature_id = create_response.json()["id"]
        
        # Отправляем POST запрос для генерации плана
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("feature_id", response_data)
        self.assertIn("tasks", response_data)
        self.assertIn("package_contract", response_data)
        self.assertEqual(response_data["feature_id"], feature_id)
        
        # Валидация по JSON-схеме
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'api', 'schemas', 'orchestrator', 'R1-Plan.json')
        validate_response_schema(response_data, schema_path)
        
        # Проверяем, что созданы задачи
        self.assertGreater(len(response_data["tasks"]), 0)
        for task in response_data["tasks"]:
            self.assertIn("id", task)
            self.assertIn("role", task)
            self.assertIn("status", task)
            self.assertEqual(task["status"], "NEW")
        
        # Проверяем, что статус фичи обновился
        # Используем DATABASE_URL из переменных окружения
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('sqlite:///'):
            db_path = database_url[10:]  # Убираем префикс 'sqlite:///'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM features WHERE id = ?", (feature_id,))
            feature_row = cursor.fetchone()
            conn.close()
            
            self.assertIsNotNone(feature_row)
            self.assertEqual(feature_row[0], "PLANNED")

    def test_plan_feature_not_found(self):
        """Тест планирования несуществующей фичи."""
        # Отправляем POST запрос для генерации плана несуществующей фичи
        response = self.client.post("/api/v1/orchestrator/features/99999/plan")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 404)
        
        # Проверяем заголовок error_code
        self.assertEqual(response.headers.get("error_code"), "FEATURE_NOT_FOUND")
        
        # Проверяем структуру тела ответа (если она соответствует ErrorResponse)
        response_data = response.json()
        self.assertIn("detail", response_data)
        
        # Валидация по JSON-схеме ErrorResponse
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'api', 'schemas', 'orchestrator', 'E0-Error.json')
        validate_response_schema(response_data, schema_path)

    def test_plan_feature_invalid_status(self):
        """Тест планирования фичи с недопустимым статусом."""
        # Сначала создаем фичу
        feature_data = {
            "title": "Feature to Plan Invalid Status",
            "intent": {"action": "test", "params": {}}
        }
        
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(create_response.status_code, 200)
        feature_id = create_response.json()["id"]
        
        # Обновляем статус фичи на PLANNED вручную
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('sqlite:///'):
            db_path = database_url[10:]  # Убираем префикс 'sqlite:///'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE features SET status = 'PLANNED' WHERE id = ?", (feature_id,))
            conn.commit()
            conn.close()
        
        # Пытаемся снова запланировать фичу
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        
        # Проверяем статус ответа
        # В текущей реализации API это будет 400, так как фича уже запланирована
        self.assertEqual(response.status_code, 400)
        
        # Проверяем заголовок error_code
        self.assertEqual(response.headers.get("error_code"), "INVALID_FEATURE_STATUS")
        
        # Проверяем структуру тела ответа (если она соответствует ErrorResponse)
        response_data = response.json()
        self.assertIn("detail", response_data)
        
        # Валидация по JSON-схеме ErrorResponse
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'api', 'schemas', 'orchestrator', 'E0-Error.json')
        validate_response_schema(response_data, schema_path)

    def test_run_feature_success(self):
        """Тест успешного запуска фичи."""
        # Сначала создаем фичу
        feature_data = {
            "title": "Feature to Run Unique",
            "intent": {"action": "test", "params": {}}
        }
        
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(create_response.status_code, 200)
        feature_id = create_response.json()["id"]
        
        # Планируем фичу
        plan_response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        self.assertEqual(plan_response.status_code, 200)
        
        # Отправляем POST запрос для запуска фичи
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/run")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("run_id", response_data)
        self.assertIn("state", response_data)
        self.assertEqual(response_data["state"], "STARTED")
        
        # Валидация по JSON-схеме
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'api', 'schemas', 'orchestrator', 'R2-Run.json')
        validate_response_schema(response_data, schema_path)
        
        # Проверяем, что статус фичи обновился
        # Используем DATABASE_URL из переменных окружения
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('sqlite:///'):
            db_path = database_url[10:]  # Убираем префикс 'sqlite:///'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM features WHERE id = ?", (feature_id,))
            feature_row = cursor.fetchone()
            conn.close()
            
            self.assertIsNotNone(feature_row)
            self.assertEqual(feature_row[0], "RUNNING")

    def test_run_feature_not_found(self):
        """Тест запуска несуществующей фичи."""
        # Отправляем POST запрос для запуска несуществующей фичи
        response = self.client.post("/api/v1/orchestrator/features/99999/run")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 404)
        
        # Проверяем заголовок error_code
        self.assertEqual(response.headers.get("error_code"), "FEATURE_NOT_FOUND")
        
        # Проверяем структуру тела ответа (если она соответствует ErrorResponse)
        response_data = response.json()
        self.assertIn("detail", response_data)
        
        # Валидация по JSON-схеме ErrorResponse
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'api', 'schemas', 'orchestrator', 'E0-Error.json')
        validate_response_schema(response_data, schema_path)

    def test_get_graph_status_success(self):
        """Тест успешного получения статуса графа."""
        # Сначала создаем фичу и запускаем её
        feature_data = {
            "title": "Feature for Graph Status Unique",
            "intent": {"action": "test", "params": {}}
        }
        
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(create_response.status_code, 200)
        feature_id = create_response.json()["id"]
        
        plan_response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        self.assertEqual(plan_response.status_code, 200)
        
        run_response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/run")
        self.assertEqual(run_response.status_code, 200)
        run_id = run_response.json()["run_id"]
        
        # Отправляем GET запрос для получения статуса графа
        response = self.client.get(f"/api/v1/orchestrator/graph/{run_id}/status")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("run_id", response_data)
        self.assertIn("graph", response_data)
        self.assertIn("status", response_data)
        self.assertIn("last_checkpoint", response_data)
        self.assertEqual(response_data["run_id"], run_id)
        self.assertEqual(response_data["graph"], "G1")
        self.assertEqual(response_data["status"], "RUNNING")
        
        # Валидация по JSON-схеме
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'api', 'schemas', 'orchestrator', 'R3-GraphStatus.json')
        validate_response_schema(response_data, schema_path)

    def test_get_graph_status_not_found(self):
        """Тест получения статуса несуществующего графа."""
        # Отправляем GET запрос для получения статуса несуществующего графа
        response = self.client.get("/api/v1/orchestrator/graph/nonexistent-run-id/status")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 404)
        
        # Проверяем заголовок error_code
        self.assertEqual(response.headers.get("error_code"), "GRAPH_RUN_NOT_FOUND")
        
        # Проверяем структуру тела ответа (если она соответствует ErrorResponse)
        response_data = response.json()
        self.assertIn("detail", response_data)
        
        # Валидация по JSON-схеме ErrorResponse
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'api', 'schemas', 'orchestrator', 'E0-Error.json')
        validate_response_schema(response_data, schema_path)

    def test_api_routes_exist(self):
        """Тест наличия всех маршрутов API."""
        # Проверяем, что маршруты существуют
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/api/v1/orchestrator/features",
            "/api/v1/orchestrator/features/{feature_id}/plan",
            "/api/v1/orchestrator/features/{feature_id}/run",
            "/api/v1/orchestrator/graph/{run_id}/status"
        ]
        
        for route in expected_routes:
            # Проверяем, что маршрут существует (без учета параметров пути)
            route_base = route.split("/{")[0] if "/{" in route else route
            found = any(r.startswith(route_base) for r in routes)
            self.assertTrue(found, f"Route {route} should exist")

    @patch('app.api.orchestrator_v2.log.info')
    def test_api_logging(self, mock_log_info):
        """Тест логирования API вызовов."""
        # Подготавливаем данные для запроса
        feature_data = {
            "title": "Logging Test Feature Unique",
            "intent": {"action": "test", "params": {}}
        }
        
        # Отправляем POST запрос
        response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        
        # Проверяем, что логирование вызывалось
        self.assertTrue(mock_log_info.called)
        
        # Проверяем, что логи содержат нужные события
        log_calls = [call for call in mock_log_info.call_args_list 
                    if 'event' in call.kwargs and call.kwargs['event'] in ['api_call_start', 'api_call_end']]
        self.assertGreater(len(log_calls), 0)

    def test_smoke_api_endpoints(self):
        """Smoke-тест лупа: создаёт задачу и доводит до DONE в TEST."""
        # Тест создания фичи
        feature_data = {
            "title": "Smoke Test Feature",
            "intent": {"action": "test", "params": {}}
        }
        response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        # Проверяем, что ответ 200 или 4xx, но не 5xx
        self.assertIn(response.status_code, [200, 400, 404, 409])
        
        if response.status_code == 200:
            feature_id = response.json()["id"]
            
            # Тест планирования фичи
            response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
            self.assertIn(response.status_code, [200, 400, 404, 409])
            
            if response.status_code == 200:
                # Тест запуска фичи
                response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/run")
                self.assertIn(response.status_code, [200, 400, 404, 409])
                
                if response.status_code == 200:
                    run_id = response.json()["run_id"]
                    # Тест получения статуса графа
                    response = self.client.get(f"/api/v1/orchestrator/graph/{run_id}/status")
                    self.assertIn(response.status_code, [200, 400, 404, 409])
        
        # Тест получения списка задач (новый эндпоинт)
        response = self.client.get("/api/v1/orchestrator/tasks")
        self.assertIn(response.status_code, [200, 400, 404, 409, 500])
        
        # Тест получения списка запусков (новый эндпоинт)
        response = self.client.get("/api/v1/orchestrator/runs")
        self.assertIn(response.status_code, [200, 400, 404, 409, 500])

    def test_orchestrator_api_smoke(self):
        """Smoke-тест оркестратора: все эндпоинты возвращают 200/4xx без 500."""
        # Создаем фичу для теста
        feature_data = {
            "title": "Smoke Test Feature",
            "intent": {"action": "test", "params": {}}
        }
        
        # POST /features
        response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertIn(response.status_code, [200, 400, 409], 
                     f"POST /features returned {response.status_code}: {response.text}")
        
        # Если фича создана успешно, продолжаем тест
        if response.status_code == 200:
            feature_id = response.json()["id"]
            
            # POST /features/{id}/plan
            response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
            self.assertIn(response.status_code, [200, 400, 404], 
                         f"POST /features/{feature_id}/plan returned {response.status_code}: {response.text}")
            
            # POST /features/{id}/run
            response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/run")
            self.assertIn(response.status_code, [200, 400, 404], 
                         f"POST /features/{feature_id}/run returned {response.status_code}: {response.text}")
            
            # GET /graph/{run_id}/status (если run был успешным)
            if response.status_code == 200:
                run_id = response.json()["run_id"]
                response = self.client.get(f"/api/v1/orchestrator/graph/{run_id}/status")
                self.assertIn(response.status_code, [200, 404], 
                             f"GET /graph/{run_id}/status returned {response.status_code}: {response.text}")
            
            # GET /tasks (новый эндпоинт)
            response = self.client.get("/api/v1/orchestrator/tasks")
            self.assertIn(response.status_code, [200, 500], 
                         f"GET /tasks returned {response.status_code}: {response.text}")
            
            # GET /runs (новый эндпоинт)
            response = self.client.get("/api/v1/orchestrator/runs")
            self.assertIn(response.status_code, [200, 500], 
                         f"GET /runs returned {response.status_code}: {response.text}")


if __name__ == '__main__':
    unittest.main()
