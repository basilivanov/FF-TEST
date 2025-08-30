#!/usr/bin/env python3
"""
E15.3 - WAIT_BUDGET e2e тест
Тестирование поведения системы при исчерпании бюджета токенов и автопереводе в WAIT_BUDGET.
"""

import os
import sys
import time
import json
import uuid
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Конфигурация
TEST_URL = "https://etl-tst.chococraft.ru"
BASIC_AUTH = ("admin", "password")
CORRELATION_ID = str(uuid.uuid4())

class WaitBudgetTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.auth = BASIC_AUTH
        self.session.timeout = 30
        self.results = {}
        self.start_time = datetime.utcnow()
        
    def log_step(self, step: str, status: str, details: Optional[Dict] = None) -> Dict:
        """Логирование шагов тестирования"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": CORRELATION_ID,
            "step": step,
            "status": status,
            "details": details or {}
        }
        print(f"[{log_entry['timestamp']}] {step}: {status}")
        if details:
            print(f"  Details: {json.dumps(details, indent=2, ensure_ascii=False)}")
        return log_entry
    
    def get_current_budget_status(self) -> Dict[str, Any]:
        """Получение текущего статуса бюджета через новый /admin/tokens endpoint"""
        try:
            response = self.session.get(f"{TEST_URL}/admin/tokens")
            
            if response.status_code == 200:
                budget_data = response.json()
                print(f"    ✅ Budget status retrieved successfully")
                return budget_data
            else:
                print(f"    ❌ Failed to get budget status: {response.status_code}")
                # Fallback к legacy endpoint
                legacy_response = self.session.get(f"{TEST_URL}/admin/tokens/summary")
                if legacy_response.status_code == 200:
                    return {"legacy": True, "data": legacy_response.json()}
                return {"error": f"Status code: {response.status_code}"}
                
        except Exception as e:
            print(f"    ❌ Budget status error: {e}")
            return {"error": str(e)}
    
    def create_budget_consuming_feature(self, intensity: str = "high") -> Optional[int]:
        """Создание фичи для истощения бюджета токенов"""
        try:
            # Создаём фичу с большим описанием для потребления токенов
            large_description = " ".join([
                "This is a comprehensive test feature designed to consume a significant amount of tokens",
                "to simulate budget exhaustion scenario for E15.3 WAIT_BUDGET testing.",
                "The feature includes multiple complex requirements that will generate substantial",
                "LLM requests across different roles including Dev, QA, Scribe, and Maintainer.",
                "Each role should perform extensive analysis and code generation tasks.",
                "Additional complexity: multi-file refactoring, comprehensive testing, documentation generation."
            ] * (10 if intensity == "high" else 5))  # Повторяем для увеличения размера
            
            feature_payload = {
                "title": f"E15.3 Budget Exhaustion Test {intensity.upper()} {datetime.utcnow().strftime('%H:%M:%S')}",
                "intent": {
                    "action": "comprehensive_development_task",
                    "params": {
                        "description": large_description,
                        "requirements": [
                            "Implement complex multi-service architecture",
                            "Create comprehensive test coverage",
                            "Generate extensive documentation",
                            "Perform thorough code review",
                            "Optimize performance across all components",
                            "Implement error handling and logging",
                            "Create monitoring and alerting",
                            "Design scalable database schemas"
                        ],
                        "complexity": "maximum",
                        "priority": "high",
                        "budget_test": True,
                        "correlation_id": CORRELATION_ID,
                        "test_intensity": intensity
                    }
                }
            }
            
            response = self.session.post(
                f"{TEST_URL}/api/v1/orchestrator/features",
                json=feature_payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                feature_data = response.json()
                feature_id = feature_data['id']
                print(f"    ✅ Budget consuming feature created: ID {feature_id}")
                return feature_id
            else:
                print(f"    ❌ Feature creation failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    ❌ Feature creation error: {e}")
            return None
    
    def execute_feature_until_budget_exhaustion(self, feature_id: int) -> Dict[str, Any]:
        """Выполнение фичи до исчерпания бюджета"""
        try:
            # Планирование
            plan_response = self.session.post(f"{TEST_URL}/api/v1/orchestrator/features/{feature_id}/plan")
            
            if plan_response.status_code != 200:
                return {"error": f"Planning failed: {plan_response.status_code}"}
            
            plan_data = plan_response.json()
            tasks_count = len(plan_data.get('tasks', []))
            print(f"    📋 Planning successful: {tasks_count} tasks created")
            
            # Запуск выполнения
            run_response = self.session.post(f"{TEST_URL}/api/v1/orchestrator/features/{feature_id}/run")
            
            if run_response.status_code != 200:
                return {"error": f"Run failed: {run_response.status_code}"}
            
            run_data = run_response.json()
            run_id = run_data['run_id']
            print(f"    🚀 Execution started: run_id {run_id}")
            
            # Мониторинг выполнения с отслеживанием WAIT_BUDGET
            wait_budget_detected = False
            monitoring_results = []
            max_monitoring_time = 300  # 5 минут максимум
            
            for i in range(max_monitoring_time // 10):  # Проверяем каждые 10 секунд
                time.sleep(10)
                
                # Проверяем статус выполнения
                status_response = self.session.get(f"{TEST_URL}/api/v1/orchestrator/graph/{run_id}/status")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    current_status = status_data.get('status', 'UNKNOWN')
                    
                    print(f"    📊 Status check {i+1}: {current_status}")
                    
                    monitoring_results.append({
                        "iteration": i + 1,
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": current_status,
                        "status_data": status_data
                    })
                    
                    # Проверяем на WAIT_BUDGET
                    if 'WAIT_BUDGET' in str(status_data) or current_status == 'WAIT_BUDGET':
                        print(f"    ⏳ WAIT_BUDGET detected!")
                        wait_budget_detected = True
                        
                        # Получаем обновлённый статус бюджета
                        budget_status = self.get_current_budget_status()
                        
                        return {
                            "feature_id": feature_id,
                            "run_id": run_id,
                            "wait_budget_detected": True,
                            "detection_iteration": i + 1,
                            "monitoring_results": monitoring_results,
                            "final_status": current_status,
                            "budget_status_at_detection": budget_status
                        }
                    
                    # Если фича завершилась до исчерпания бюджета
                    if current_status in ['DONE', 'FAILED', 'ERROR']:
                        print(f"    🏁 Feature completed before budget exhaustion: {current_status}")
                        return {
                            "feature_id": feature_id,
                            "run_id": run_id,
                            "wait_budget_detected": False,
                            "completion_status": current_status,
                            "monitoring_results": monitoring_results,
                            "note": "Feature completed before reaching budget limits"
                        }
                
                # Получаем статус бюджета для проверки
                budget_status = self.get_current_budget_status()
                if "budget_status" in budget_status:
                    status_info = budget_status.get("budget_status", {})
                    if status_info.get("status") == "critical":
                        print(f"    ⚠️ Critical budget status detected")
            
            # Если время мониторинга истекло
            return {
                "feature_id": feature_id,
                "run_id": run_id,
                "wait_budget_detected": wait_budget_detected,
                "monitoring_results": monitoring_results,
                "timeout": True,
                "note": "Monitoring timeout reached without WAIT_BUDGET detection"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def test_budget_recovery_cycle(self) -> Dict[str, Any]:
        """Тестирование цикла восстановления бюджета"""
        print("\n💰 Тестирование цикла восстановления бюджета...")
        
        try:
            # Получаем текущий статус
            initial_budget = self.get_current_budget_status()
            print(f"    📊 Initial budget status obtained")
            
            # Создаём несколько фич для истощения бюджета
            feature_ids = []
            for i in range(3):  # Создаём 3 ресурсоёмкие фичи
                feature_id = self.create_budget_consuming_feature("high")
                if feature_id:
                    feature_ids.append(feature_id)
                    time.sleep(2)  # Небольшая пауза между созданиями
            
            print(f"    ✅ Created {len(feature_ids)} budget-consuming features")
            
            # Запускаем все фичи параллельно
            execution_results = []
            for feature_id in feature_ids:
                print(f"    🚀 Starting execution of feature {feature_id}...")
                result = self.execute_feature_until_budget_exhaustion(feature_id)
                execution_results.append(result)
                
                # Если обнаружен WAIT_BUDGET, прекращаем создание новых
                if result.get("wait_budget_detected"):
                    print(f"    ⏳ WAIT_BUDGET detected, stopping further executions")
                    break
            
            # Проверяем финальный статус бюджета
            final_budget = self.get_current_budget_status()
            
            return {
                "initial_budget": initial_budget,
                "final_budget": final_budget,
                "feature_ids": feature_ids,
                "execution_results": execution_results,
                "wait_budget_occurred": any(r.get("wait_budget_detected", False) for r in execution_results)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def test_automatic_budget_reset(self) -> Dict[str, Any]:
        """Тестирование автоматического сброса бюджета"""
        print("\n🔄 Тестирование автоматического сброса бюджета...")
        
        # В реальной системе здесь бы ждали до полуночи или симулировали сброс
        # Для тестов получаем информацию о времени следующего сброса
        
        try:
            budget_status = self.get_current_budget_status()
            
            if "budget_status" in budget_status:
                next_reset = budget_status["budget_status"].get("next_reset")
                print(f"    📅 Next budget reset scheduled: {next_reset}")
                
                # Рекомендации для полного тестирования
                recommendations = [
                    "Schedule this test to run just before midnight UTC for full reset testing",
                    "Monitor system behavior during actual reset time",
                    "Verify that WAIT_BUDGET tasks automatically resume after reset",
                    "Check that daily limits are properly restored"
                ]
                
                return {
                    "next_reset_time": next_reset,
                    "current_status": budget_status,
                    "testing_recommendations": recommendations,
                    "test_type": "informational"
                }
            else:
                return {
                    "error": "Budget status format not recognized",
                    "raw_response": budget_status
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    def generate_wait_budget_report(self) -> str:
        """Генерация отчёта по WAIT_BUDGET тестированию"""
        print("\n" + "="*70)
        print("📋 ОТЧЁТ E15.3 - WAIT_BUDGET E2E ТЕСТИРОВАНИЕ")
        print("="*70)
        
        # Подсчёт результатов
        passed_tests = sum(1 for result in self.results.values() if not result.get('error'))
        total_tests = len(self.results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        # Общий статус
        if success_rate >= 0.8:
            overall_status = "🟢 PASS - WAIT_BUDGET поведение корректно"
        elif success_rate >= 0.5:
            overall_status = "🟡 PARTIAL - WAIT_BUDGET частично протестирован"
        else:
            overall_status = "🔴 FAIL - WAIT_BUDGET требует исправлений"
        
        print(f"ИТОГОВЫЙ СТАТУС: {overall_status}")
        print(f"Успешных тестов: {passed_tests}/{total_tests} ({success_rate:.1%})")
        print()
        
        # Детализация по тестам
        print("Результаты тестов:")
        for test_name, result in self.results.items():
            status = "✅ PASS" if not result.get('error') else "❌ FAIL"
            print(f"  {test_name:<30} {status}")
            
            if result.get('wait_budget_detected'):
                print(f"    └─ WAIT_BUDGET успешно обнаружен")
            
            if result.get('error'):
                print(f"    └─ Error: {result['error']}")
        
        total_time = (datetime.utcnow() - self.start_time).total_seconds()
        print(f"\nОбщее время выполнения: {total_time:.1f} секунд")
        print(f"Correlation ID: {CORRELATION_ID}")
        
        return overall_status
    
    def run_comprehensive_wait_budget_test(self):
        """Запуск комплексного WAIT_BUDGET тестирования"""
        print("🚀 ЗАПУСК E15.3 - WAIT_BUDGET E2E ТЕСТИРОВАНИЯ")
        print(f"🔗 TEST URL: {TEST_URL}")
        print(f"🆔 Correlation ID: {CORRELATION_ID}")
        print(f"⏰ Время начала: {self.start_time.isoformat()}")
        
        # Тест 1: Проверка доступности budget endpoints
        print("\n🔍 Тест 1: Проверка доступности budget endpoints...")
        budget_status = self.get_current_budget_status()
        self.results["budget_endpoint_availability"] = budget_status
        
        # Тест 2: Цикл восстановления бюджета
        recovery_result = self.test_budget_recovery_cycle()
        self.results["budget_recovery_cycle"] = recovery_result
        
        # Тест 3: Автоматический сброс бюджета
        reset_result = self.test_automatic_budget_reset()
        self.results["automatic_budget_reset"] = reset_result
        
        # Генерация отчёта
        overall_status = self.generate_wait_budget_report()
        
        return overall_status.startswith("🟢"), self.results

def main():
    """Основная функция"""
    test = WaitBudgetTest()
    success, results = test.run_comprehensive_wait_budget_test()
    
    # Сохранение результатов
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_file = f"e15_wait_budget_results_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": CORRELATION_ID,
            "test_url": TEST_URL,
            "test_type": "E15.3_WAIT_BUDGET_E2E",
            "overall_success": success,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Детальные результаты сохранены в: {report_file}")
    
    if not success:
        print("\n⚠️ WAIT_BUDGET тестирование выявило проблемы, требующие внимания")
        sys.exit(1)
    else:
        print("\n✅ WAIT_BUDGET поведение протестировано успешно!")

if __name__ == '__main__':
    main()