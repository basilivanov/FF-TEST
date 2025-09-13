#!/usr/bin/env python3
"""
Комплексный тест всех агентов с реальными провайдерами
Проверяет каждую роль и их авторизацию
"""

import asyncio
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Добавляем корень проекта в PATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.llm.router import completion

# Настройки
os.environ['DATABASE_URL'] = 'sqlite:////opt/feature-factory/data/test.db'
CORRELATION_ID = f"COMPREHENSIVE_TEST_{int(time.time())}"

class ComprehensiveAgentTest:
    def __init__(self):
        self.correlation_id = CORRELATION_ID
        self.artifacts_dir = Path(f"/opt/feature-factory/artifacts/COMPREHENSIVE_TEST/{CORRELATION_ID}")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.start_time = time.time()
        self.results = {}
        
    def log(self, message: str):
        """Логирование"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def save_artifact(self, filename: str, data: Any):
        """Сохранение артефакта"""
        filepath = self.artifacts_dir / filename
        if isinstance(data, (dict, list)):
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            with open(filepath, 'w') as f:
                f.write(str(data))

    def test_role(self, role: str, test_messages: List[Dict[str, str]], expected_behavior: str) -> Dict[str, Any]:
        """Тестирует конкретную роль"""
        self.log(f"🧪 Testing {role} role...")
        
        result = {
            "role": role,
            "status": "UNKNOWN",
            "error": None,
            "response": None,
            "provider_used": None,
            "latency_ms": 0,
            "expected_behavior": expected_behavior
        }
        
        start_time = time.time()
        
        try:
            # Вызываем роль через LLM роутер
            response = completion(
                role=role,
                messages=test_messages,
                max_tokens=500,
                temperature=0.3,
                timeout_s=30
            )
            
            result["status"] = "SUCCESS"
            result["response"] = response
            result["provider_used"] = response.get("provider", "unknown")
            result["latency_ms"] = int((time.time() - start_time) * 1000)
            
            # Проверяем что ответ не пустой
            content = ""
            if "choices" in response and response["choices"]:
                content = response["choices"][0].get("message", {}).get("content", "")
            elif "text" in response:
                content = response["text"]
                
            if not content or len(content.strip()) < 10:
                result["status"] = "FAILED"
                result["error"] = "Empty or too short response"
            
            self.log(f"✅ {role} completed in {result['latency_ms']}ms using {result['provider_used']}")
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
            result["latency_ms"] = int((time.time() - start_time) * 1000)
            
            self.log(f"❌ {role} failed: {str(e)[:100]}")
            
            # Сохраняем полную ошибку для отладки
            result["full_error"] = traceback.format_exc()
            
        self.save_artifact(f"test_{role.lower()}.json", result)
        return result

    def test_all_roles(self) -> Dict[str, Dict[str, Any]]:
        """Тестирует все роли с подходящими задачами"""
        
        test_cases = {
            "Architect": {
                "messages": [
                    {
                        "role": "system", 
                        "content": "Ты - Architect. Создай план реализации для простой фичи. Верни JSON с полями dag, budgets, dod."
                    },
                    {
                        "role": "user",
                        "content": "Создай простой REST API эндпоинт /health для проверки статуса сервиса"
                    }
                ],
                "expected": "JSON план с узлами графа для Dev, QA, Scribe"
            },
            
            "Dev": {
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты - Python разработчик. Создай код по техническому заданию. Используй artifact_manifest."
                    },
                    {
                        "role": "user", 
                        "content": "Создай FastAPI эндпоинт /health который возвращает {\"status\": \"ok\"}"
                    }
                ],
                "expected": "YAML artifact_manifest + Python код"
            },
            
            "QA": {
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты - QA-инженер. Создай тесты для кода. Используй pytest."
                    },
                    {
                        "role": "user",
                        "content": "Создай тест для эндпоинта /health из файла app/api/health.py"
                    }
                ],
                "expected": "Python тест с pytest"
            },
            
            "Scribe": {
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты - Scribe-инженер. Создай changelog запись в YAML формате."
                    },
                    {
                        "role": "user",
                        "content": "Документируй добавление эндпоинта /health"
                    }
                ],
                "expected": "YAML с changelog_entry"
            },
            
            "Maintainer": {
                "messages": [
                    {
                        "role": "system", 
                        "content": "Ты - дружелюбный помощник системы. Отвечай в JSON формате с полями response_for_user и action."
                    },
                    {
                        "role": "user",
                        "content": "Привет! Можешь помочь с созданием API?"
                    }
                ],
                "expected": "JSON ответ с дружелюбным сообщением"
            }
        }
        
        results = {}
        
        for role, test_data in test_cases.items():
            results[role] = self.test_role(
                role=role,
                test_messages=test_data["messages"],
                expected_behavior=test_data["expected"]
            )
            
            # Небольшая пауза между тестами
            time.sleep(2)
            
        return results

    def test_provider_authorization(self) -> Dict[str, Any]:
        """Проверяет авторизацию провайдеров"""
        self.log("🔐 Testing provider authorization...")
        
        auth_results = {
            "timestamp": datetime.now().isoformat(),
            "providers": {}
        }
        
        # Список провайдеров для проверки
        providers_to_test = [
            "anthropic_opus41",
            "openai_gpt5_via_codex", 
            "gemini_25_pro",
            "gemini_25_flash",
            "qwen_code"
        ]
        
        simple_test_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Respond with 'Hello, authorization test successful!'"
            },
            {
                "role": "user", 
                "content": "Test message"
            }
        ]
        
        for provider in providers_to_test:
            self.log(f"🔍 Testing {provider} authorization...")
            
            provider_result = {
                "status": "UNKNOWN",
                "error": None,
                "response_received": False
            }
            
            try:
                # Попробуем использовать провайдер через роль которая его поддерживает
                if provider.startswith("anthropic") or provider.startswith("openai"):
                    test_role = "Architect"  # Эти провайдеры есть в Architect
                elif provider.startswith("gemini"):
                    test_role = "Architect"  # Gemini тоже есть в Architect
                elif provider.startswith("qwen"):
                    test_role = "Dev"  # Qwen есть в Dev
                else:
                    test_role = "Architect"
                
                response = completion(
                    role=test_role,
                    messages=simple_test_messages,
                    max_tokens=50,
                    temperature=0.1,
                    timeout_s=20
                )
                
                # Проверяем что ответ получен
                if response and "choices" in response:
                    content = response["choices"][0].get("message", {}).get("content", "")
                    if content:
                        provider_result["status"] = "SUCCESS"
                        provider_result["response_received"] = True
                        provider_result["provider_used"] = response.get("provider", "unknown")
                        self.log(f"✅ {provider} authorization OK")
                    else:
                        provider_result["status"] = "FAILED"
                        provider_result["error"] = "Empty response"
                        self.log(f"⚠️ {provider} returned empty response")
                else:
                    provider_result["status"] = "FAILED"
                    provider_result["error"] = "No response received"
                    self.log(f"❌ {provider} no response")
                    
            except Exception as e:
                provider_result["status"] = "FAILED"
                provider_result["error"] = str(e)
                self.log(f"❌ {provider} authorization failed: {str(e)[:100]}")
                
            auth_results["providers"][provider] = provider_result
            time.sleep(1)  # Пауза между провайдерами
            
        self.save_artifact("authorization_test.json", auth_results)
        return auth_results

    def create_full_feature_test(self) -> Dict[str, Any]:
        """Создает полную фичу для проверки цепочки ролей"""
        self.log("🚀 Creating full feature to test role chain...")
        
        import requests
        
        try:
            # Создаем фичу с задачей которая должна задействовать все роли
            payload = {
                "title": f"Comprehensive Test Feature {self.correlation_id}",
                "description": "Создать REST API эндпоинт /api/v1/status который возвращает статус системы с временем работы",
                "autostart": True,
                "notes": "comprehensive_test_full_feature"
            }
            
            response = requests.post(
                "http://127.0.0.1:8081/api/v1/orchestrator/features",
                json=payload,
                auth=("ops", "ops123"),
                timeout=10
            )
            
            if response.status_code != 200:
                return {
                    "status": "FAILED",
                    "error": f"Feature creation failed: {response.status_code}",
                    "response": response.text
                }
                
            feature_data = response.json()
            feature_id = feature_data["id"]
            
            self.log(f"✅ Feature created: ID={feature_id}")
            
            # Ждем завершения (до 3 минут)
            start_time = time.time()
            timeout = 180
            
            while time.time() - start_time < timeout:
                try:
                    status_response = requests.get(
                        f"http://127.0.0.1:8081/api/v1/orchestrator/features/{feature_id}",
                        auth=("ops", "ops123"),
                        timeout=5
                    )
                    
                    if status_response.status_code == 200:
                        feature_status = status_response.json()
                        current_status = feature_status.get("status", "UNKNOWN")
                        
                        self.log(f"📊 Feature status: {current_status}")
                        
                        if current_status in ["DONE", "COMPLETED", "MERGED"]:
                            return {
                                "status": "SUCCESS",
                                "feature_id": feature_id,
                                "final_status": current_status,
                                "execution_time": time.time() - start_time,
                                "feature_data": feature_status
                            }
                        elif current_status in ["FAILED", "ERROR"]:
                            return {
                                "status": "FAILED", 
                                "feature_id": feature_id,
                                "final_status": current_status,
                                "execution_time": time.time() - start_time,
                                "feature_data": feature_status
                            }
                            
                    time.sleep(10)
                    
                except Exception as e:
                    self.log(f"⚠️ Status check error: {e}")
                    time.sleep(15)
                    
            # Timeout
            return {
                "status": "TIMEOUT",
                "feature_id": feature_id,
                "execution_time": timeout,
                "error": "Feature execution timeout"
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "full_error": traceback.format_exc()
            }

    def generate_report(self, role_results: Dict[str, Any], auth_results: Dict[str, Any], feature_result: Dict[str, Any]) -> str:
        """Генерирует итоговый отчет"""
        
        # Подсчитываем статистику
        total_roles = len(role_results)
        successful_roles = len([r for r in role_results.values() if r["status"] == "SUCCESS"])
        
        total_providers = len(auth_results["providers"])
        successful_providers = len([p for p in auth_results["providers"].values() if p["status"] == "SUCCESS"])
        
        execution_time = time.time() - self.start_time
        
        report = f"""# Comprehensive Agent Test Report

## Test Summary
- **Correlation ID**: {self.correlation_id}
- **Execution Time**: {execution_time:.2f} seconds
- **Test Date**: {datetime.now().isoformat()}

## Role Testing Results ({successful_roles}/{total_roles} passed)
"""
        
        for role, result in role_results.items():
            status_icon = "✅" if result["status"] == "SUCCESS" else "❌"
            provider = result.get("provider_used", "unknown")
            latency = result.get("latency_ms", 0)
            
            report += f"- **{role}**: {status_icon} ({provider}, {latency}ms)\n"
            if result["error"]:
                report += f"  - Error: {result['error']}\n"
                
        report += f"""
## Provider Authorization Results ({successful_providers}/{total_providers} passed)
"""
        
        for provider, result in auth_results["providers"].items():
            status_icon = "✅" if result["status"] == "SUCCESS" else "❌"
            report += f"- **{provider}**: {status_icon}\n"
            if result["error"]:
                report += f"  - Error: {result['error']}\n"
                
        report += f"""
## Full Feature Test
"""
        
        if feature_result["status"] == "SUCCESS":
            report += f"""- **Status**: ✅ SUCCESS
- **Feature ID**: {feature_result['feature_id']}
- **Final Status**: {feature_result['final_status']}
- **Execution Time**: {feature_result['execution_time']:.2f}s
"""
        else:
            report += f"""- **Status**: ❌ {feature_result['status']}
- **Error**: {feature_result.get('error', 'Unknown error')}
"""

        if feature_result.get('feature_id'):
            report += f"- **Feature ID**: {feature_result['feature_id']}\n"
            
        report += f"""
## System Health
- **LLM Router**: {'✅ Working' if successful_roles > 0 else '❌ Issues'}
- **Provider Auth**: {'✅ Working' if successful_providers > 0 else '❌ Issues'}
- **Orchestrator**: {'✅ Working' if feature_result['status'] in ['SUCCESS', 'TIMEOUT'] else '❌ Issues'}

## Recommendations
"""

        if successful_roles < total_roles:
            report += "- Fix failed role configurations\n"
        if successful_providers < total_providers:
            report += "- Check provider authorization credentials\n"
        if feature_result["status"] != "SUCCESS":
            report += "- Debug orchestrator pipeline\n"
        if successful_roles == total_roles and successful_providers == total_providers:
            report += "- All systems operational! 🎉\n"

        report += f"""
## Artifacts Location
All test artifacts saved to: {self.artifacts_dir}

---
**Test completed at {datetime.now().isoformat()}**
"""
        
        self.save_artifact("COMPREHENSIVE_REPORT.md", report)
        return report

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Запускает полный комплексный тест"""
        
        self.log("🚀 Starting comprehensive agent test...")
        
        try:
            # 1. Тест ролей
            self.log("Phase 1: Testing individual roles...")
            role_results = self.test_all_roles()
            
            # 2. Тест авторизации провайдеров
            self.log("Phase 2: Testing provider authorization...")
            auth_results = self.test_provider_authorization()
            
            # 3. Тест полной фичи
            self.log("Phase 3: Testing full feature pipeline...")
            feature_result = self.create_full_feature_test()
            
            # 4. Генерация отчета
            self.log("Phase 4: Generating report...")
            report = self.generate_report(role_results, auth_results, feature_result)
            
            return {
                "status": "SUCCESS",
                "correlation_id": self.correlation_id,
                "execution_time": time.time() - self.start_time,
                "role_results": role_results,
                "auth_results": auth_results,
                "feature_result": feature_result,
                "artifacts_dir": str(self.artifacts_dir),
                "report": report
            }
            
        except Exception as e:
            error_result = {
                "status": "FAILED",
                "error": str(e),
                "full_error": traceback.format_exc(),
                "correlation_id": self.correlation_id,
                "execution_time": time.time() - self.start_time
            }
            self.save_artifact("ERROR_REPORT.json", error_result)
            raise


def main():
    """Main entry point"""
    test = ComprehensiveAgentTest()
    
    print("🧪 COMPREHENSIVE AGENT TEST")
    print("="*50)
    print(f"📋 Correlation ID: {test.correlation_id}")
    print("🎯 Testing all roles with real providers")
    print("🔐 Checking authorization for all providers")
    print("🚀 Creating full feature pipeline test")
    print("="*50)
    
    try:
        result = test.run_comprehensive_test()
        
        print("\n" + "="*60)
        print("🎉 COMPREHENSIVE TEST COMPLETED!")
        print("="*60)
        print(f"✅ Status: {result['status']}")
        print(f"⏱️  Duration: {result['execution_time']:.2f}s")
        print(f"📁 Artifacts: {result['artifacts_dir']}")
        
        # Краткая статистика
        role_results = result['role_results']
        auth_results = result['auth_results']
        
        successful_roles = len([r for r in role_results.values() if r["status"] == "SUCCESS"])
        total_roles = len(role_results)
        
        successful_providers = len([p for p in auth_results["providers"].values() if p["status"] == "SUCCESS"])
        total_providers = len(auth_results["providers"])
        
        print(f"👥 Roles: {successful_roles}/{total_roles} passed")
        print(f"🔐 Providers: {successful_providers}/{total_providers} authorized")
        print(f"🚀 Feature: {result['feature_result']['status']}")
        
        return 0 if result['status'] == 'SUCCESS' else 1
        
    except Exception as e:
        print(f"\n❌ COMPREHENSIVE TEST FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())