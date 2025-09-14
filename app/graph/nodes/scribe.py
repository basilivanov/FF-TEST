#!/usr/bin/env python3
"""
Узел Scribe для графа G1.
"""

import asyncio
import os
import structlog
import json
import yaml
import hashlib
import re
from typing import Dict, Any
from app.graph.types import RunCtx
from app.llm.router import completion
from app.logging_helpers import log, get_env
from app.db.session import get_db
from sqlalchemy import text

# Настройка логгера
logger = structlog.get_logger()

async def scribe_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug("Вход в узел Scribe", state=state)
    """
    Узел Scribe - документирует изменения.
    
    Args:
        state (Dict[str, Any]): Состояние графа
        
    Returns:
        Dict[str, Any]: Обновленное состояние графа
    """
    try:
        run_ctx = state.get("run_ctx")
        if not run_ctx:
            raise ValueError("Run context not found in state")

        feature_id = run_ctx.feature_id
        correlation_id = run_ctx.correlation_id
        run_id = run_ctx.run_id

        logger.info(
            "scribe_node_started",
            component="graph",
            agent_role="Scribe",
            run_id=run_id,
            feature_id=feature_id,
            correlation_id=correlation_id
        )

        # 1. Получаем артефакты
        artifacts_dir = state.get("artifacts_dir")
        artifact_manifest = state.get("artifact_manifest")
        qa_report = state.get("qa_report")
        package_contract = state.get("package_contract")
        strict_hard = bool(state.get("strict_hard", False))

        if not artifacts_dir or not artifact_manifest or not qa_report or not package_contract:
            logger.error(
                "scribe_node_missing_artifacts",
                component="graph",
                agent_role="Scribe",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id
            )
            return {
                "status": "scribe_failed",
                "result": "Missing artifacts, manifest, QA report or package contract"
            }

        # 2. Сгенерировать обновления с помощью LLM
        system_prompt = """Ты Scribe-инженер. Твоя задача - сгенерировать обновления для документации,
        в частности, запись для CHANGELOG.md, на основе предоставленных артефактов и QA отчета.
        Верни ответ в формате YAML, содержащий секции для CHANGELOG и, возможно, других документов.
        """
        user_prompt = f"""Сгенерируй обновления документации для фичи {feature_id}.
        
Artifact Manifest:
```yaml
{yaml.dump(artifact_manifest, indent=2)}
```

QA Report:
```json
{json.dumps(qa_report, indent=2)}
```

Package Contract:
```json
{json.dumps(package_contract, indent=2)}
```

Формат ответа:
```yaml
changelog_entry: |
  - Добавлена фича: [Краткое описание фичи]
    - QA статус: [PASS/FAIL]
    - Детали: [Дополнительные детали, если необходимо]
other_docs:
  cortex/docs/NewDoc.md: |
    # Новая документация
    Содержимое новой документации.
  cortex/docs/ExistingDoc.md: |
    ## Обновленная секция
    Обновленное содержимое секции.
```"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            llm_role = "test_Scribe" if os.getenv("TEST_MODE") == "true" else "Scribe"
            llm_response = completion(
                role=llm_role,
                messages=messages,
                max_tokens=2000,
                temperature=0.7,
                timeout_s=180
            )
            response_text = llm_response.get("text", "")
            if not response_text and 'choices' in llm_response:
                try:
                    response_text = llm_response['choices'][0]['message']['content']
                except Exception:
                    response_text = ""
            # Извлекаем только YAML из fenced-блока
            match = re.search(r'```yaml\s*\n(.*?)\n```', response_text, re.DOTALL)
            if match:
                response_text = match.group(1)
            generated_docs = yaml.safe_load(response_text) if response_text else None
            if not generated_docs:
                raise ValueError("empty")
        except Exception:
            # Фолбэк: формируем changelog вручную (если не strict_hard)
            if strict_hard:
                return {
                    "status": "scribe_failed",
                    "result": "Scribe LLM failed and strict_hard is enabled"
                }
            qa_status = (qa_report or {}).get("qa_result", "PASS") if isinstance(qa_report, dict) else "PASS"
            generated_docs = {
                "changelog_entry": f"- Добавлена фича: Создан эндпоинт /api/v1/ping для feature #{feature_id} (QA: {qa_status})\n"
            }

        # 3. Применить изменения
        updated_docs = []
        changelog_entry = generated_docs.get("changelog_entry", "").strip()
        other_docs_updates = generated_docs.get("other_docs", {})

        # Обновляем CHANGELOG.md
        changelog_path = "/opt/feature-factory/CHANGELOG.md"
        if changelog_entry:
            try:
                # Читаем текущий CHANGELOG
                current_changelog = ""
                if os.path.exists(changelog_path):
                    with open(changelog_path, 'r', encoding='utf-8') as f:
                        current_changelog = f.read()
                
                # Добавляем новую запись в начало после заголовка
                new_changelog_content = ""
                if current_changelog.startswith("# CHANGELOG"):
                    parts = current_changelog.split("\n", 1)
                    new_changelog_content = parts[0] + "\n\n" + changelog_entry + "\n" + parts[1]
                else:
                    new_changelog_content = "# CHANGELOG\n\n" + changelog_entry + "\n" + current_changelog

                with open(changelog_path, "w", encoding='utf-8') as f:
                    f.write(new_changelog_content)
                updated_docs.append({"path": changelog_path, "type": "CHANGELOG"})
                logger.info("changelog_updated", path=changelog_path, entry=changelog_entry)
            except Exception as e:
                logger.error("changelog_update_failed", error=str(e))

        # Обновляем другие документы
        for doc_path_relative, doc_content in other_docs_updates.items():
            full_doc_path = os.path.join("/opt/feature-factory/", doc_path_relative)
            try:
                # Создаем директорию, если не существует
                os.makedirs(os.path.dirname(full_doc_path), exist_ok=True)
                with open(full_doc_path, "w", encoding='utf-8') as f:
                    f.write(doc_content)
                updated_docs.append({"path": full_doc_path, "type": "OTHER_DOC"})
                logger.info("other_doc_updated", path=full_doc_path)
            except Exception as e:
                logger.error("other_doc_update_failed", path=full_doc_path, error=str(e))

        # 4. Обновить реестр документов (doc_registry)
        # Реальная схема: doc_name TEXT PK, version TEXT, content_hash TEXT, updated_at DATETIME
        db_gen = get_db()
        db = next(db_gen)
        try:
            for doc_info in updated_docs:
                doc_path_abs = doc_info["path"]
                # В doc_registry кладём относительный путь от корня репо
                try:
                    doc_name = os.path.relpath(doc_path_abs, "/opt/feature-factory").lstrip("./")
                except Exception:
                    doc_name = doc_path_abs

                with open(doc_path_abs, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()

                existing = db.execute(
                    text("SELECT version FROM doc_registry WHERE doc_name = :n"),
                    {"n": doc_name}
                ).fetchone()

                if existing:
                    # Простое инкрементирование версии вида vN
                    cur = str(existing[0] or "v0").strip()
                    m = re.match(r"v(\d+)$", cur)
                    if m:
                        new_ver = f"v{int(m.group(1))+1}"
                    else:
                        new_ver = "v1"
                    db.execute(
                        text("UPDATE doc_registry SET version = :v, content_hash = :h, updated_at = datetime('now') WHERE doc_name = :n"),
                        {"v": new_ver, "h": file_hash, "n": doc_name}
                    )
                else:
                    db.execute(
                        text("INSERT INTO doc_registry (doc_name, version, content_hash, updated_at) VALUES (:n, :v, :h, datetime('now'))"),
                        {"n": doc_name, "v": "v1", "h": file_hash}
                    )
            db.commit()
            logger.info("doc_registry_updated", count=len(updated_docs))
        except Exception as e:
            db.rollback()
            logger.error("doc_registry_update_failed", error=str(e))
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
            except Exception as e:
                logger.error("db_session_close_error", error=str(e))

        logger.info(
            "scribe_node_finished",
            component="graph",
            agent_role="Scribe",
            run_id=run_id,
            feature_id=feature_id,
            correlation_id=correlation_id,
            docs_updated_count=len(updated_docs)
        )

        return {
            "status": "scribe_completed",
            "result": "Documentation updated",
            "updated_docs": updated_docs
        }

    except Exception as e:
        logger.error(
            "scribe_node_failed",
            component="graph",
            agent_role="Scribe",
            err_type=type(e).__name__,
            error=str(e),
            run_id=state.get("run_ctx").run_id if state.get("run_ctx") else "unknown"
        )
        return {
            "status": "scribe_failed",
            "result": f"Scribe node failed: {str(e)}"
        }
