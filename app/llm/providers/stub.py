import json
from typing import Dict, Any, Tuple, List

from app.llm.providers.base import LLMProviderAdapter


class StubAdapter(LLMProviderAdapter):
    """
    Адаптер-заглушка для тестирования без реальных вызовов LLM.
    """
    
    def __init__(self, provider_name="stub"):
        super().__init__(provider_name)

    def complete(self, messages: List[Dict[str, str]], max_tokens: int,
                 temperature: float, stop: List[str] = None, timeout_s: int = None) -> Dict[str, Any]:
        """
        Имитирует ответ LLM в зависимости от роли (по системному промпту).
        - Architect: JSON-план
        - Dev: fenced YAML с artifact_manifest + fenced код файла app/api/ping.py
        - QA: fenced Python тест для app/api/ping.py из каталога артефактов
        - Scribe: fenced YAML с changelog_entry
        """
        sys_text = (messages[0].get("content", "") if messages else "").lower()
        import sys
        print(f"[STUB DEBUG] System text keywords check: maintainer={('maintainer' in sys_text)}, диалоговый={('диалоговый' in sys_text)}", file=sys.stderr)
        print(f"[STUB DEBUG] System text preview: {sys_text[:300]}...", file=sys.stderr)

        def mk_result(content: str) -> Dict[str, Any]:
            return {
                "choices": [{"message": {"content": content}}],
                "usage": {"input_tokens": 10, "output_tokens": max(50, len(content)//4), "estimated": True},
                "model": "stub-1.0",
                "finish_reason": "stop"
            }

        if "maintainer" in sys_text.lower() or "мейнтейнер" in sys_text.lower() or "дружелюбный помощник" in sys_text.lower() or "контекст системы" in sys_text.lower() or "диалоговый" in sys_text.lower():
            # Maintainer: JSON ответ для диалога
            maintainer_response = {
                "response_for_user": "Отлично! 😊 Telegram бот для уведомлений - отличная идея! Уточните пожалуйста:\n\n• Какие уведомления нужны? (о новых заказах, ошибках системы, завершении задач?)\n• Откуда брать информацию? (из базы данных, файлов, внешних сервисов?)\n• Как часто проверять? (постоянно, раз в час, раз в день?)\n• Кому отправлять? (лично вам или группе?)\n\nЭто поможет создать идеальное решение! 🚀",
                "action": {
                    "type": "CONTINUE_DIALOG"
                }
            }
            return mk_result(json.dumps(maintainer_response))
        
        if "architect" in sys_text:
            mock_plan = {
                "dag": {
                    "nodes": [
                        {"id": "dev_task_1", "role": "Dev", "name": "Implement Ping-Pong Endpoint"}
                    ],
                    "edges": []
                },
                "budgets": {"Dev": 100, "QA": 50, "Scribe": 20, "Maintainer": 10, "Architect": 5},
                "dod": ["Ping-Pong endpoint implemented", "Tests passed"]
            }
            return mk_result(json.dumps(mock_plan))

        if "internal analyst" in sys_text.lower() or "внутренняя задача" in sys_text.lower() or "техническое" in sys_text.lower():
            # Internal Analyst: JSON для внутренних задач
            internal_response = {
                "interpretation": "Требуется создать систему уведомлений в Telegram для внутренних процессов фабрики",
                "intent": {
                    "type": "INTERNAL",
                    "title": "Telegram бот для уведомлений",
                    "description": "Создать Telegram бота для отправки уведомлений о событиях системы",
                    "priority": 2,
                    "technical_requirements": ["Python telegram-bot библиотека", "Webhook или polling механизм", "Интеграция с системными событиями"],
                    "dependencies": ["Telegram Bot API", "FastAPI webhook endpoint"],
                    "affected_components": ["Notification system", "API endpoints", "Event handlers"],
                    "estimated_complexity": "medium"
                }
            }
            return mk_result(json.dumps(internal_response))
            
        if "business analyst" in sys_text.lower() or "бизнес-задача" in sys_text.lower() or "клиент" in sys_text.lower():
            # Business Analyst: JSON для бизнес-задач  
            business_response = {
                "interpretation": "Пользователи хотят получать уведомления о важных бизнес-событиях через Telegram",
                "intent": {
                    "type": "BUSINESS",
                    "title": "Telegram уведомления для пользователей",
                    "description": "Система push-уведомлений в Telegram для клиентов о статусе заказов и важных событиях",
                    "priority": 3,
                    "user_stories": ["Как пользователь, я хочу получать уведомления о статусе заказа", "Как пользователь, я хочу настраивать типы уведомлений"],
                    "acceptance_criteria": ["Подключение к Telegram", "Настройка типов уведомлений", "Персональные настройки"],
                    "business_value": "Увеличение вовлеченности пользователей и уменьшение обращений в поддержку",
                    "target_audience": "Активные клиенты",
                    "success_metrics": ["Процент подключившихся к боту", "Снижение обращений в поддержку"],
                    "estimated_impact": "high"
                }
            }
            return mk_result(json.dumps(business_response))

        if "python разработчик" in sys_text or "artifact_manifest" in sys_text:
            # Dev: вернуть YAML + файл ping.py
            manifest_yaml = (
                "files:\n"
                "  - app/api/ping.py\n"
                "package_contract:\n"
                "  package_id: PKG-PING-MOCK\n"
                "  summary: Add /api/v1/ping endpoint returning {\\\"ping\\\":\\\"pong\\\"}\n"
                "  files_layout:\n"
                "    - app/api/ping.py\n"
            )
            ping_py = (
                "from fastapi import APIRouter\n\n"
                "router = APIRouter(prefix=\"/api/v1\")\n\n"
                "@router.get(\"/ping\")\n"
                "async def ping():\n"
                "    return {\"ping\": \"pong\"}\n"
            )
            content = f"""
```yaml
{manifest_yaml}
```

```python
# app/api/ping.py
{ping_py}
```
""".strip()
            return mk_result(content)

        if "qa-инженер" in sys_text or "pytest" in sys_text:
            # QA: тест, который импортирует модуль из артефактов и дергает эндпоинт
            test_code = (
                "import importlib.util, pathlib\n"
                "from fastapi import FastAPI\n"
                "from fastapi.testclient import TestClient\n"
                "def test_ping_endpoint_from_artifacts():\n"
                "    mod_path = pathlib.Path(__file__).parent / 'app' / 'api' / 'ping.py'\n"
                "    spec = importlib.util.spec_from_file_location('app.api.ping', str(mod_path))\n"
                "    ping = importlib.util.module_from_spec(spec)\n"
                "    spec.loader.exec_module(ping)\n"
                "    app = FastAPI()\n"
                "    app.include_router(ping.router)\n"
                "    client = TestClient(app)\n"
                "    r = client.get('/api/v1/ping')\n"
                "    assert r.status_code == 200\n"
                "    assert r.json() == {\"ping\": \"pong\"}\n"
            )
            content = f"""
```python
{test_code}
```
""".strip()
            return mk_result(content)

        if "scribe-инженер" in sys_text or "changelog" in sys_text:
            # Scribe: YAML с changelog_entry
            yaml_text = (
                "changelog_entry: |\n"
                "  - Добавлена фича: Создан эндпоинт /api/v1/ping (QA: PASS)\n"
            )
            return mk_result(f"```yaml\n{yaml_text}\n```")

        if "maintainer" in sys_text.lower() or "мейнтейнер" in sys_text.lower() or "дружелюбный помощник" in sys_text.lower() or "контекст системы" in sys_text.lower() or "диалоговый" in sys_text.lower():
            # Maintainer: JSON ответ для диалога
            maintainer_response = {
                "response_for_user": "Отлично! 😊 Telegram бот для уведомлений - отличная идея! Уточните пожалуйста:\n\n• Какие уведомления нужны? (о новых заказах, ошибках системы, завершении задач?)\n• Откуда брать информацию? (из базы данных, файлов, внешних сервисов?)\n• Как часто проверять? (постоянно, раз в час, раз в день?)\n• Кому отправлять? (лично вам или группе?)\n\nЭто поможет создать идеальное решение! 🚀",
                "action": {
                    "type": "CONTINUE_DIALOG"
                }
            }
            return mk_result(json.dumps(maintainer_response))
        
        # По умолчанию вернем JSON план  
        default_plan = {"dag": {"nodes": [], "edges": []}}
        return mk_result(json.dumps(default_plan))

    def parse_stdout(self, stdout: str) -> Dict[str, Any]:
        """
        Парсит stdout от CLI команды и возвращает унифицированный контракт.
        Для StubAdapter просто парсит stdout как JSON.
        """
        return json.loads(stdout)
