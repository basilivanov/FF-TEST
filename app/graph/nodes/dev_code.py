#!/usr/bin/env python3
"""
Узел Dev для графа G1.
Интеграция с LLM роутером для генерации кода.
"""

import asyncio
import tempfile
import os
import uuid
import yaml
import hashlib
import re
from typing import Dict, Any
from app.llm.router import completion
from app.graph.types import RunCtx
from app.logging_helpers import log, get_env
from app.db.session import get_db
from app.utils.prompts import get_role_prompt
from sqlalchemy import text

def _get_capsule_hash() -> str:
    """Вычисляет хэш капсулы контекста для передачи в LLM."""
    try:
        with open("/opt/feature-factory/app/agents/prompts/_capsule.md", "r") as f:
            capsule_content = f.read()
        return hashlib.md5(capsule_content.encode()).hexdigest()[:8]
    except Exception:
        return "unknown"

def _parse_llm_response(response_text: str) -> tuple[dict, dict]:
    """Парсит ответ LLM и извлекает artifact_manifest и файлы."""
    artifact_manifest = {}
    files = {}
    yaml_blocks = re.findall(r'```yaml\s*\n(.*?)\n```', response_text, re.DOTALL)
    if yaml_blocks:
        try:
            artifact_manifest = yaml.safe_load(yaml_blocks[0])
        except yaml.YAMLError:
            artifact_manifest = {"files": [], "package_contract": {}}
    code_blocks = re.findall(r'```(\w+)\s*\n# ([^\n]+)\n(.*?)\n```', response_text, re.DOTALL)
    for lang, filename, content in code_blocks:
        files[filename.strip()] = content.strip()
    if not files:
        python_blocks = re.findall(r'```python\s*\n(.*?)\n```', response_text, re.DOTALL)
        for i, content in enumerate(python_blocks):
            files[f"main_{i}.py"] = content.strip()
    return artifact_manifest, files

async def dev_code_node(state: Dict[str, Any]) -> Dict[str, Any]:
    log.debug("Вход в узел Dev", state=state)
    try:
        run_ctx = state.get("run_ctx")
        if not run_ctx:
            raise ValueError("Run context not found in state")
        
        task_id = run_ctx.task_id
        feature_id = run_ctx.feature_id
        correlation_id = run_ctx.correlation_id
        run_id = run_ctx.run_id
        
        package_contract = state.get("package_contract", {})
        strict_hard = bool(state.get("strict_hard", False))
        capsule_hash = _get_capsule_hash()
        
        log.info(
            event="job_started",
            env=get_env(),
            component="graph",
            agent_role="Dev",
            run_id=run_id,
            task_id=task_id,
            correlation_id=correlation_id,
            kv={
                "feature_id": feature_id,
                "capsule_hash": capsule_hash,
                "graph_node": "dev_code",
                "package_contract_id": package_contract.get("package_id") if package_contract else "unknown"
            }
        )
        
        # Загружаем промпт из системы промптов
        try:
            system_prompt = get_role_prompt("Dev")
            log.info("dev_prompt_loaded", run_id=run_id, task_id=task_id, prompt_hash=hashlib.md5(system_prompt.encode()).hexdigest()[:8])
        except Exception as e:
            log.error("dev_prompt_load_failed", run_id=run_id, task_id=task_id, error=str(e))
            # Используем встроенный промпт как fallback
            system_prompt = '''Ты опытный Python разработчик FastAPI. Твоя задача - создать код на основе описания задачи.

ВАЖНО: Отвечай ТОЛЬКО YAML манифест + код в fenced блоках. Никаких объяснений.

ФОРМАТ ОТВЕТА:
```yaml
files:
  - app/api/[endpoint_name].py
  - tests/test_[endpoint_name].py  # ОБЯЗАТЕЛЬНО тесты
package_contract:
  package_id: PKG-[FEATURE_ID]-v1
```

```python
# app/api/[endpoint_name].py
from __future__ import annotations
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/v1")

@router.get("/[endpoint]")
async def [function_name]():
    return {"message": "Hello, World!", "timestamp": datetime.now().isoformat()}
```

```python
# tests/test_[endpoint_name].py
from __future__ import annotations
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

def test_[endpoint]_endpoint():
    app = FastAPI()
    from app.api.[endpoint_name] import router
    app.include_router(router)
    client = TestClient(app)
    
    response = client.get("/api/v1/[endpoint]")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "timestamp" in data
```

ПРАВИЛА:
- Python 3.12 с type hints
- FastAPI роутеры с prefix="/api/v1"  
- ОБЯЗАТЕЛЬНО включай unit tests
- Только реальный код, без TODO/заглушек
- Имена файлов должны точно совпадать с files в YAML'''

        # *** WATCHDOG INTEGRATION START ***
        escalation_context = state.get("escalation_context")
        if escalation_context:
            log.warning("dev_node_retry_with_context", run_id=run_id, task_id=task_id)
            error_context_prompt = f"""### Контекст предыдущих ошибок
В предыдущих запусках были обнаружены следующие повторяющиеся ошибки. Проанализируй их и измени свой подход, чтобы избежать их повторения.
{escalation_context}
###

"""
            system_prompt = error_context_prompt + system_prompt
        # *** WATCHDOG INTEGRATION END ***

        db_gen = get_db()
        db = next(db_gen)
        
        try:
            task_result = db.execute(
                text("SELECT dsl_json FROM tasks WHERE feature_id = :feature_id AND id = :task_id"),
                {"feature_id": feature_id, "task_id": task_id}
            ).fetchone()

            if not task_result or not task_result[0]:
                raise ValueError(f"DSL JSON not found for task {task_id} of feature {feature_id}")

            dsl_json_content = task_result[0]

            # Контекстный пакет из оркестратора/упаковщика
            context_pack = state.get("context_pack", "Контекст не был предоставлен.")

            task_description = f"Задача: {task_id}\nФича: {feature_id}\nContract: {package_contract}\nDSL JSON для задачи: {dsl_json_content}\n\nСоздай простую Python фичу \"{feature_id}\" согласно DSL JSON."

            user_content = f"""
# КОНТЕКСТ ЗАДАЧИ
{context_pack}

# ОПИСАНИЕ ЗАДАЧИ
{task_description}
"""
            
            # Логируем факт включения контекста в промпт (превью усечено)
            try:
                preview = (context_pack or "")[:300]
                log.info(
                    event="dev_prompt_context_attached",
                    env=get_env(),
                    component="graph",
                    agent_role="Dev",
                    run_id=run_id,
                    task_id=task_id,
                    kv={"context_size": len(context_pack or ""), "preview": preview}
                )
            except Exception:
                pass

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            llm_role = "test_Dev" if os.getenv("TEST_MODE") == "true" else "Dev"
            
            tool_errors = [] # Для Watchdog
            try:
                provider_start_index = int(state.get("next_provider_index", 0) or 0)
                result = completion(
                    role=llm_role,
                    messages=messages,
                    max_tokens=1400,
                    temperature=0,
                    timeout_s=120,
                    provider_start_index=provider_start_index,
                )
                response_text = result.get("text", "")
                if not response_text and 'choices' in result:
                    try:
                        response_text = result['choices'][0]['message']['content']
                    except Exception:
                        response_text = ""
                artifact_manifest, files = _parse_llm_response(response_text)
            except Exception as llm_error:
                # Предполагаем, что ошибка LLM - это тип ошибки инструмента
                tool_errors.append({"tool_name": "llm_completion", "error_type": type(llm_error).__name__, "error_message": str(llm_error)})
                log.error(
                    event="llm_error_no_fallback",
                    agent_role="Dev",
                    run_id=run_id,
                    task_id=task_id,
                    kv={"llm_error": str(llm_error)}
                )
                # NO MORE FALLBACK - fail the task if LLM fails
                raise Exception(f"Dev agent LLM failed: {llm_error}. No fallback allowed.")
                
            artifacts_dir = f"/opt/feature-factory/tmp/{run_id}"
            os.makedirs(artifacts_dir, exist_ok=True)
            
            if not artifact_manifest or not artifact_manifest.get("files"):
                log.error(
                    event="dev_no_artifacts_generated",
                    agent_role="Dev",
                    run_id=run_id,
                    task_id=task_id
                )
                raise Exception("Dev agent did not generate any artifacts. LLM response was empty or invalid.")

            manifest_path = os.path.join(artifacts_dir, "artifact_manifest.yaml")
            with open(manifest_path, "w") as f:
                yaml.dump(artifact_manifest, f)
            
            created_files = ["artifact_manifest.yaml"]
            for filename, content in files.items():
                file_path = os.path.join(artifacts_dir, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(content)
                created_files.append(filename)
            
            log.info(event="artifact_generated", agent_role="Dev", run_id=run_id, kv={"files_created": created_files})
            log.info(event="job_finished", agent_role="Dev", run_id=run_id, kv={"status": "success"})
            
            # Возвращаем результат и очищаем состояние Watchdog для следующего шага
            return {
                "status": "dev_completed",
                "result": "Dev work completed",
                "artifacts_dir": artifacts_dir,
                "artifacts": created_files,
                "artifact_manifest": artifact_manifest,
                "response_text": response_text or "",
                "package_contract": artifact_manifest.get("package_contract", {}),
                "tool_errors": tool_errors, # Передаем ошибки в Watchdog
                "escalation_context": "", # Очищаем контекст
                "watchdog_failures": [], # Очищаем историю для следующего чистого запуска
                "next_provider_index": 0, # Сбрасываем эскалацию провайдера после успешной генерации
            }
            
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    except Exception as e:
        run_ctx = state.get("run_ctx")
        log.error(
            event="job_finished",
            agent_role="Dev",
            run_id=run_ctx.run_id if run_ctx else "unknown",
            kv={"status": "failed", "err_type": type(e).__name__, "err_msg": str(e)},
            stack=True
        )
        # Передаем ошибку в виде, понятном для Watchdog
        return {
            "tool_errors": [{"tool_name": "dev_code_node", "error_type": type(e).__name__, "error_message": str(e)}],
            "escalation_context": "",
            "watchdog_failures": state.get("watchdog_failures", [])
        }
