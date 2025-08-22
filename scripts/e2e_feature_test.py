#!/usr/bin/env python3
"""
E2E Feature Test Script (E12-A)
Автоматический тест полного прогона фичи через систему Feature Factory
"""

import os
import sys
import time
import json
import uuid
import requests
from datetime import datetime
import structlog

# Настройка логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.LoggerFactory(),
    logger_factory=structlog.stdlib.LoggerFactory(),
    context_class=dict,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Конфигурация из переменных окружения
TEST_URL = os.getenv('TEST_URL', 'https://etl-tst.chococraft.ru')
BASIC_AUTH_USER = os.getenv('BASIC_AUTH_USER', 'admin')
BASIC_AUTH_PASS = os.getenv('BASIC_AUTH_PASS', 'password')
CORRELATION_ID = str(uuid.uuid4())

class E2EFeatureTest:
    def __init__(self):
        self.base_url = TEST_URL
        self.auth = (BASIC_AUTH_USER, BASIC_AUTH_PASS)
        self.session = requests.Session()
        self.feature_id = None
        self.run_id = None
        self.start_time = datetime.utcnow()
        
    def log_event(self, event, **kwargs):
        """Логирование событий согласно стандарту Logging-001"""
        logger.info(event, 
                   ts=datetime.utcnow().isoformat(),
                   env="TEST",
                   component="e2e_test",
                   agent_role="QA",
                   correlation_id=CORRELATION_ID,
                   **kwargs)
    
    def make_request(self, method, endpoint, **kwargs):
        """Выполнение HTTP запроса с обработкой ошибок"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, auth=self.auth, timeout=30, **kwargs)
            
            # Проверка на 5xx ошибки (критично по требованиям)
            if response.status_code >= 500:
                self.log_event("api_error_5xx", 
                              endpoint=endpoint, 
                              status_code=response.status_code,
                              response_text=response.text[:1000])
                raise Exception(f"5xx error on {endpoint}: {response.status_code}")
                
            return response
        except requests.exceptions.RequestException as e:
            self.log_event("api_request_failed", 
                          endpoint=endpoint,
                          error=str(e))
            raise
    
    def test_feature_creation(self):
        """Шаг 1: Создание фичи"""
        self.log_event("feature_creation_started")
        
        payload = {
            "title": f"E2E CI Test Feature {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "intent": {
                "action": "test_e2e_ci",
                "params": {
                    "description": "Automated E2E test feature for CI/CD pipeline",
                    "correlation_id": CORRELATION_ID
                }
            }
        }
        
        response = self.make_request('POST', '/api/v1/orchestrator/features', 
                                   headers={'Content-Type': 'application/json'},
                                   json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Feature creation failed: {response.status_code}")
            
        data = response.json()
        self.feature_id = data['id']
        
        self.log_event("feature_created", 
                      feature_id=self.feature_id,
                      status=data['status'])
        
        assert data['status'] == 'NEW', f"Expected status NEW, got {data['status']}"
        return True
    
    def test_feature_planning(self):
        """Шаг 2: Планирование фичи"""
        self.log_event("feature_planning_started", feature_id=self.feature_id)
        
        response = self.make_request('POST', f'/api/v1/orchestrator/features/{self.feature_id}/plan')
        
        if response.status_code != 200:
            raise Exception(f"Feature planning failed: {response.status_code}")
            
        data = response.json()
        
        self.log_event("feature_planned",
                      feature_id=self.feature_id,
                      tasks_count=len(data['tasks']))
        
        # Проверка структуры ответа
        assert 'tasks' in data, "Tasks not found in planning response"
        assert len(data['tasks']) > 0, "No tasks created during planning"
        assert 'package_contract' in data, "Package contract not found"
        
        # Проверка наличия Dev задачи
        dev_tasks = [t for t in data['tasks'] if t['role'] == 'Dev']
        assert len(dev_tasks) > 0, "No Dev tasks found"
        
        return True
    
    def test_feature_execution(self):
        """Шаг 3: Запуск графа выполнения"""
        self.log_event("feature_execution_started", feature_id=self.feature_id)
        
        response = self.make_request('POST', f'/api/v1/orchestrator/features/{self.feature_id}/run')
        
        if response.status_code != 200:
            raise Exception(f"Feature execution failed: {response.status_code}")
            
        data = response.json()
        self.run_id = data['run_id']
        
        self.log_event("feature_execution_launched",
                      feature_id=self.feature_id,
                      run_id=self.run_id,
                      state=data['state'])
        
        assert data['state'] == 'STARTED', f"Expected state STARTED, got {data['state']}"
        return True
    
    def test_execution_monitoring(self):
        """Шаг 4: Мониторинг выполнения до завершения"""
        self.log_event("execution_monitoring_started", 
                      feature_id=self.feature_id,
                      run_id=self.run_id)
        
        max_wait_time = 600  # 10 минут максимум
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = self.make_request('GET', f'/api/v1/orchestrator/graph/{self.run_id}/status')
            
            if response.status_code != 200:
                raise Exception(f"Status check failed: {response.status_code}")
                
            data = response.json()
            status = data.get('status', 'UNKNOWN')
            
            self.log_event("execution_status_check",
                          run_id=self.run_id,
                          status=status,
                          elapsed_time=int(time.time() - start_time))
            
            if status == 'DONE':
                self.log_event("execution_completed",
                              run_id=self.run_id,
                              total_time=int(time.time() - start_time))
                return True
            elif status == 'FAILED':
                raise Exception(f"Graph execution failed: {data}")
            elif status in ['RUNNING', 'STARTED']:
                time.sleep(10)  # Ждём 10 секунд
                continue
            else:
                raise Exception(f"Unknown status: {status}")
        
        raise Exception(f"Execution timeout after {max_wait_time} seconds")
    
    def test_feature_final_status(self):
        """Шаг 5: Проверка финального статуса фичи"""
        self.log_event("final_status_check_started", feature_id=self.feature_id)
        
        response = self.make_request('GET', f'/api/v1/orchestrator/features/{self.feature_id}')
        
        if response.status_code != 200:
            raise Exception(f"Final status check failed: {response.status_code}")
            
        data = response.json()
        status = data.get('status', 'UNKNOWN')
        
        self.log_event("final_status_checked",
                      feature_id=self.feature_id,
                      final_status=status)
        
        assert status == 'DONE', f"Expected final status DONE, got {status}"
        return True
    
    def run_test(self):
        """Запуск полного E2E теста"""
        try:
            self.log_event("e2e_feature_test_started")
            
            # Выполнение всех шагов
            self.test_feature_creation()
            self.test_feature_planning() 
            self.test_feature_execution()
            self.test_execution_monitoring()
            self.test_feature_final_status()
            
            total_time = (datetime.utcnow() - self.start_time).total_seconds()
            
            self.log_event("e2e_feature_test_completed",
                          feature_id=self.feature_id,
                          run_id=self.run_id,
                          total_time_seconds=total_time,
                          result="SUCCESS")
            
            print(f"✅ E2E Feature Test PASSED")
            print(f"   Feature ID: {self.feature_id}")
            print(f"   Run ID: {self.run_id}")
            print(f"   Total time: {total_time:.1f}s")
            return True
            
        except Exception as e:
            total_time = (datetime.utcnow() - self.start_time).total_seconds()
            
            self.log_event("e2e_feature_test_failed",
                          feature_id=self.feature_id,
                          run_id=self.run_id,
                          error=str(e),
                          total_time_seconds=total_time,
                          result="FAILURE")
            
            print(f"❌ E2E Feature Test FAILED: {e}")
            return False

def main():
    """Основная функция"""
    test = E2EFeatureTest()
    success = test.run_test()
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()