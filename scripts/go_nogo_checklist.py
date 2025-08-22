#!/usr/bin/env python3
"""
Go/No-Go чек-лист для TEST окружения Feature Factory
Проверяет готовность контура TEST к работе без ручных костылей
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
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
TEST_URL = "https://etl-tst.chococraft.ru"
BASIC_AUTH = ("admin", "password")
CORRELATION_ID = str(uuid.uuid4())

class GoNoGoChecker:
    def __init__(self):
        self.results = {}
        self.session = requests.Session()
        self.session.auth = BASIC_AUTH
        self.session.timeout = 30
        
    def log_event(self, event, **kwargs):
        """Логирование событий"""
        log_data = {
            "ts": datetime.utcnow().isoformat(),
            "env": "TEST", 
            "component": "go_nogo_checker",
            "correlation_id": CORRELATION_ID,
            "event": event,
            **kwargs
        }
        logger.info(f"{event}: {json.dumps(log_data, ensure_ascii=False)}")
    
    def check_https_setup(self):
        """Проверка HTTPS настроек (E10)"""
        print("🔒 Проверка HTTPS настроек...")
        
        try:
            # Проверка health endpoint
            response = requests.get(f"{TEST_URL}/api/v1/health", timeout=10)
            
            checks = {
                "status_200": response.status_code == 200,
                "https_enabled": TEST_URL.startswith('https://'),
                "hsts_header": 'strict-transport-security' in response.headers,
                "correlation_id": 'x-correlation-id' in response.headers,
                "x_frame_options": 'x-frame-options' in response.headers
            }
            
            # Проверка 401 без авторизации на защищённых endpoint'ах
            auth_response = requests.get(f"{TEST_URL}/api/v1/orchestrator/features", timeout=10)
            checks["auth_required"] = auth_response.status_code == 401
            
            self.results["https"] = {
                "status": "✅ PASS" if all(checks.values()) else "❌ FAIL",
                "checks": checks,
                "details": {
                    "url": TEST_URL,
                    "health_status": response.status_code,
                    "hsts_value": response.headers.get('strict-transport-security', 'отсутствует'),
                    "correlation_id": response.headers.get('x-correlation-id', 'отсутствует')
                }
            }
            
            self.log_event("https_check_completed", **checks)
            
        except Exception as e:
            self.results["https"] = {
                "status": "❌ FAIL",
                "error": str(e)
            }
            self.log_event("https_check_failed", error=str(e))
    
    def check_api_endpoints(self):
        """Проверка API endpoints"""
        print("🌐 Проверка API endpoints...")
        
        endpoints = [
            ("GET", "/api/v1/health", False),  # public
            ("GET", "/api/v1/orchestrator/features", True),  # protected
            ("GET", "/api/v1/logs", True),  # protected
        ]
        
        results = {}
        
        for method, endpoint, needs_auth in endpoints:
            try:
                if needs_auth:
                    response = self.session.request(method, f"{TEST_URL}{endpoint}")
                else:
                    response = requests.request(method, f"{TEST_URL}{endpoint}", timeout=10)
                
                results[endpoint] = {
                    "status_code": response.status_code,
                    "success": response.status_code in [200, 401, 405],  # 405 для неправильного метода это ок
                    "correlation_id": response.headers.get('x-correlation-id')
                }
                
            except Exception as e:
                results[endpoint] = {
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
        
        all_good = all(r["success"] for r in results.values())
        
        self.results["api_endpoints"] = {
            "status": "✅ PASS" if all_good else "❌ FAIL",
            "endpoints": results
        }
        
        self.log_event("api_endpoints_check_completed", 
                      endpoints_checked=len(endpoints),
                      all_successful=all_good)
    
    def check_orchestrator_api(self):
        """Проверка API оркестратора"""
        print("🎼 Проверка Orchestrator API...")
        
        try:
            # Тестовая фича
            feature_payload = {
                "title": f"Go/No-Go Test Feature {datetime.utcnow().strftime('%H:%M:%S')}",
                "intent": {
                    "action": "test_nogo", 
                    "params": {
                        "description": "Test feature for Go/No-Go checklist",
                        "correlation_id": CORRELATION_ID
                    }
                }
            }
            
            # POST /features
            create_response = self.session.post(
                f"{TEST_URL}/api/v1/orchestrator/features",
                json=feature_payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if create_response.status_code != 200:
                raise Exception(f"Feature creation failed: {create_response.status_code} {create_response.text}")
            
            feature_data = create_response.json()
            feature_id = feature_data['id']
            
            # POST /plan
            plan_response = self.session.post(f"{TEST_URL}/api/v1/orchestrator/features/{feature_id}/plan")
            
            if plan_response.status_code != 200:
                raise Exception(f"Feature planning failed: {plan_response.status_code} {plan_response.text}")
            
            plan_data = plan_response.json()
            
            # POST /run
            run_response = self.session.post(f"{TEST_URL}/api/v1/orchestrator/features/{feature_id}/run")
            
            if run_response.status_code != 200:
                raise Exception(f"Feature run failed: {run_response.status_code} {run_response.text}")
            
            run_data = run_response.json()
            run_id = run_data['run_id']
            
            # GET /status (несколько попыток)
            status_checks = []
            for i in range(3):
                time.sleep(2)
                status_response = self.session.get(f"{TEST_URL}/api/v1/orchestrator/graph/{run_id}/status")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status_checks.append({
                        "attempt": i + 1,
                        "status": status_data.get('status', 'UNKNOWN'),
                        "response": status_data
                    })
                else:
                    status_checks.append({
                        "attempt": i + 1,
                        "status": "ERROR",
                        "status_code": status_response.status_code
                    })
            
            self.results["orchestrator_api"] = {
                "status": "✅ PASS",
                "feature_id": feature_id,
                "run_id": run_id,
                "operations": {
                    "create": {"status_code": create_response.status_code, "success": True},
                    "plan": {"status_code": plan_response.status_code, "tasks": len(plan_data.get('tasks', []))},
                    "run": {"status_code": run_response.status_code, "state": run_data.get('state')},
                    "status_checks": status_checks
                }
            }
            
            self.log_event("orchestrator_api_check_completed",
                          feature_id=feature_id,
                          run_id=run_id,
                          operations_successful=True)
            
        except Exception as e:
            self.results["orchestrator_api"] = {
                "status": "❌ FAIL",
                "error": str(e)
            }
            self.log_event("orchestrator_api_check_failed", error=str(e))
    
    def check_logs_and_correlation(self):
        """Проверка логирования и correlation ID"""
        print("📋 Проверка логирования...")
        
        try:
            # Проверка logs endpoint
            logs_response = self.session.get(f"{TEST_URL}/api/v1/logs?limit=10")
            
            if logs_response.status_code != 200:
                raise Exception(f"Logs endpoint failed: {logs_response.status_code}")
            
            logs_data = logs_response.json()
            
            # Проверка структуры логов
            log_checks = {
                "logs_available": len(logs_data.get('logs', [])) > 0,
                "json_format": True,  # предполагаем, если API вернул JSON
                "correlation_ids": False
            }
            
            # Поиск correlation_id в логах
            for log_entry in logs_data.get('logs', [])[:5]:
                if isinstance(log_entry, dict) and 'correlation_id' in log_entry:
                    log_checks["correlation_ids"] = True
                    break
            
            self.results["logging"] = {
                "status": "✅ PASS" if all(log_checks.values()) else "⚠️ PARTIAL",
                "checks": log_checks,
                "sample_logs": logs_data.get('logs', [])[:3]
            }
            
            self.log_event("logging_check_completed", **log_checks)
            
        except Exception as e:
            self.results["logging"] = {
                "status": "❌ FAIL", 
                "error": str(e)
            }
            self.log_event("logging_check_failed", error=str(e))
    
    def generate_summary(self):
        """Генерация итогового отчёта"""
        print("\n" + "="*60)
        print("📋 ИТОГИ GO/NO-GO ЧЕКИСТА TEST ОКРУЖЕНИЯ")
        print("="*60)
        
        overall_status = "GO ✅"
        failed_checks = []
        
        for check_name, result in self.results.items():
            status = result.get("status", "❌ FAIL")
            print(f"{check_name.upper():<20} {status}")
            
            if "FAIL" in status:
                overall_status = "NO-GO ❌"
                failed_checks.append(check_name)
            elif "PARTIAL" in status:
                overall_status = "CONDITIONAL GO ⚠️"
        
        print("="*60)
        print(f"ИТОГОВОЕ РЕШЕНИЕ: {overall_status}")
        
        if failed_checks:
            print(f"\nТребуют исправления: {', '.join(failed_checks)}")
        
        print("\n📊 Детальные результаты:")
        print(json.dumps(self.results, indent=2, ensure_ascii=False))
        
        self.log_event("go_nogo_check_completed",
                      overall_status=overall_status,
                      failed_checks=failed_checks,
                      total_checks=len(self.results))
        
        return overall_status, self.results
    
    def run_full_check(self):
        """Запуск полной проверки"""
        print("🚀 Запуск Go/No-Go чек-листа для TEST окружения")
        print(f"🔗 URL: {TEST_URL}")
        print(f"🆔 Correlation ID: {CORRELATION_ID}")
        print(f"⏰ Время: {datetime.utcnow().isoformat()}")
        print()
        
        self.log_event("go_nogo_check_started", test_url=TEST_URL)
        
        # Выполнение всех проверок
        self.check_https_setup()
        self.check_api_endpoints()
        self.check_orchestrator_api()
        self.check_logs_and_correlation()
        
        # Генерация итогов
        overall_status, results = self.generate_summary()
        
        return overall_status == "GO ✅", results

def main():
    """Основная функция"""
    checker = GoNoGoChecker()
    success, results = checker.run_full_check()
    
    # Сохранение результатов
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_file = f"go_nogo_results_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": CORRELATION_ID,
            "test_url": TEST_URL,
            "overall_success": success,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результаты сохранены в: {report_file}")
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()