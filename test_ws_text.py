#!/usr/bin/env python3
"""
Тестовый скрипт для проверки WebSocket-чата с текстовыми адаптерами.
Тестирует "холодные" и "горячие" старты LLM для роли Maintainer.
"""

import asyncio
import json
import time
import uuid
import yaml
from typing import List, Dict, Any
import websockets
from websockets.exceptions import ConnectionClosedError, WebSocketException

# Конфигурация
WS_URL = "ws://localhost:8081/ws/v1/chat/maintainer"
ROUTING_CONFIG_PATH = "/opt/feature-factory/configs/llm_routing.yaml"

class WebSocketTester:
    def __init__(self):
        self.results = {}
        self.session_id = None
        
    def load_routing_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию роутинга LLM."""
        with open(ROUTING_CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    
    def get_reasoning_providers_for_maintainer(self) -> List[str]:
        """Получает список reasoning-провайдеров для роли Maintainer."""
        config = self.load_routing_config()
        maintainer_config = config.get('roles', {}).get('Maintainer', {})
        all_providers = maintainer_config.get('providers', [])
        
        # Фильтруем только reasoning-провайдеры согласно логике из router.py
        reasoning_providers = []
        reasoning_effort = maintainer_config.get('reasoning_effort', 'minimal')
        extended_thinking = maintainer_config.get('extended_thinking', False)
        adaptive_thinking = maintainer_config.get('adaptive_thinking', False)
        
        for provider in all_providers:
            # Qwen исключается из reasoning режима (router.py:102)
            if provider.startswith('qwen'):
                continue
                
            # В reasoning режиме выбираем провайдеров для high reasoning effort
            if reasoning_effort == 'high' or extended_thinking or adaptive_thinking:
                reasoning_providers.append(provider)
                
        return reasoning_providers
    
    async def test_websocket_connection(self) -> bool:
        """Тестирует базовое WebSocket подключение."""
        try:
            async with websockets.connect(WS_URL) as websocket:
                # Отправляем handshake
                handshake = {"message": None, "session_id": None}
                await websocket.send(json.dumps(handshake))
                
                # Получаем ответ
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                
                if data.get("type") == "connected":
                    self.session_id = data.get("session_id")
                    print(f"✅ WebSocket подключение успешно. Session ID: {self.session_id}")
                    return True
                else:
                    print(f"❌ Неожиданный ответ handshake: {data}")
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка WebSocket подключения: {e}")
            return False
    
    async def test_cold_start(self, provider_hint: str = None) -> Dict[str, Any]:
        """Тестирует холодный старт (новая сессия)."""
        print(f"🧊 Тестирование холодного старта...")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                start_time = time.time()
                
                # Новая сессия (без session_id)
                test_message = {
                    "message": "Привет! Просто скажи 'тест пройден' для проверки связи.", 
                    "session_id": None
                }
                await websocket.send(json.dumps(test_message))
                
                # Получаем ответ
                response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                end_time = time.time()
                
                data = json.loads(response)
                latency = (end_time - start_time) * 1000  # в миллисекундах
                
                return {
                    "success": True,
                    "latency_ms": latency,
                    "session_id": data.get("session_id"),
                    "response_length": len(data.get("response", "")),
                    "response_preview": data.get("response", "")[:100]
                }
                
        except asyncio.TimeoutError:
            return {"success": False, "error": "Timeout", "latency_ms": 60000}
        except Exception as e:
            return {"success": False, "error": str(e), "latency_ms": -1}
    
    async def test_warm_start(self, session_id: str) -> Dict[str, Any]:
        """Тестирует горячий старт (существующая сессия)."""
        print(f"🔥 Тестирование горячего старта с session_id: {session_id}")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                start_time = time.time()
                
                # Используем существующую сессию
                test_message = {
                    "message": "Еще раз скажи 'тест пройден' для проверки горячего старта.",
                    "session_id": session_id
                }
                await websocket.send(json.dumps(test_message))
                
                # Получаем ответ
                response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                end_time = time.time()
                
                data = json.loads(response)
                latency = (end_time - start_time) * 1000  # в миллисекундах
                
                return {
                    "success": True,
                    "latency_ms": latency,
                    "session_id": data.get("session_id"),
                    "response_length": len(data.get("response", "")),
                    "response_preview": data.get("response", "")[:100]
                }
                
        except asyncio.TimeoutError:
            return {"success": False, "error": "Timeout", "latency_ms": 60000}
        except Exception as e:
            return {"success": False, "error": str(e), "latency_ms": -1}
    
    async def run_full_test(self):
        """Выполняет полный цикл тестирования."""
        print("🚀 Начинаем тестирование WebSocket чата с текстовыми адаптерами...")
        
        # 1. Получаем список reasoning-провайдеров
        reasoning_providers = self.get_reasoning_providers_for_maintainer()
        print(f"📋 Reasoning-провайдеры для Maintainer: {reasoning_providers}")
        
        # 2. Тестируем WebSocket подключение
        if not await self.test_websocket_connection():
            print("❌ Базовое подключение не удалось. Завершаем тестирование.")
            return {"error": "WebSocket connection failed"}
        
        # 3. Тестируем холодный старт
        cold_start_result = await self.test_cold_start()
        print(f"🧊 Результат холодного старта: {cold_start_result}")
        
        if not cold_start_result.get("success"):
            print("❌ Холодный старт не удался. Завершаем тестирование.")
            return {"error": "Cold start failed", "cold_start": cold_start_result}
        
        # Получаем session_id для горячего старта
        session_id = cold_start_result.get("session_id")
        if not session_id:
            print("❌ Не получен session_id. Завершаем тестирование.")
            return {"error": "No session_id received", "cold_start": cold_start_result}
        
        # 4. Ждем немного для стабилизации
        await asyncio.sleep(2)
        
        # 5. Тестируем горячий старт
        warm_start_result = await self.test_warm_start(session_id)
        print(f"🔥 Результат горячего старта: {warm_start_result}")
        
        # 6. Формируем итоговый отчет
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_session_id": session_id,
            "reasoning_providers": reasoning_providers,
            "websocket_url": WS_URL,
            "cold_start": cold_start_result,
            "warm_start": warm_start_result,
            "performance_comparison": {
                "warm_faster_than_cold": (
                    warm_start_result.get("success", False) and 
                    cold_start_result.get("success", False) and
                    warm_start_result.get("latency_ms", 99999) < cold_start_result.get("latency_ms", 0)
                ),
                "latency_improvement_ms": (
                    cold_start_result.get("latency_ms", 0) - warm_start_result.get("latency_ms", 0)
                    if cold_start_result.get("success") and warm_start_result.get("success") else 0
                )
            }
        }
        
        return report

async def main():
    """Главная функция тестирования."""
    tester = WebSocketTester()
    
    try:
        report = await tester.run_full_test()
        
        # Сохраняем отчет в JSON
        with open("/opt/feature-factory/qa_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*60)
        print("📋 ИТОГОВЫЙ ОТЧЕТ СОХРАНЕН В qa_report.json")
        print("="*60)
        
        # Выводим краткую сводку
        if report.get("error"):
            print(f"❌ ТЕСТ НЕ ПРОЙДЕН: {report['error']}")
        else:
            cold_success = report["cold_start"].get("success", False)
            warm_success = report["warm_start"].get("success", False)
            
            if cold_success and warm_success:
                cold_time = report["cold_start"]["latency_ms"]
                warm_time = report["warm_start"]["latency_ms"]
                improvement = report["performance_comparison"]["latency_improvement_ms"]
                
                print(f"✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
                print(f"🧊 Холодный старт: {cold_time:.0f}ms")
                print(f"🔥 Горячий старт: {warm_time:.0f}ms")
                print(f"⚡ Улучшение: {improvement:.0f}ms ({improvement/cold_time*100:.1f}%)")
                print(f"📊 Горячий старт быстрее: {report['performance_comparison']['warm_faster_than_cold']}")
            else:
                print(f"⚠️  ТЕСТ ЧАСТИЧНО НЕ ПРОЙДЕН:")
                print(f"   Холодный старт: {'✅' if cold_success else '❌'}")
                print(f"   Горячий старт: {'✅' if warm_success else '❌'}")
                
    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        error_report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "critical_error": str(e),
            "test_status": "FAILED"
        }
        
        with open("/opt/feature-factory/qa_report.json", "w", encoding="utf-8") as f:
            json.dump(error_report, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    print("🧪 WebSocket + Text Adapters QA Test v2")
    print("="*50)
    asyncio.run(main())