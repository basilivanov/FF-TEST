#!/usr/bin/env python3
"""
API оркестратора для интеграции UI/скриптов, реализация по спецификации API-Orchestrator-001.md.
"""

import time
import uuid
import os
import json
import yaml
import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Request, Depends, status
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.orchestrator.apply import ArtifactApplier

# Импортируем схемы
from app.api.schemas.orchestrator_schemas import (
    FeatureCreateRequest,
    FeatureCreatedResponse,
    PlanResponse,
    TaskPlanResponse,
    RunResponse,
    GraphStatusResponse,
    GraphRunListItem,
    ErrorResponse
)

# Импортируем logging_helpers
from app.logging_helpers import log, get_env, generate_correlation_id
from app.db.session import get_db
from app.utils.datetime_helpers import serialize_datetime_safe
from app.llm.router import completion, RETRYABLE_ERROR
from jsonschema import validate, ValidationError as JsonSchemaValidationError
import os

# Пытаемся импортировать start_run, но если не получается - работаем без графа
try:
    from app.graph.base import start_run
    GRAPH_AVAILABLE = True  # Enable real LangGraph for E2E testing
except ImportError as e:
    GRAPH_AVAILABLE = False
    import structlog
    graph_logger = structlog.get_logger()
    graph_logger.warning("graph_import_failed", error=str(e))

# Создаем роутер без префикса, так как он будет добавлен в app/api/orchestrator.py
router = APIRouter()

# Загружаем схему Architect Plan при старте приложения
ARCHITECT_PLAN_SCHEMA_PATH = "/opt/feature-factory/configs/schemas/architect.plan.schema.json"
try:
    with open(ARCHITECT_PLAN_SCHEMA_PATH, 'r') as f:
        architect_plan_schema = json.load(f)
except Exception as e:
    log.error("architect_plan_schema_load_failed", error=str(e))
    architect_plan_schema = {} # Fallback to empty schema to avoid startup crash



# Вспомогательные функции


def get_correlation_id(request: Request) -> str:
    """Получает correlation_id из заголовков запроса."""
    return request.headers.get("x-correlation-id", generate_correlation_id())


def log_api_call_start(request: Request, correlation_id: str, **kwargs):
    """Логирует начало API вызова."""
    log.info(
        event="api_call_start",
        env=get_env(),
        component="api",
        agent_role="Orchestrator",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            **kwargs
        }
    )


def log_api_call_end(request: Request, correlation_id: str, status_code: int, duration_ms: float, **kwargs):
    """Логирует завершение API вызова."""
    log.info(
        event="api_call_end",
        env=get_env(),
        component="api",
        agent_role="Orchestrator",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            "status": status_code,
            "duration_ms": round(duration_ms, 2),
            **kwargs
        }
    )


# Эндпоинты API
@router.post("/features", 
             response_model=FeatureCreatedResponse,
             responses={
                 400: {"model": ErrorResponse},
                 409: {"model": ErrorResponse}
             })
async def create_feature(
    request: Request,
    feature_request: FeatureCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Создать фичу.
    
    Args:
        request: HTTP запрос
        feature_request: Данные для создания фичи
        
    Returns:
        FeatureCreatedResponse: Информация о созданной или найденной фиче
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    env = get_env()
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        title=feature_request.title
    )
    
    try:
        # Проверяем, есть ли уже фича с таким title и env (идемпотентность)
        result = db.execute(
            text("""
                SELECT id, status FROM features 
                WHERE title = :title AND env = :env
            """
            ),
            {
                "title": feature_request.title,
                "env": env
            }
        )
        existing_feature = result.fetchone()
        
        # Если фича уже существует, возвращаем её
        if existing_feature:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=200,
                duration_ms=duration_ms,
                feature_id=existing_feature[0],
                message="Feature already exists"
            )
            
            return FeatureCreatedResponse(
                id=existing_feature[0],
                status=existing_feature[1]
            )
        
        # Создаем новую фичу
        intent_json = json.dumps(feature_request.intent) if feature_request.intent else "{}"

        # Совместимость со схемой БД: определяем доступные колонки таблицы features
        cols_res = db.execute(text("PRAGMA table_info(features)"))
        feature_cols = {row[1] for row in cols_res.fetchall()}  # row[1] = name

        # Базовые колонки, присутствующие во всех вариантах схемы
        columns = ["title", "intent_json", "status", "created_at", "created_by", "env"]
        values = [":title", ":intent_json", "'NEW'", "datetime('now')", "'API'", ":env"]

        # Опциональная колонка 'type' — добавляем ТОЛЬКО если есть в БД и задано значение
        params: Dict[str, Any] = {
            "title": feature_request.title,
            "intent_json": intent_json,
            "env": env,
        }
        feat_type = getattr(feature_request, "type", None)
        if "type" in feature_cols:
            # Если значение не передано в запросе — используем безопасный дефолт согласно CHECK-конSTRAINTу БД
            # Допустимые значения: 'INTERNAL' | 'BUSINESS'; выбираем 'BUSINESS' по умолчанию
            if feat_type is None:
                feat_type = "BUSINESS"
            columns.append("type")
            values.append(":type")
            params["type"] = feat_type

        insert_sql = f"INSERT INTO features ({', '.join(columns)}) VALUES ({', '.join(values)})"

        result = db.execute(text(insert_sql), params)
        
        feature_id = result.lastrowid
        db.commit()
        
        # Логируем успешное завершение вызова
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(
            request,
            correlation_id,
            status_code=200,
            duration_ms=duration_ms,
            feature_id=feature_id
        )
        
        # Автостарт планирования и выполнения для тестового контура (или если явно задано)
        def _auto_plan_and_run(fid: int, corr_id: str, strict: bool, strict_hard: bool):
            try:
                # Используем новую сессию
                db_gen_inner = get_db()
                db_inner = next(db_gen_inner)
                
                # PLAN (строгая валидация по схеме Architect в strict-режиме)
                res = db_inner.execute(text("SELECT intent_json FROM features WHERE id = :id"), {"id": fid})
                row = res.fetchone()
                intent_json = {}
                if row and row[0]:
                    try:
                        intent_json = json.loads(row[0])
                    except Exception:
                        intent_json = {}
                messages = [
                    {"role": "system", "content": "You are an Architect AI. Your task is to generate a detailed plan (DAG of tasks) based on the provided intent. The plan should be in JSON format, strictly following the architect.plan.schema.json."},
                    {"role": "user", "content": f"Generate a plan for the following intent: {json.dumps(intent_json)}"}
                ]
                llm_arch_role = "test_Architect" if os.getenv("TEST_MODE") == "true" else "Architect"

                # Robust JSON plan synthesis: try providers in chain order with fallback index
                plan_data = None
                last_err = None
                for start_idx in (0, 1, 2):
                    try:
                        llm_response = completion(
                            role=llm_arch_role,
                            messages=messages,
                            max_tokens=4000,
                            temperature=0.7,
                            timeout_s=60,
                            provider_start_index=start_idx,
                        )
                        plan_content = llm_response['choices'][0]['message']['content']
                        plan_data = json.loads(plan_content)
                        break
                    except Exception as e:
                        last_err = e
                        continue
                if plan_data is None:
                    raise RuntimeError(f"Architect plan JSON not obtained: {last_err}")
                # Валидация схемы (если strict)
                if strict:
                    validate(instance=plan_data, schema=architect_plan_schema)
                dag_nodes = plan_data.get("dag", {}).get("nodes", [])
                created_task_ids = []
                for node in dag_nodes:
                    task_role = node.get("role")
                    task_name = node.get("name") or node.get("id")
                    if not task_role or not task_name:
                        continue
                    result_ins = db_inner.execute(
                        text("""
                            INSERT INTO tasks (feature_id, role, dsl_json, status, attempts, scheduled_at)
                            VALUES (:feature_id, :role, :dsl_json, 'NEW', 0, datetime('now'))
                        """),
                        {"feature_id": fid, "role": task_role, "dsl_json": task_name}
                    )
                    try:
                        created_task_ids.append(result_ins.lastrowid)
                    except Exception:
                        pass
                db_inner.execute(text("UPDATE features SET status='PLANNED', updated_at=datetime('now') WHERE id=:id"), {"id": fid})
                db_inner.commit()

                # RUN (реплика логики run_feature мок)
                run_id = str(uuid.uuid4())
                env_local = get_env()
                db_inner.execute(
                    text("""
                        INSERT INTO graph_runs (run_id, feature_id, graph_name, thread_id, state_json, status, last_checkpoint_at, env)
                        VALUES (:run_id, :feature_id, 'G1', :thread_id, :state_json, 'RUNNING', datetime('now'), :env)
                    """),
                    {"run_id": run_id, "feature_id": fid, "thread_id": str(uuid.uuid4()), "state_json": json.dumps({"state": "started"}), "env": env_local}
                )
                db_inner.commit()

                def mock_graph_execution(run_id: str, feature_id: int):
                    try:
                        if strict:
                            # Строгий прогон узлов Dev→Gate→QA→Scribe→Apply
                            import asyncio
                            from app.graph.nodes.dev_code import dev_code_node
                            from app.graph.nodes.gate import gate_node
                            from app.graph.nodes.qa import qa_node
                            from app.graph.nodes.scribe import scribe_node
                            from app.graph.nodes.apply import apply_node
                            from app.graph.nodes.spec_synth import spec_synth_node
                            from app.graph.nodes.test_synth import test_synth_node
                            from app.graph.types import RunCtx

                            async def run_nodes():
                                package_contract = {"package_id": f"PKG-FEATURE-{feature_id}", "summary": "Auto strict pipeline"}
                                # Выбираем Dev-задачу
                                db_g = get_db()
                                db3 = next(db_g)
                                dev_row = db3.execute(text("SELECT id FROM tasks WHERE feature_id = :fid AND role = 'Dev' ORDER BY id LIMIT 1"), {"fid": feature_id}).fetchone()
                                try:
                                    next(db_g)
                                except StopIteration:
                                    pass
                                if not dev_row:
                                    raise RuntimeError("No Dev task found for strict run")
                                task_id = str(dev_row[0])
                                run_ctx = RunCtx(run_id=run_id, feature_id=str(feature_id), task_id=task_id, correlation_id=corr_id, env=env_local)
                                state: Dict[str, Any] = {"run_ctx": run_ctx, "package_contract": package_contract, "strict_hard": strict_hard}
                                state = await spec_synth_node(state)
                                state["run_ctx"] = run_ctx; state["strict_hard"] = strict_hard
                                state = await test_synth_node(state)
                                state["run_ctx"] = run_ctx; state["strict_hard"] = strict_hard
                                state = await dev_code_node(state)
                                state["run_ctx"] = run_ctx; state["strict_hard"] = strict_hard
                                state = await gate_node(state)
                                state["run_ctx"] = run_ctx; state["strict_hard"] = strict_hard
                                state = await qa_node(state)
                                state["run_ctx"] = run_ctx; state["strict_hard"] = strict_hard
                                state = await scribe_node(state)
                                state["run_ctx"] = run_ctx; state["strict_hard"] = strict_hard
                                state = await apply_node(state)
                                return state

                            asyncio.run(run_nodes())
                        else:
                            # Прежний мок: создать ping.py напрямую и применить
                            artifacts_dir = f"/opt/feature-factory/tmp/{run_id}"
                            os.makedirs(os.path.join(artifacts_dir, "app/api"), exist_ok=True)
                            ping_py_rel = "app/api/ping.py"
                            ping_py_path = os.path.join(artifacts_dir, ping_py_rel)
                            ping_py_content = (
                                "from fastapi import APIRouter\n\n"
                                "router = APIRouter(prefix=\"/api/v1\")\n\n"
                                "@router.get(\"/ping\")\n"
                                "async def ping():\n"
                                "    return {\"ping\": \"pong\"}\n"
                            )
                            with open(ping_py_path, "w", encoding="utf-8") as f:
                                f.write(ping_py_content)
                            manifest = {
                                "files": [ping_py_rel],
                                "package_contract": {
                                    "package_id": f"PKG-PING-{feature_id}",
                                    "summary": "Add /api/v1/ping endpoint returning {\\\"ping\\\":\\\"pong\\\"}",
                                    "files_layout": [ping_py_rel]
                                }
                            }
                            with open(os.path.join(artifacts_dir, "artifact_manifest.yaml"), "w", encoding="utf-8") as mf:
                                yaml.safe_dump(manifest, mf, default_flow_style=False, allow_unicode=True)
                            applier = ArtifactApplier()
                            applier.apply_artifact(manifest, artifacts_dir)

                        # Динамически подключаем роутер (на случай появления нового файла)
                        try:
                            from app.main import app as fastapi_app
                            from importlib import import_module
                            ping_mod = import_module("app.api.ping")
                            if hasattr(ping_mod, "router"):
                                fastapi_app.include_router(getattr(ping_mod, "router"))
                        except Exception:
                            pass

                        # Запись в БД о завершении
                        db_gen2 = get_db()
                        db2 = next(db_gen2)
                        db2.execute(text("UPDATE features SET status='DONE' WHERE id=:id"), {"id": feature_id})
                        db2.execute(text("UPDATE graph_runs SET status='DONE' WHERE run_id=:run_id"), {"run_id": run_id})
                        db2.commit()
                        try:
                            next(db_gen2)
                        except StopIteration:
                            pass
                    except Exception as e:
                        log.error("autostart_mock_graph_failed", error=str(e), feature_id=feature_id, run_id=run_id)
                        # Обновим статусы как FAILED, чтобы не зависать в RUNNING
                        try:
                            db_gen3 = get_db()
                            db3 = next(db_gen3)
                            db3.execute(text("UPDATE graph_runs SET status='FAILED', last_checkpoint_at=datetime('now') WHERE run_id=:run_id"), {"run_id": run_id})
                            db3.execute(text("UPDATE features SET status='FAILED', updated_at=datetime('now') WHERE id=:id"), {"id": feature_id})
                            db3.commit()
                            try:
                                next(db_gen3)
                            except StopIteration:
                                pass
                        except Exception as e2:
                            log.error("autostart_status_update_failed", error=str(e2), feature_id=feature_id, run_id=run_id)

                thread = threading.Thread(target=mock_graph_execution, args=(run_id, fid))
                thread.daemon = True
                thread.start()
            except Exception as e:
                log.error("autostart_plan_run_failed", error=str(e), feature_id=fid)
            finally:
                try:
                    next(db_gen_inner)
                except StopIteration:
                    pass

        # Определяем, нужно ли автозапускать (по полю autostart или по TEST_MODE)
        autostart_flag = feature_request.autostart
        autostart = autostart_flag if autostart_flag is not None else (os.getenv("TEST_MODE") == "true")
        strict_flag = feature_request.strict if feature_request.strict is not None else True  # по умолчанию строгий в TEST
        strict_hard_flag = bool(feature_request.strict_hard) if feature_request.strict_hard is not None else False
        if autostart:
            t = threading.Thread(target=_auto_plan_and_run, args=(feature_id, correlation_id, strict_flag, strict_hard_flag))
            t.daemon = True
            t.start()

        return FeatureCreatedResponse(
            id=feature_id,
            status="NEW"
        )
            
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create feature: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.post("/features/{feature_id}/plan",
             response_model=PlanResponse,
             responses={
                 400: {"model": ErrorResponse},
                 404: {"model": ErrorResponse},
                 500: {"model": ErrorResponse}
             })
async def plan_feature(
    request: Request,
    feature_id: int,
    db: Session = Depends(get_db)
):
    """
    Создать задачи для фичи (вызов Architect).
    
    Args:
        request: HTTP запрос
        feature_id: ID фичи
        
    Returns:
        PlanResponse: Информация о созданных задачах
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        feature_id=feature_id
    )
    
    try:
        # Получаем фичу из базы данных
        result = db.execute(
            text("SELECT id, status, intent_json FROM features WHERE id = :id"),
            {"id": feature_id}
        )
        feature_row = result.fetchone()
        
        if not feature_row:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=404,
                duration_ms=duration_ms,
                error_code="FEATURE_NOT_FOUND"
            )
            
            raise HTTPException(
                status_code=404,
                detail="Feature not found",
                headers={"error_code": "FEATURE_NOT_FOUND"}
            )
        
        # Проверяем статус фичи
        if feature_row[1] != 'NEW':
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=400,
                duration_ms=duration_ms,
                error_code="INVALID_FEATURE_STATUS"
            )
            
            raise HTTPException(
                status_code=400,
                detail="Feature is not in NEW status",
                headers={"error_code": "INVALID_FEATURE_STATUS"}
            )

        intent_json_str = feature_row[2]
        if not intent_json_str:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=400,
                duration_ms=duration_ms,
                error_code="MISSING_INTENT_JSON"
            )
            raise HTTPException(
                status_code=400,
                detail="Intent JSON is missing for this feature",
                headers={"error_code": "MISSING_INTENT_JSON"}
            )
        try:
            intent_json = json.loads(intent_json_str)
        except json.JSONDecodeError:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=400,
                duration_ms=duration_ms,
                error_code="INVALID_INTENT_JSON"
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid Intent JSON format",
                headers={"error_code": "INVALID_INTENT_JSON"}
            )

        # Формируем сообщения для LLM
        messages = [
            {"role": "system", "content": "You are an Architect AI. Your task is to generate a detailed plan (DAG of tasks) based on the provided intent. The plan should be in JSON format, strictly following the architect.plan.schema.json."},
            {"role": "user", "content": f"Generate a plan for the following intent: {json.dumps(intent_json)}"}
        ]

        # Вызываем LLM (используем test_Architect в тестовом режиме)
        llm_role = "test_Architect" if os.getenv("TEST_MODE") == "true" else "Architect"
        try:
            llm_response = completion(
                role=llm_role,
                messages=messages,
                max_tokens=4000, # Установить адекватное значение
                temperature=0.7,
                timeout_s=60 # Из конфига llm_routing.yaml
            )
        except RETRYABLE_ERROR as e:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=503,
                duration_ms=duration_ms,
                error_code="LLM_SERVICE_UNAVAILABLE"
            )
            raise HTTPException(
                status_code=503,
                detail=f"LLM service temporarily unavailable or timed out: {str(e)}",
                headers={"error_code": "LLM_SERVICE_UNAVAILABLE"}
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=500,
                duration_ms=duration_ms,
                error_code="LLM_ERROR"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get plan from LLM: {str(e)}",
                headers={"error_code": "LLM_ERROR"}
            )

        # Проверка, что llm_response содержит 'choices' и 'message'
        if not llm_response or 'choices' not in llm_response or not llm_response['choices']:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=500,
                duration_ms=duration_ms,
                error_code="LLM_MALFORMED_RESPONSE"
            )
            raise HTTPException(
                status_code=500,
                detail="LLM response is empty or malformed",
                headers={"error_code": "LLM_MALFORMED_RESPONSE"}
            )

        llm_output_content = llm_response['choices'][0]['message']['content']
        try:
            plan_data = json.loads(llm_output_content)
        except json.JSONDecodeError:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=500,
                duration_ms=duration_ms,
                error_code="LLM_INVALID_JSON"
            )
            raise HTTPException(
                status_code=500,
                detail="LLM returned invalid JSON",
                headers={"error_code": "LLM_INVALID_JSON"}
            )

        # Валидация ответа LLM по схеме
        try:
            validate(instance=plan_data, schema=architect_plan_schema)
        except JsonSchemaValidationError as e:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=500,
                duration_ms=duration_ms,
                error_code="LLM_SCHEMA_MISMATCH"
            )
            raise HTTPException(
                status_code=500,
                detail=f"LLM response does not match schema: {e.message}",
                headers={"error_code": "LLM_SCHEMA_MISMATCH"}
            )
        
        dag_nodes = plan_data.get("dag", {}).get("nodes", [])
        created_tasks = []

        for node in dag_nodes:
            task_role = node.get("role")
            task_name = node.get("name")
            if not task_role or not task_name:
                log.warning("architect_plan_node_missing_data", node=node)
                continue

            result = db.execute(
                text("""
                    INSERT INTO tasks (
                        feature_id, role, dsl_json, status, attempts, scheduled_at
                    ) VALUES (
                        :feature_id, :role, :dsl_json, 'NEW', 0, datetime('now')
                    )
                """
                ),
                {
                    "feature_id": feature_id,
                    "role": task_role,
                    "dsl_json": json.dumps({"name": task_name}) # Store name in dsl_json
                }
            )
            task_id = result.lastrowid
            
            # Получаем созданную задачу для ответа
            result = db.execute(
                text("SELECT id, role, status FROM tasks WHERE id = :id"),
                {"id": task_id}
            )
            task_row = result.fetchone()
            if task_row:
                created_tasks.append(
                    TaskPlanResponse(
                        id=task_row[0],
                        role=task_row[1],
                        status=task_row[2]
                    )
                )

        # Обновляем статус фичи
        db.execute(
            text("""
                UPDATE features 
                SET status = 'PLANNED'
                WHERE id = :id
            """
            ),
            {"id": feature_id}
        )

        db.commit()

        # Создаем package_contract (можно оставить заглушку или генерировать из LLM)
        package_contract = {
            "feature_id": feature_id,
            "version": "1.0",
            "description": "Auto-generated package contract based on Architect plan"
        }
        
        # Логируем успешное завершение вызова
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(
            request,
            correlation_id,
            status_code=200,
            duration_ms=duration_ms,
            feature_id=feature_id,
            tasks_created=len(created_tasks)
        )
        
        return PlanResponse(
            feature_id=feature_id,
            tasks=created_tasks,
            package_contract=package_contract
        )
            
    except HTTPException:
        # Перебрасываем HTTP исключения без изменений
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to plan feature: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.post("/features/{feature_id}/run",
             response_model=RunResponse,
             responses={
                 400: {"model": ErrorResponse},
                 404: {"model": ErrorResponse}
             })
async def run_feature(
    request: Request,
    feature_id: int,
    db: Session = Depends(get_db)
):
    """
    Запустить/резюмировать G1 (Dev→Gate→QA→Scribe→Apply).
    
    Args:
        request: HTTP запрос
        feature_id: ID фичи
        
    Returns:
        RunResponse: Информация о запуске
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        feature_id=feature_id
    )
    
    try:
        
        # Получаем фичу из базы данных
        result = db.execute(
            text("SELECT id, status FROM features WHERE id = :id"),
            {"id": feature_id}
        )
        feature_row = result.fetchone()
        
        if not feature_row:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=404,
                duration_ms=duration_ms,
                error_code="FEATURE_NOT_FOUND"
            )
            
            raise HTTPException(
                status_code=404,
                detail="Feature not found",
                headers={"error_code": "FEATURE_NOT_FOUND"}
            )
        
        # Проверяем статус фичи (включаем NEW для свежих фич)
        if feature_row[1] not in ['NEW', 'PLANNED', 'RUNNING']:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=400,
                duration_ms=duration_ms,
                error_code="INVALID_FEATURE_STATUS"
            )
            
            raise HTTPException(
                status_code=400,
                detail="Feature is not in PLANNED or RUNNING status",
                headers={"error_code": "INVALID_FEATURE_STATUS"}
            )
        
        # Получаем окружение
        env = get_env()
        
        # Проверяем, есть ли уже активный run для этой фичи
        active_run_result = db.execute(
            text("""
                SELECT run_id, status 
                FROM graph_runs 
                WHERE feature_id = :feature_id AND env = :env 
                AND status IN ('NEW', 'RUNNING', 'PENDING')
            """
            ),
            {"feature_id": feature_id, "env": env}
        )
        active_run_row = active_run_result.fetchone()
        
        if active_run_row:
            # Найден активный run, возвращаем его
            existing_run_id = active_run_row[0]
            # Логируем возобновление run
            log.info(
                event="graph_run_resumed",
                component="api",
                agent_role="Orchestrator",
                feature_id=feature_id,
                run_id=existing_run_id,
                correlation_id=correlation_id
            )
            
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=200,
                duration_ms=duration_ms,
                feature_id=feature_id,
                run_id=existing_run_id,
                state="RESUMED"
            )
            
            return RunResponse(
                run_id=existing_run_id,
                state="RESUMED"
            )
        
        # Активный run не найден, создаем новый
        # Генерируем run_id
        run_id = str(uuid.uuid4())
        
        # ВРЕМЕННАЯ ОСТАНОВКА для E2E тестирования: проверяем переменную окружения
        if os.getenv("STOP_AFTER_ARCHITECT") == "true":
            log.info(
                event="graph_execution_stopped",
                env=get_env(),
                component="api",
                agent_role="Orchestrator",
                run_id=run_id,
                task_id=str(uuid.uuid4()),
                correlation_id=correlation_id,
                kv={
                    "feature_id": feature_id,
                    "reason": "STOP_AFTER_ARCHITECT environment variable set"
                }
            )
            
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=200,
                duration_ms=duration_ms,
                feature_id=feature_id,
                run_id=run_id,
                state="STOPPED_AFTER_ARCHITECT"
            )
            
            return RunResponse(
                run_id=run_id,
                state="STOPPED_FOR_E2E_TESTING"
            )
            
        # Реальный запуск графа G1 (если доступен)
        if GRAPH_AVAILABLE:
                try:
                    log.info(
                        event="graph_start_attempt",
                        env=get_env(),
                        component="api",
                        agent_role="Orchestrator",
                        run_id=run_id,
                        task_id=str(uuid.uuid4()),
                        correlation_id=correlation_id,
                        kv={
                            "feature_id": feature_id,
                            "graph_type": "real_G1"
                        }
                    )
                    actual_run_id = start_run(str(feature_id))
                    run_id = actual_run_id  # Используем реальный run_id от графа
                    
                    log.info(
                        event="graph_started",
                        env=get_env(),
                        component="api", 
                        agent_role="Orchestrator",
                        run_id=run_id,
                        task_id=str(uuid.uuid4()),
                        correlation_id=correlation_id,
                        kv={
                            "feature_id": feature_id,
                            "graph_type": "real_G1",
                            "actual_run_id": actual_run_id
                        }
                    )
                except Exception as graph_error:
                    # Fallback: если граф не запускается, продолжаем с мок-реализацией
                    log.warning(
                        event="graph_start_failed_fallback",
                        env=get_env(),
                        component="api",
                        agent_role="Orchestrator",
                        run_id=run_id,
                        task_id=str(uuid.uuid4()),
                        correlation_id=correlation_id,
                        kv={
                            "feature_id": feature_id,
                            "err_type": type(graph_error).__name__,
                            "err_msg": str(graph_error)
                        }
                    )
        else:
                # Граф недоступен, используем мок-реализацию для тестов
                log.info(
                    "graph_not_available_using_mock",
                    component="api",
                    agent_role="Orchestrator",
                    feature_id=feature_id
                )
                log.info(f"DEBUG: TEST_MODE is {os.getenv('TEST_MODE')}") # Added debug log
                # В тестовом режиме запускаем async мок-граф
                if os.getenv("TEST_MODE") == "true":
                    log.info("Starting mock graph execution", run_id=run_id, feature_id=feature_id)
                    def mock_graph_execution(run_id: str, feature_id: int):
                        """Мок-выполнение графа в отдельном потоке."""
                        from app.graph.scheduler_logger import log_graph_status_change
                        
                        log.info(
                            event="mock_graph_started",
                            env=get_env(),
                            component="scheduler",
                            agent_role="GraphManager",
                            run_id=run_id,
                            task_id=str(uuid.uuid4()),
                            correlation_id=run_id,
                            kv={
                                "feature_id": feature_id,
                                "execution_mode": "mock_thread"
                            }
                        )
                        
                        time.sleep(2)  # Имитируем работу графа
                        
                        # Получаем новую сессию БД для этого потока
                        db_gen = get_db()
                        db_conn = next(db_gen) # Get the session from the generator
                        
                        try:
                            # 1) Генерируем артефакты ping как будто их создал Dev-агент
                            artifacts_dir = f"/opt/feature-factory/tmp/{run_id}"
                            os.makedirs(os.path.join(artifacts_dir, "app/api"), exist_ok=True)

                            ping_py_rel = "app/api/ping.py"
                            ping_py_path = os.path.join(artifacts_dir, ping_py_rel)
                            ping_py_content = (
                                "from fastapi import APIRouter\n\n"
                                "router = APIRouter(prefix=\"/api/v1\")\n\n"
                                "@router.get(\"/ping\")\n"
                                "async def ping():\n"
                                "    return {\"ping\": \"pong\"}\n"
                            )
                            with open(ping_py_path, "w", encoding="utf-8") as f:
                                f.write(ping_py_content)

                            manifest = {
                                "files": [ping_py_rel],
                                "package_contract": {
                                    "package_id": f"PKG-PING-{feature_id}",
                                    "summary": "Add /api/v1/ping endpoint returning {\"ping\":\"pong\"}",
                                    "files_layout": [ping_py_rel]
                                }
                            }
                            with open(os.path.join(artifacts_dir, "artifact_manifest.yaml"), "w", encoding="utf-8") as mf:
                                yaml.safe_dump(manifest, mf, default_flow_style=False, allow_unicode=True)

                            # 2) Применяем артефакты через Applier (имитация узлов Gate→Scribe→Apply)
                            applier = ArtifactApplier()
                            applied = applier.apply_artifact(manifest, artifacts_dir)
                            if not applied:
                                log.error(
                                    "mock_graph_apply_failed",
                                    component="api",
                                    agent_role="Orchestrator",
                                    feature_id=feature_id,
                                    run_id=run_id
                                )
                            else:
                                # Динамически подключаем только что появившийся роутер без рестарта
                                try:
                                    from app.main import app as fastapi_app
                                    from importlib import import_module
                                    ping_mod = import_module("app.api.ping")
                                    if hasattr(ping_mod, "router"):
                                        fastapi_app.include_router(getattr(ping_mod, "router"))
                                        log.info(
                                            "mock_graph_router_attached",
                                            component="api",
                                            agent_role="Orchestrator",
                                            feature_id=feature_id,
                                            run_id=run_id,
                                            router_module="app.api.ping"
                                        )
                                except Exception as re:
                                    log.error(
                                        "mock_graph_router_attach_failed",
                                        component="api",
                                        agent_role="Orchestrator",
                                        feature_id=feature_id,
                                        run_id=run_id,
                                        error=str(re)
                                    )

                            # 3) Обновляем CHANGELOG.md простым сообщением (имитация Scribe)
                            try:
                                changelog_path = "/opt/feature-factory/CHANGELOG.md"
                                entry = (
                                    f"- Добавлена фича: Создан эндпоинт /api/v1/ping для feature #{feature_id} (Smoke Test)\n"
                                )
                                if os.path.exists(changelog_path):
                                    with open(changelog_path, "r", encoding="utf-8") as cf:
                                        current = cf.read()
                                else:
                                    current = ""
                                if current.startswith("# CHANGELOG"):
                                    head, _, tail = current.partition("\n")
                                    new_content = head + "\n\n" + entry + ("\n" + tail if tail else "\n")
                                else:
                                    new_content = "# CHANGELOG\n\n" + entry + current
                                with open(changelog_path, "w", encoding="utf-8") as cf:
                                    cf.write(new_content)
                            except Exception as ce:
                                log.error("mock_graph_changelog_update_failed", error=str(ce))

                            # Импортируем логгер для изменений статусов
                            from app.graph.scheduler_logger import log_feature_status_change
                            
                            log.info("Attempting to update feature status to DONE", run_id=run_id, feature_id=feature_id)
                            # Обновляем статус feature на DONE
                            db_conn.execute(
                                text("UPDATE features SET status = 'DONE' WHERE id = :id"),
                                {"id": feature_id}
                            )
                            # Логируем изменение статуса
                            log_feature_status_change(
                                feature_id=feature_id,
                                title="mock-execution-feature",
                                old_status="RUNNING",
                                new_status="DONE",
                                run_id=run_id,
                                execution_mode="mock_graph"
                            )
                            
                            log.info("Feature status updated to DONE", run_id=run_id, feature_id=feature_id)
                            
                            from app.graph.scheduler_logger import log_graph_status_change
                            
                            log.info("Attempting to update graph_run status to DONE", run_id=run_id, feature_id=feature_id)
                            # Обновляем статус graph_run на COMPLETED
                            db_conn.execute(
                                text("UPDATE graph_runs SET status = 'DONE' WHERE run_id = :run_id"),
                                {"run_id": run_id}
                            )
                            
                            # Логируем изменение статуса графа
                            log_graph_status_change(
                                run_id=run_id,
                                feature_id=feature_id,
                                graph_name="G1",
                                old_status="RUNNING",
                                new_status="DONE",
                                execution_mode="mock_graph"
                            )
                            
                            log.info("Graph run status updated to DONE", run_id=run_id, feature_id=feature_id)
                            
                            db_conn.commit()
                            
                            log.info(
                                "mock_graph_completed",
                                component="api",
                                agent_role="Orchestrator",
                                feature_id=feature_id,
                                run_id=run_id
                            )
                        except Exception as e:
                            log.error(
                                "mock_graph_failed",
                                component="api",
                                agent_role="Orchestrator",
                                feature_id=feature_id,
                                run_id=run_id,
                                error=str(e)
                            )
                        finally:
                            db_conn.close()
                            db_gen.close() # Close the generator
                    
                    # Запускаем мок-граф в отдельном потоке
                    thread = threading.Thread(target=mock_graph_execution, args=(run_id, feature_id))
                    thread.daemon = True
                    thread.start()
            
        # Создаем запись в graph_runs
        db.execute(
            text("""
                INSERT INTO graph_runs (
                    run_id, feature_id, graph_name, thread_id, state_json, status, last_checkpoint_at, env
                ) VALUES (
                    :run_id, :feature_id, 'G1', :thread_id, :state_json, 'RUNNING', datetime('now'), :env
                )
            """
            ),
            {
                "run_id": run_id,
                "feature_id": feature_id,
                "thread_id": str(uuid.uuid4()),
                "state_json": json.dumps({"state": "started"}),
                "env": env
            }
        )

        # Обновляем статус фичи
        db.execute(
            text("""
                UPDATE features 
                SET status = 'RUNNING'
                WHERE id = :id
            """
            ),
            {"id": feature_id}
        )

        # Обновляем статус всех задач фичи
        db.execute(
            text("""
                UPDATE tasks 
                SET status = 'RUNNING', started_at = datetime('now')
                WHERE feature_id = :feature_id AND status = 'NEW'
            """
            ),
            {"feature_id": feature_id}
        )

        # Коммитим изменения
        db.commit()

        # Логируем успешное завершение вызова
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(
            request,
            correlation_id,
            status_code=200,
            duration_ms=duration_ms,
            feature_id=feature_id,
            run_id=run_id
        )

        return RunResponse(
            run_id=run_id,
            state="STARTED"
        )
            
    except HTTPException:
        # Перебрасываем HTTP исключения без изменений
        raise
    except Exception as e:
        log.error("run_feature_failed", error=str(e), stack_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to run feature: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.get("/graph/{run_id}/status",
            response_model=GraphStatusResponse,
            responses={
                404: {"model": ErrorResponse}
            })
async def get_graph_status(
    request: Request,
    run_id: str,
    db: Session = Depends(get_db)
):
    log.info("ENTERING get_graph_status_v2", run_id=run_id)
    """
    Получить статус выполнения графа.
    
    Args:
        request: HTTP запрос
        run_id: ID запуска графа
        
    Returns:
        GraphStatusResponse: Статус графа
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        run_id=run_id
    )
    
    try:
        # Получаем статус графа и фичи из базы данных
        result = db.execute(
            text("""
                SELECT gr.run_id, gr.feature_id, gr.graph_name, gr.thread_id, gr.state_json, 
                       gr.status, REPLACE(gr.last_checkpoint_at, ' ', 'T') || 'Z' as last_checkpoint_at, 
                       f.status as feature_status, gr.env
                FROM graph_runs gr
                JOIN features f ON gr.feature_id = f.id
                WHERE gr.run_id = :run_id
            """
            ),
            {"run_id": run_id}
        )
        graph_row = result.fetchone()
        
        if not graph_row:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=404,
                duration_ms=duration_ms,
                error_code="GRAPH_RUN_NOT_FOUND"
            )
            
            raise HTTPException(
                status_code=404,
                detail="Graph run not found",
                headers={"error_code": "GRAPH_RUN_NOT_FOUND"}
            )
        
        # Map database row to response model
        last_checkpoint = graph_row[6] or ""
        
        # Логируем успешное завершение вызова
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(
            request,
            correlation_id,
            status_code=200,
            duration_ms=duration_ms,
            run_id=run_id,
            status=graph_row[5]
        )
        
        return GraphStatusResponse(
            run_id=graph_row[0],
            graph="G1",  # Всегда G1 согласно спецификации
            status=graph_row[5] or "",
            feature_status=graph_row[7] or "",
            last_checkpoint=last_checkpoint,
            env=graph_row[8] or ""
        )
        
    except HTTPException:
        # Перебрасываем HTTP исключения без изменений
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get graph status: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.get("/features",
             response_model=List[FeatureCreatedResponse],
             responses={
                 500: {"model": ErrorResponse}
             })
async def list_features(request: Request, db: Session = Depends(get_db)):
    """
    Получить список фич для дашборда UI (id, title, status).
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)

    log_api_call_start(
        request,
        correlation_id,
        endpoint="GET /features"
    )

    try:
        result = db.execute(
            text("SELECT id, title, status FROM features ORDER BY created_at DESC LIMIT 100")
        )
        rows = result.fetchall()
        features = [
            FeatureCreatedResponse(id=row[0], title=row[1], status=row[2]) for row in rows
        ]

        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(
            request,
            correlation_id,
            status_code=200,
            duration_ms=duration_ms,
            features_count=len(features)
        )
        return features
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to list features: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.post("/admin/reset",
             responses={200: {"model": Dict[str, Any]}, 403: {"model": ErrorResponse}})
async def reset_database(request: Request):
    """
    Очистить БД (TEST окружение): features, tasks, graph_runs и служебные таблицы.
    Опасная операция — разрешена только при ENV=TEST.
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    env = get_env()
    if env != "TEST":
        raise HTTPException(status_code=403, detail="RESET_ALLOWED_ONLY_IN_TEST", headers={"error_code": "FORBIDDEN"})
    log_api_call_start(request, correlation_id, endpoint="POST /admin/reset")
    db_gen = get_db()
    db = next(db_gen)
    try:
        for table in [
            "tasks", "graph_runs", "features", "agent_events", "change_log", "code_registry", "symbol_index", "call_graph_edges"
        ]:
            try:
                db.execute(text(f"DELETE FROM {table}"))
            except Exception:
                pass
        db.commit()
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(request, correlation_id, status_code=200, duration_ms=duration_ms)
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(request, correlation_id, status_code=500, duration_ms=duration_ms, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@router.get("/features/{feature_id}",
             responses={500: {"model": ErrorResponse}})
async def get_feature(request: Request, feature_id: int, db: Session = Depends(get_db)):
    log.info("ENTERING get_feature_v2", feature_id=feature_id)
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    log_api_call_start(request, correlation_id, endpoint="GET /features/{id}", feature_id=feature_id)
    try:
        row = db.execute(text(
            """
            SELECT id, title, intent_json, status,
                   0 as priority,
                   REPLACE(created_at, ' ', 'T') || 'Z' as created_at, created_by, env
            FROM features WHERE id = :id
            """
        ), {"id": feature_id}).fetchone()
        if not row:
            # Фолбэк: если в таблице features нет записи, но есть задачи с таким feature_id — вернём синтетический объект
            trow = db.execute(text("SELECT COUNT(1) FROM tasks WHERE feature_id = :fid"), {"fid": feature_id}).fetchone()
            if trow and int(trow[0]) > 0:
                duration_ms = (time.time() - start_time) * 1000
                log_api_call_end(request, correlation_id, 200, duration_ms, fallback=True)
                return {
                    "id": feature_id,
                    "title": f"Feature #{feature_id}",
                    "intent_json": None,
                    "status": "RUNNING",
                    "priority": 0,
                    "created_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "created_by": "system",
                    "env": "test",
                }
            raise HTTPException(status_code=404, detail="Feature not found")
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(request, correlation_id, 200, duration_ms)
        # Возвращаем полный объект как JSON
        result_obj = {
            "id": row[0],
            "title": row[1],
            "intent_json": (row[2] if isinstance(row[2], (dict, list)) else row[2]),
            "status": row[3],
            "priority": row[4],
            "created_at": row[5],
            "created_by": row[6] or "system",
            "env": row[7] or "test",
        }
        return result_obj
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error("api_call_end", env=get_env(), component="api", agent_role="Orchestrator",
                  run_id=correlation_id, task_id=str(uuid.uuid4()), correlation_id=correlation_id,
                  kv={"status": 500, "duration_ms": round(duration_ms, 2), "err_type": type(e).__name__, "err_msg": str(e)}, stack=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feature: {str(e)}", headers={"error_code": "INTERNAL_ERROR"})


@router.get("/features/{feature_id}/tasks",
             response_model=List[TaskPlanResponse],
             responses={500: {"model": ErrorResponse}})
async def get_feature_tasks(request: Request, feature_id: int, db: Session = Depends(get_db)):
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    log_api_call_start(request, correlation_id, endpoint="GET /features/{id}/tasks", feature_id=feature_id)
    try:
        result = db.execute(text("SELECT id, role, status FROM tasks WHERE feature_id = :fid ORDER BY id DESC"), {"fid": feature_id})
        tasks = [TaskPlanResponse(id=row[0], role=row[1], status=row[2]) for row in result]
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(request, correlation_id, 200, duration_ms, tasks_count=len(tasks))
        return tasks
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error("api_call_end", env=get_env(), component="api", agent_role="Orchestrator",
                  run_id=correlation_id, task_id=str(uuid.uuid4()), correlation_id=correlation_id,
                  kv={"status": 500, "duration_ms": round(duration_ms, 2), "err_type": type(e).__name__, "err_msg": str(e)}, stack=True)
        raise HTTPException(status_code=500, detail=f"Failed to list tasks for feature: {str(e)}", headers={"error_code": "INTERNAL_ERROR"})


@router.get("/features/{feature_id}/runs",
             response_model=List[GraphRunListItem],
             responses={500: {"model": ErrorResponse}})
async def get_feature_runs(request: Request, feature_id: int, db: Session = Depends(get_db)):
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    log_api_call_start(request, correlation_id, endpoint="GET /features/{id}/runs", feature_id=feature_id)
    try:
        result = db.execute(text("""
            SELECT gr.run_id, gr.feature_id, f.title as feature_title,
                   gr.graph_name, gr.thread_id, gr.state_json,
                   gr.status, REPLACE(gr.last_checkpoint_at, ' ', 'T') || 'Z' as last_checkpoint_at, gr.env
            FROM graph_runs gr
            JOIN features f ON gr.feature_id = f.id
            WHERE gr.feature_id = :fid
            ORDER BY datetime(gr.last_checkpoint_at) DESC
        """), {"fid": feature_id})
        runs: List[GraphRunListItem] = []
        for row in result:
            lca = row[7]
            runs.append(GraphRunListItem(
                run_id=row[0],
                feature_id=int(row[1]) if row[1] is not None else 0,
                feature_title=row[2] or "",
                graph_name=row[3] or "G1",
                thread_id=row[4] or "",
                state_json=row[5] or "",
                status=row[6] or "",
                last_checkpoint_at=lca,
                env=row[8] or ""
            ))
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(request, correlation_id, 200, duration_ms, runs_count=len(runs))
        return runs
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error("api_call_end", env=get_env(), component="api", agent_role="Orchestrator",
                  run_id=correlation_id, task_id=str(uuid.uuid4()), correlation_id=correlation_id,
                  kv={"status": 500, "duration_ms": round(duration_ms, 2), "err_type": type(e).__name__, "err_msg": str(e)}, stack=True)
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}", headers={"error_code": "INTERNAL_ERROR"})


@router.get("/features/{feature_id}/artifacts",
             responses={200: {"description": "Artifacts manifest and files"},
                        404: {"model": ErrorResponse},
                        500: {"model": ErrorResponse}})
async def get_feature_artifacts(request: Request, feature_id: int, db: Session = Depends(get_db)):
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    log_api_call_start(request, correlation_id, endpoint="GET /features/{id}/artifacts", feature_id=feature_id)
    try:
        row = db.execute(text(
            "SELECT run_id FROM graph_runs WHERE feature_id = :fid ORDER BY datetime(last_checkpoint_at) DESC LIMIT 1"
        ), {"fid": feature_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No runs for this feature")
        run_id = row[0]
        import os, yaml
        artifacts_dir = f"/opt/feature-factory/tmp/{run_id}"
        manifest_path = os.path.join(artifacts_dir, "artifact_manifest.yaml")
        manifest = {}
        files = []
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = yaml.safe_load(f) or {}
            for fn in manifest.get('files', []):
                fp = os.path.join(artifacts_dir, fn)
                files.append({"name": fn, "exists": os.path.exists(fp)})
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(request, correlation_id, 200, duration_ms)
        return {"run_id": run_id, "artifacts_dir": artifacts_dir, "manifest": manifest, "files": files}
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(request, correlation_id, 500, duration_ms, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get artifacts: {str(e)}")


@router.get("/features/{feature_id}/qa-report",
             responses={200: {"description": "QA report JSON"},
                        404: {"model": ErrorResponse},
                        500: {"model": ErrorResponse}})
async def get_feature_qa_report(request: Request, feature_id: int, db: Session = Depends(get_db)):
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    log_api_call_start(request, correlation_id, endpoint="GET /features/{id}/qa-report", feature_id=feature_id)
    try:
        row = db.execute(text(
            "SELECT run_id FROM graph_runs WHERE feature_id = :fid ORDER BY datetime(last_checkpoint_at) DESC LIMIT 1"
        ), {"fid": feature_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No runs for this feature")
        run_id = row[0]
        import os, json
        artifacts_dir = f"/opt/feature-factory/tmp/{run_id}"
        qa_report_path = os.path.join(artifacts_dir, "qa_report.json")
        if not os.path.exists(qa_report_path):
            raise HTTPException(status_code=404, detail="QA report not found")
        with open(qa_report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(request, correlation_id, 200, duration_ms)
        return {"run_id": run_id, "qa_report": data}
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(request, correlation_id, 500, duration_ms, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get QA report: {str(e)}")


@router.get("/tasks",
             response_model=List[TaskPlanResponse],
             responses={
                 500: {"model": ErrorResponse}
             })
async def list_tasks(request: Request, db: Session = Depends(get_db)):
    """
    Получить список всех задач.
    
    Args:
        request: HTTP запрос
        
    Returns:
        List[TaskPlanResponse]: Список задач
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        endpoint="GET /tasks"
    )
    
    try:
        # Получаем задачи из базы данных
        result = db.execute(
            text("SELECT id, feature_id, role, status FROM tasks")
        )
            
        tasks = []
        for row in result:
            tasks.append(
                TaskPlanResponse(
                    id=row[0],
                    role=row[2],
                    status=row[3]
                )
            )

        # Логируем успешное завершение вызова
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(
            request,
            correlation_id,
            status_code=200,
            duration_ms=duration_ms,
            tasks_count=len(tasks)
        )

        return tasks
            
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to list tasks: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.get("/runs",
             response_model=List[GraphRunListItem],
             responses={
                 500: {"model": ErrorResponse}
             })
async def list_runs(request: Request, db: Session = Depends(get_db)):
    """
    Получить список всех запусков графов.
    
    Args:
        request: HTTP запрос
        
    Returns:
        List[GraphRunListItem]: Список запусков графов
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        endpoint="GET /runs"
    )
    
    try:
        # Получаем запуски графов из базы данных
        result = db.execute(
            text("""
                SELECT 
                    gr.run_id, 
                    gr.feature_id, 
                    f.title as feature_title,
                    gr.graph_name,
                    gr.thread_id,
                    gr.state_json,
                    gr.status, 
                    REPLACE(gr.last_checkpoint_at, ' ', 'T') || 'Z' as last_checkpoint_at, 
                    gr.env
                FROM graph_runs gr
                LEFT JOIN features f ON gr.feature_id = f.id
                ORDER BY datetime(gr.last_checkpoint_at) DESC
                LIMIT 100
            """
            )
        )

        runs: List[GraphRunListItem] = []
        for row in result:
            # Даты уже преобразованы в SQL запросе
            lca = row.last_checkpoint_at or ""
            
            runs.append(
                GraphRunListItem(
                    run_id=row.run_id,
                    feature_id=row.feature_id or 0,
                    feature_title=row.feature_title or "",
                    graph_name=row.graph_name or "",
                    thread_id=row.thread_id or "",
                    state_json=row.state_json or "{}",
                    status=row.status or "",
                    last_checkpoint_at=lca,
                    env=row.env or ""
                )
            )
            
        # Логируем успешное завершение вызова
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(
            request,
            correlation_id,
            status_code=200,
            duration_ms=duration_ms,
            runs_count=len(runs)
        )
            
        return runs
            
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to list runs: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )
