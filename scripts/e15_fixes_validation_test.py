#!/usr/bin/env python3
"""
E15-FIXES Validation Test
Валидация исправлений E15.1 (Admin Tokens 401) и E15.2 (Logs API 404)
"""

import os
import sys
import time
import json
import uuid
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Конфигурация
TEST_URL = "https://etl-tst.chococraft.ru"
BASIC_AUTH = ("admin", "password")
CORRELATION_ID = str(uuid.uuid4())

class E15FixesValidationTest:
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
    
    def validate_e15_1_admin_tokens_fix(self) -> Dict[str, Any]:
        """E15.1: Валидация исправления Admin Tokens 401 ошибки"""
        print("\\n🔧 E15.1: Валидация исправления Admin Tokens endpoint...")
        
        try:
            # Тестируем новый /admin/tokens endpoint с BasicAuth
            response = self.session.get(f"{TEST_URL}/admin/tokens")
            
            validation_result = {
                "endpoint": "/admin/tokens",
                "status_code": response.status_code,
                "has_basic_auth": True,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
            
            if response.status_code == 200:
                # Проверяем структуру ответа согласно R-TokensStats.json
                try:
                    data = response.json()
                    
                    # Проверяем обязательные поля из схемы
                    required_fields = ["date", "stats_by_role", "total_usage", "budget_status", "metadata"]
                    schema_compliance = all(field in data for field in required_fields)
                    
                    validation_result.update({
                        "response_valid_json": True,
                        "schema_compliant": schema_compliance,
                        "has_correlation_id": "correlation_id" in data.get("metadata", {}),
                        "roles_count": len(data.get("stats_by_role", {})),
                        "budget_status": data.get("budget_status", {}).get("status", "unknown"),
                        "total_usage": data.get("total_usage", {}),
                        "sample_response": {
                            "date": data.get("date"),
                            "budget_status": data.get("budget_status", {}).get("status"),
                            "total_limit": data.get("total_usage", {}).get("total_limit"),
                            "total_used": data.get("total_usage", {}).get("total_used")
                        }
                    })
                    
                    print(f"    ✅ Admin Tokens endpoint now returns 200 OK")
                    print(f"    ✅ Response follows R-TokensStats.json schema: {schema_compliance}")
                    print(f"    ✅ Found {len(data.get('stats_by_role', {}))} roles in statistics")
                    print(f"    ✅ Budget status: {data.get('budget_status', {}).get('status', 'unknown')}")
                    
                    self.results["e15_1_admin_tokens"] = self.log_step(
                        "E15.1 Admin Tokens Fix", 
                        "✅ FIXED", 
                        validation_result
                    )
                    
                    return validation_result
                    
                except json.JSONDecodeError:
                    validation_result.update({
                        "response_valid_json": False,
                        "error": "Invalid JSON response"
                    })
                    
            elif response.status_code == 401:
                print(f"    ❌ Still getting 401 Unauthorized - E15.1 fix not working")
                validation_result.update({
                    "error": "E15.1 fix incomplete - still returns 401",
                    "auth_header": response.headers.get("WWW-Authenticate"),
                    "response_text": response.text[:200]
                })
                
            else:
                print(f"    ❌ Unexpected status code: {response.status_code}")
                validation_result.update({
                    "error": f"Unexpected status code: {response.status_code}",
                    "response_text": response.text[:200]
                })
            
            self.results["e15_1_admin_tokens"] = self.log_step(
                "E15.1 Admin Tokens Fix", 
                "❌ NOT FIXED" if response.status_code != 200 else "✅ FIXED", 
                validation_result
            )
            
            return validation_result
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "endpoint": "/admin/tokens"
            }
            
            self.results["e15_1_admin_tokens"] = self.log_step(
                "E15.1 Admin Tokens Fix", 
                "❌ ERROR", 
                error_result
            )
            
            return error_result
    
    def validate_e15_2_logs_api_fix(self) -> Dict[str, Any]:
        """E15.2: Валидация исправления Logs API 404 ошибки"""
        print("\\n📋 E15.2: Валидация исправления Logs API endpoint...")
        
        try:
            # Тестируем новый /api/v1/logs endpoint
            response = self.session.get(f"{TEST_URL}/api/v1/logs")
            
            validation_result = {
                "endpoint": "/api/v1/logs",
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
            
            if response.status_code == 200:
                # Проверяем структуру ответа согласно R-Logs.json
                try:
                    data = response.json()
                    
                    # Проверяем обязательные поля из схемы
                    required_fields = ["logs", "pagination", "metadata"]
                    schema_compliance = all(field in data for field in required_fields)
                    
                    logs_count = len(data.get("logs", []))
                    
                    validation_result.update({
                        "response_valid_json": True,
                        "schema_compliant": schema_compliance,
                        "logs_count": logs_count,
                        "has_pagination": "pagination" in data,
                        "has_metadata": "metadata" in data,
                        "has_correlation_id": "correlation_id" in data.get("metadata", {}),
                        "pagination_info": data.get("pagination", {}),
                        "sample_log": data.get("logs", [{}])[0] if logs_count > 0 else None
                    })
                    
                    print(f"    ✅ Logs API endpoint now returns 200 OK")
                    print(f"    ✅ Response follows R-Logs.json schema: {schema_compliance}")
                    print(f"    ✅ Retrieved {logs_count} log entries")
                    print(f"    ✅ Pagination present: {validation_result['has_pagination']}")
                    
                    # Тестируем фильтрацию
                    filter_response = self.session.get(
                        f"{TEST_URL}/api/v1/logs",
                        params={"level": "INFO", "per_page": 10}
                    )
                    
                    if filter_response.status_code == 200:
                        filter_data = filter_response.json()
                        validation_result.update({
                            "filtering_works": True,
                            "filtered_logs_count": len(filter_data.get("logs", [])),
                            "filters_applied": filter_data.get("filters", {})
                        })
                        print(f"    ✅ Filtering works: retrieved {len(filter_data.get('logs', []))} INFO logs")
                    
                    self.results["e15_2_logs_api"] = self.log_step(
                        "E15.2 Logs API Fix", 
                        "✅ FIXED", 
                        validation_result
                    )
                    
                    return validation_result
                    
                except json.JSONDecodeError:
                    validation_result.update({
                        "response_valid_json": False,
                        "error": "Invalid JSON response"
                    })
                    
            elif response.status_code == 404:
                print(f"    ❌ Still getting 404 Not Found - E15.2 fix not working")
                validation_result.update({
                    "error": "E15.2 fix incomplete - still returns 404",
                    "response_text": response.text[:200]
                })
                
            else:
                print(f"    ❌ Unexpected status code: {response.status_code}")
                validation_result.update({
                    "error": f"Unexpected status code: {response.status_code}",
                    "response_text": response.text[:200]
                })
            
            self.results["e15_2_logs_api"] = self.log_step(
                "E15.2 Logs API Fix", 
                "❌ NOT FIXED" if response.status_code != 200 else "✅ FIXED", 
                validation_result
            )
            
            return validation_result
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "endpoint": "/api/v1/logs"
            }
            
            self.results["e15_2_logs_api"] = self.log_step(
                "E15.2 Logs API Fix", 
                "❌ ERROR", 
                error_result
            )
            
            return error_result
    
    def test_comprehensive_go_nogo_revalidation(self) -> Dict[str, Any]:
        """Повторная проверка критичных Go/No-Go тестов с учётом исправлений"""
        print("\\n🔍 Повторная проверка Go/No-Go критериев...")
        
        revalidation_results = {
            "admin_tokens_accessible": False,
            "logs_api_accessible": False,
            "basic_auth_working": False,
            "https_security": False,
            "correlation_tracking": False
        }
        
        try:
            # 1. Проверка доступности admin токенов
            admin_response = self.session.get(f"{TEST_URL}/admin/tokens")
            revalidation_results["admin_tokens_accessible"] = admin_response.status_code == 200
            
            # 2. Проверка доступности logs API
            logs_response = self.session.get(f"{TEST_URL}/api/v1/logs")
            revalidation_results["logs_api_accessible"] = logs_response.status_code == 200
            
            # 3. Проверка BasicAuth
            # Пробуем доступ без авторизации
            unauth_session = requests.Session()
            unauth_response = unauth_session.get(f"{TEST_URL}/admin/tokens")
            revalidation_results["basic_auth_working"] = unauth_response.status_code == 401
            
            # 4. Проверка HTTPS security headers
            health_response = self.session.get(f"{TEST_URL}/api/v1/health")
            security_headers = {
                "strict-transport-security": health_response.headers.get("strict-transport-security"),
                "x-correlation-id": health_response.headers.get("x-correlation-id")
            }
            revalidation_results["https_security"] = bool(security_headers["strict-transport-security"])
            revalidation_results["correlation_tracking"] = bool(security_headers["x-correlation-id"])
            
            # Подсчёт успешных проверок
            passed_checks = sum(1 for check in revalidation_results.values() if check)
            total_checks = len(revalidation_results)
            success_rate = passed_checks / total_checks
            
            overall_go_nogo_status = "GO" if success_rate >= 0.8 else "CONDITIONAL_GO" if success_rate >= 0.6 else "NO_GO"
            
            final_result = {
                "revalidation_results": revalidation_results,
                "passed_checks": passed_checks,
                "total_checks": total_checks,
                "success_rate": f"{success_rate:.1%}",
                "overall_status": overall_go_nogo_status,
                "security_headers": security_headers
            }
            
            print(f"    📊 Go/No-Go реvalidация: {passed_checks}/{total_checks} ({success_rate:.1%})")
            print(f"    🎯 Общий статус: {overall_go_nogo_status}")
            
            self.results["go_nogo_revalidation"] = self.log_step(
                "Go/No-Go Revalidation", 
                f"✅ {overall_go_nogo_status}", 
                final_result
            )
            
            return final_result
            
        except Exception as e:
            error_result = {"error": str(e)}
            self.results["go_nogo_revalidation"] = self.log_step(
                "Go/No-Go Revalidation", 
                "❌ ERROR", 
                error_result
            )
            return error_result
    
    def generate_e15_fixes_report(self) -> str:
        """Генерация отчёта по E15-FIXES валидации"""
        print("\\n" + "="*70)
        print("📋 ОТЧЁТ ВАЛИДАЦИИ E15-FIXES")
        print("="*70)
        
        # Анализ результатов
        e15_1_fixed = self.results.get("e15_1_admin_tokens", {}).get("status", "").startswith("✅")
        e15_2_fixed = self.results.get("e15_2_logs_api", {}).get("status", "").startswith("✅")
        go_nogo_status = self.results.get("go_nogo_revalidation", {}).get("details", {}).get("overall_status", "UNKNOWN")
        
        # Общий статус
        fixes_applied = sum([e15_1_fixed, e15_2_fixed])
        
        if fixes_applied == 2 and go_nogo_status == "GO":
            overall_status = "🟢 ALL FIXES VALIDATED - Ready for Production"
        elif fixes_applied >= 1 and go_nogo_status in ["GO", "CONDITIONAL_GO"]:
            overall_status = "🟡 PARTIAL FIXES - Minor issues remain"
        else:
            overall_status = "🔴 FIXES INCOMPLETE - Critical issues not resolved"
        
        print(f"ИТОГОВЫЙ СТАТУС: {overall_status}")
        print(f"Исправлено компонентов: {fixes_applied}/2")
        print(f"Go/No-Go статус: {go_nogo_status}")
        print()
        
        # Детализация по исправлениям
        print("Статус исправлений:")
        print(f"  E15.1 Admin Tokens 401    {'✅ FIXED' if e15_1_fixed else '❌ NOT FIXED'}")
        print(f"  E15.2 Logs API 404        {'✅ FIXED' if e15_2_fixed else '❌ NOT FIXED'}")
        print(f"  Go/No-Go Revalidation     ✅ {go_nogo_status}")
        
        # Рекомендации
        print("\\nРекомендации:")
        if not e15_1_fixed:
            print("  🔧 E15.1: Проверить BasicAuth в /admin/tokens endpoint")
        if not e15_2_fixed:
            print("  🔧 E15.2: Проверить регистрацию /api/v1/logs в main.py")
        if go_nogo_status == "CONDITIONAL_GO":
            print("  📋 Go/No-Go: Минорные проблемы требуют внимания перед продакшеном")
        if go_nogo_status == "NO_GO":
            print("  ⛔ Go/No-Go: Критические проблемы блокируют деплой")
            
        total_time = (datetime.utcnow() - self.start_time).total_seconds()
        print(f"\\nВремя валидации: {total_time:.1f} секунд")
        print(f"Correlation ID: {CORRELATION_ID}")
        
        return overall_status
    
    def run_e15_fixes_validation(self):
        """Запуск валидации исправлений E15-FIXES"""
        print("🚀 ЗАПУСК ВАЛИДАЦИИ E15-FIXES")
        print(f"🔗 TEST URL: {TEST_URL}")
        print(f"🆔 Correlation ID: {CORRELATION_ID}")
        print(f"⏰ Время начала: {self.start_time.isoformat()}")
        
        # Валидация E15.1
        self.validate_e15_1_admin_tokens_fix()
        
        # Валидация E15.2
        self.validate_e15_2_logs_api_fix()
        
        # Комплексная повторная проверка Go/No-Go
        self.test_comprehensive_go_nogo_revalidation()
        
        # Генерация отчёта
        overall_status = self.generate_e15_fixes_report()
        
        return overall_status.startswith("🟢"), self.results

def main():
    """Основная функция"""
    test = E15FixesValidationTest()
    success, results = test.run_e15_fixes_validation()
    
    # Сохранение результатов
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_file = f"e15_fixes_validation_results_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": CORRELATION_ID,
            "test_url": TEST_URL,
            "test_type": "E15_FIXES_VALIDATION",
            "overall_success": success,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\\n💾 Результаты валидации сохранены в: {report_file}")
    
    if success:
        print("\\n✅ E15-FIXES исправления успешно валидированы!")
    else:
        print("\\n⚠️ E15-FIXES валидация выявила проблемы, требующие внимания")
        sys.exit(1)

if __name__ == '__main__':
    main()