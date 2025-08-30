#!/usr/bin/env python3
"""
E2E тест для полного пайплайна hello-e2e:
POST /features → plan → run → Dev→Gate→QA→Scribe→Apply
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
import time
import sqlite3
from pathlib import Path
from typing import Dict, Any, List

# Добавляем корневую директорию проекта в Python path
sys.path.insert(0, '/opt/feature-factory')

from fastapi.testclient import TestClient
from app.main import app
from app.db.guard import get_db_connection_string

class TestE2EHelloFullPipeline(unittest.TestCase):
    """E2E тест для полного пайплайна hello-e2e."""
    
    @classmethod
    def setUpClass(cls):
        """Настройка класса тестов."""
        # Создаем временную директорию для тестовой БД
        cls.test_db_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.test_db_dir, "test.db")
        
        # Устанавливаем переменную окружения для тестовой БД
        os.environ["DATABASE_URL"] = f"sqlite:///{cls.test_db_path}"
        
        # Инициализируем БД
        cls._init_test_database()
        
        # Переопределяем get_db dependency для тестов
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.db.session import get_db
        
        test_engine = create_engine(f"sqlite:///{cls.test_db_path}")
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        def override_get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Создаем тестовый клиент
        cls.client = TestClient(app)
        
        # Создаем временную директорию для tmp файлов
        cls.test_tmp_dir = tempfile.mkdtemp()
        # Переопределяем tmp директорию для тестов
        os.environ["TMP_DIR"] = cls.test_tmp_dir
    
    @classmethod
    def tearDownClass(cls):
        """Очистка после тестов."""
        # Очищаем переопределения зависимостей
        app.dependency_overrides.clear()
        
        # Удаляем временные директории
        if os.path.exists(cls.test_db_dir):
            shutil.rmtree(cls.test_db_dir)
        if os.path.exists(cls.test_tmp_dir):
            shutil.rmtree(cls.test_tmp_dir)
    
    @classmethod
    def _init_test_database(cls):
        """Инициализирует тестовую базу данных."""
        with sqlite3.connect(cls.test_db_path) as conn:
            # Создаем таблицы
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature_id TEXT UNIQUE,
                    title TEXT NOT NULL,
                    intent_json TEXT,
                    status TEXT NOT NULL DEFAULT 'NEW',
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'API',
                    env TEXT NOT NULL DEFAULT 'test',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE,
                    feature_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    dsl_json TEXT,
                    status TEXT NOT NULL DEFAULT 'NEW',
                    attempts INTEGER DEFAULT 0,
                    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP,
                    package_contract TEXT,
                    capsule_hash TEXT,
                    budget_tokens INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (feature_id) REFERENCES features (id)
                );
                
                CREATE TABLE IF NOT EXISTS graph_runs (
                    run_id TEXT PRIMARY KEY,
                    feature_id INTEGER NOT NULL,
                    graph_name TEXT NOT NULL DEFAULT 'G1',
                    thread_id TEXT,
                    state_json TEXT,
                    status TEXT NOT NULL DEFAULT 'RUNNING',
                    env TEXT,
                    last_checkpoint_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (feature_id) REFERENCES features (id)
                );
                
                CREATE TABLE IF NOT EXISTS packages (
                    package_id TEXT PRIMARY KEY,
                    package_contract TEXT NOT NULL,
                    file_paths TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS doc_index (
                    doc_id TEXT PRIMARY KEY,
                    package_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (package_id) REFERENCES packages (package_id)
                );
            """)
            conn.commit()
    
    def setUp(self):
        """Настройка для каждого теста."""
        # Очищаем БД перед каждым тестом
        with sqlite3.connect(self.test_db_path) as conn:
            conn.execute("DELETE FROM doc_index")
            conn.execute("DELETE FROM packages")
            conn.execute("DELETE FROM graph_runs")
            conn.execute("DELETE FROM tasks")
            conn.execute("DELETE FROM features")
            conn.commit()
        
        # Очищаем tmp директорию
        if os.path.exists(self.test_tmp_dir):
            shutil.rmtree(self.test_tmp_dir)
        os.makedirs(self.test_tmp_dir, exist_ok=True)
    
    def test_full_hello_e2e_pipeline(self):
        """
        Тест полного пайплайна hello-e2e:
        1. POST /features с title="hello-e2e"
        2. plan → создается ≥1 Dev-задача  
        3. run → запускается граф Dev→Gate→QA→Scribe→Apply
        4. Проверяем: artifact_manifest применен, события в логах, status=DONE
        """
        
        # Устанавливаем переменные окружения для тестового режима
        original_env = os.environ.copy()
        os.environ["TEST_MODE"] = "true"
        
        try:
            # === ШАГ 1: POST /features ===
            feature_data = {
                "title": "hello-e2e",
                "description": "Test feature for e2e pipeline verification",
                "autostart": False  # Отключаем автостарт для контролируемого тестирования
            }
            
            response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
            self.assertEqual(response.status_code, 200, f"Features endpoint failed: {response.text}")
            
            feature_result = response.json()
            self.assertIn("id", feature_result)
            feature_id = feature_result["id"]
            
            # Проверяем, что feature создан в БД
            with sqlite3.connect(self.test_db_path) as conn:
                cursor = conn.execute(
                    "SELECT title, status FROM features WHERE id = ?", 
                    (feature_id,)
                )
                row = cursor.fetchone()
                self.assertIsNotNone(row, "Feature not found in database")
                self.assertEqual(row[0], "hello-e2e")
                self.assertEqual(row[1], "NEW")
            
            # === ШАГ 2: POST /plan ===
            response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
            self.assertEqual(response.status_code, 200, f"Plan endpoint failed: {response.text}")
            
            plan_result = response.json()
            self.assertIn("tasks", plan_result)
            
            # Проверяем, что создалась ≥1 Dev-задача
            dev_tasks = [task for task in plan_result["tasks"] if task["role"] == "Dev"]
            self.assertGreaterEqual(len(dev_tasks), 1, "No Dev tasks created by plan")
            
            # Проверяем задачи в БД
            with sqlite3.connect(self.test_db_path) as conn:
                cursor = conn.execute(
                    "SELECT task_id, role, package_contract FROM tasks WHERE feature_id = ?", 
                    (feature_id,)
                )
                db_tasks = cursor.fetchall()
                self.assertGreaterEqual(len(db_tasks), 1, "No tasks found in database")
                
                # Проверяем, что есть Dev задача
                dev_db_tasks = [task for task in db_tasks if task[1] == "Dev"]
                self.assertGreaterEqual(len(dev_db_tasks), 1, "No Dev tasks in database")
            
            # === ШАГ 3: POST /run ===
            response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/run")
            self.assertEqual(response.status_code, 200, f"Run endpoint failed: {response.text}")
            
            run_result = response.json()
            self.assertIn("run_id", run_result)
            run_id = run_result["run_id"]
            
            # Проверяем, что graph_run создан в БД
            with sqlite3.connect(self.test_db_path) as conn:
                cursor = conn.execute(
                    "SELECT status FROM graph_runs WHERE run_id = ?", 
                    (run_id,)
                )
                row = cursor.fetchone()
                self.assertIsNotNone(row, "Graph run not found in database")
                self.assertEqual(row[0], "RUNNING")
            
            # === ШАГ 4: GET /status и ожидание завершения ===
            max_wait_time = 60  # Максимум 60 секунд ожидания
            start_time = time.time()
            final_status = None
            
            while time.time() - start_time < max_wait_time:
                response = self.client.get(f"/api/v1/orchestrator/graph/{run_id}/status")
                self.assertEqual(response.status_code, 200, f"Status endpoint failed: {response.text}")
                
                status_result = response.json()
                feature_status = status_result.get("feature_status")
                
                if feature_status == "DONE":
                    final_status = status_result
                    break
                elif feature_status in ["ERROR", "FAILED"]:
                    self.fail(f"Feature processing failed with status: {feature_status}")
                
                time.sleep(2)  # Ждем 2 секунды перед следующей проверкой
            
            self.assertIsNotNone(final_status, f"Feature did not complete within {max_wait_time} seconds")
            self.assertEqual(final_status["feature_status"], "DONE")
            
            # === ШАГ 5: Проверяем применение artifact_manifest ===
            # Ищем созданные файлы в tmp/{run_id}/
            run_tmp_dir = os.path.join(self.test_tmp_dir, run_id)
            self.assertTrue(os.path.exists(run_tmp_dir), f"Run directory not found: {run_tmp_dir}")
            
            # Проверяем наличие ожидаемых файлов (main.py, __init__.py)
            expected_files = ["main.py", "__init__.py"]
            for expected_file in expected_files:
                file_path = os.path.join(run_tmp_dir, expected_file)
                self.assertTrue(os.path.exists(file_path), f"Expected file not found: {expected_file}")
            
            # Проверяем содержимое main.py
            main_py_path = os.path.join(run_tmp_dir, "main.py")
            with open(main_py_path, 'r') as f:
                main_content = f.read()
            self.assertIn("Hello from hello-e2e", main_content, "main.py does not contain expected content")
            
            # === ШАГ 6: Проверяем пакет в БД ===
            with sqlite3.connect(self.test_db_path) as conn:
                cursor = conn.execute(
                    "SELECT package_id, package_contract, file_paths FROM packages"
                )
                packages = cursor.fetchall()
                self.assertGreaterEqual(len(packages), 1, "No packages found in database")
                
                # Проверяем contract пакета
                package_contract = json.loads(packages[0][1])
                self.assertEqual(package_contract["package_id"], "PKG-HELLO-E2E-v1")
                self.assertEqual(package_contract["summary"], "Simple hello-e2e implementation")
            
            # === ШАГ 7: Проверяем индексирование документации ===
            with sqlite3.connect(self.test_db_path) as conn:
                cursor = conn.execute(
                    "SELECT doc_id, title, content FROM doc_index"
                )
                docs = cursor.fetchall()
                self.assertGreaterEqual(len(docs), 1, "No documents found in index")
                
                # Проверяем, что документация содержит ожидаемый контент
                doc_content = docs[0][2]
                self.assertIn("hello-e2e", doc_content.lower(), "Documentation does not mention hello-e2e")
            
            # === ШАГ 8: Финальная проверка статуса feature ===
            with sqlite3.connect(self.test_db_path) as conn:
                cursor = conn.execute(
                    "SELECT status FROM features WHERE id = ?", 
                    (feature_id,)
                )
                row = cursor.fetchone()
                self.assertIsNotNone(row, "Feature not found in final check")
                self.assertEqual(row[0], "DONE", "Feature status is not DONE")
        
        finally:
            # Восстанавливаем переменные окружения
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_stub_llm_provider_works(self):
        """Тест что stub LLM провайдер работает корректно."""
        # Импортируем router после установки переменных окружения
        from app.llm.router import completion
        
        # Устанавливаем тестовый режим
        os.environ["TEST_MODE"] = "true"
        
        try:
            # Тестируем вызов stub провайдера для роли test_Dev
            messages = [
                {"role": "system", "content": "Generate hello-e2e package"},
                {"role": "user", "content": "Create a simple hello world package"}
            ]
            
            result = completion(
                role="test_Dev",
                messages=messages,
                max_tokens=1000,
                temperature=0.1
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn("text", result)
            self.assertIn("model", result)
            self.assertEqual(result["model"], "stub-1.0")
            self.assertIn("hello-e2e", result["text"])
            
        finally:
            # Очищаем переменную окружения
            if "TEST_MODE" in os.environ:
                del os.environ["TEST_MODE"]


if __name__ == "__main__":
    unittest.main()