#!/usr/bin/env python3
"""
Планировщик оркестратора для цикла "самовыполнения" из бэклога.
"""

import asyncio
import json
import time
import uuid
import structlog
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Настройка логгера
logger = structlog.get_logger()

# Интервал проверки бэклога (в секундах)
DEFAULT_CHECK_INTERVAL = 10  # Можно настроить через конфигурацию
CHECK_INTERVAL = int(os.getenv("ORCH_LOOP_INTERVAL_SEC", DEFAULT_CHECK_INTERVAL))

# Флаг включения цикла
LOOP_ENABLED = os.getenv("ORCH_LOOP_ENABLED", "false").lower() == "true"

# Параметры retry и backoff для задач
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 5  # секунды

# Импортируем функцию для получения счетчика токенов
from app.llm.token_accountant import get_token_accountant

# Импортируем функции для работы с БД
from app.db.session import get_db
from app.db.guard import get_db_connection_string

# Импортируем менеджер блокировок
from app.orchestrator.lock_manager import lock_manager, parse_resource_locks_from_plan
from app.context.packager import ContextPackager
from app.graph.nodes.dev_code import dev_code_node
from app.graph.types import RunCtx
from app.logging_helpers import get_env
from app.services.git_integration import GitIntegrationService, GitIntegrationError

# Получаем DATABASE_URL из переменных окружения или используем тестовую базу
DATABASE_URL = get_db_connection_string()
# Для SQLAlchemy engine нам все еще нужен engine, но будем использовать get_db для сессий
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class OrchestratorLoop:
    """Планировщик оркестратора для цикла "самовыполнения" из бэклога."""
    
    def __init__(self):
        """Инициализирует планировщик."""
        self.running = False
        self.session = None
        # Инициализируем упаковщик контекста (RAG)
        try:
            self.packager = ContextPackager()
        except Exception:
            self.packager = None
    
    async def start(self):
        """Запускает цикл планировщика."""
        logger.info("orchestrator_loop_started", component="orchestrator")
        self.running = True
        
        try:
            while self.running:
                try:
                    # Обрабатываем бэклог
                    await self._process_backlog()
                    
                    # Ждем до следующей итерации
                    await asyncio.sleep(CHECK_INTERVAL)
                    
                except Exception as e:
                    logger.error(
                        "orchestrator_loop_error",
                        component="orchestrator",
                        err_type=type(e).__name__,
                        error=str(e)
                    )
                    # Продолжаем работу даже при ошибке
                    await asyncio.sleep(CHECK_INTERVAL)
                    
        except asyncio.CancelledError:
            logger.info("orchestrator_loop_cancelled", component="orchestrator")
        finally:
            await self.stop()
    
    async def stop(self):
        """Останавливает цикл планировщика."""
        logger.info("orchestrator_loop_stopped", component="orchestrator")
        self.running = False
        
        if self.session:
            self.session.close()
    
    async def _process_backlog(self):
        """Обрабатывает бэклог - новые фичи и задачи."""
        try:
            # Создаем сессию
            self.session = SessionLocal()
            
            # Обрабатываем новые фичи
            await self._process_new_features()
            
            # Обрабатываем новые задачи
            await self._process_new_tasks()
            
            # Обрабатываем задачи в состоянии WAIT_BUDGET
            await self._process_wait_budget_tasks()

            # Проверяем и обновляем статус фичи
            await self._check_and_update_feature_status()
            
        except Exception as e:
            logger.error(
                "backlog_processing_error",
                component="orchestrator",
                err_type=type(e).__name__,
                error=str(e)
            )
        finally:
            if self.session:
                self.session.close()
                self.session = None
    
    async def _process_new_features(self):
        """Обрабатывает новые фичи."""
        try:
            # Выбираем фичи со статусом NEW и PLANNED
            result = self.session.execute(
                text("""
                    SELECT id, title, intent_json, created_by, env, status
                    FROM features 
                    WHERE status IN ('NEW', 'PLANNED')
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 10
                """)
            )
            
            features = result.fetchall()
            
            for feature_row in features:
                feature_id = feature_row[0]
                feature_title = feature_row[1]
                intent_json = feature_row[2]
                created_by = feature_row[3]
                env = feature_row[4]
                status = feature_row[5]
                plan_dsl_json = None
                
                logger.info(
                    "processing_feature",
                    component="orchestrator",
                    feature_id=feature_id,
                    feature_title=feature_title,
                    created_by=created_by,
                    env=env,
                    status=status
                )
                
                try:
                    if status == 'NEW':
                        # Проверяем, есть ли уже план для этой фичи
                        task_result = self.session.execute(
                            text("""
                                SELECT COUNT(*) 
                                FROM tasks 
                                WHERE feature_id = :feature_id
                            """),
                            {"feature_id": feature_id}
                        )
                        
                        task_count = task_result.fetchone()[0]
                        
                        if task_count == 0:
                            # Нужно сгенерировать план через Architect
                            await self._generate_plan_for_feature(feature_id, feature_title, intent_json, created_by, env)
                        else:
                            # План уже есть, обновляем статус фичи
                            self.session.execute(
                                text("""
                                    UPDATE features 
                                    SET status = 'PLANNED'
                                    WHERE id = :feature_id
                                """),
                                {"feature_id": feature_id}
                            )
                            self.session.commit()
                            
                            logger.info(
                                "feature_planned",
                                component="orchestrator",
                                feature_id=feature_id,
                                feature_title=feature_title
                            )
                    
                    elif status == 'PLANNED':
                        # Фича запланирована, проверяем блокировки ресурсов
                        await self._check_and_acquire_locks_for_feature(feature_id, feature_title, plan_dsl_json)
                        
                except Exception as e:
                    logger.error(
                        "feature_processing_error",
                        component="orchestrator",
                        feature_id=feature_id,
                        err_type=type(e).__name__,
                        error=str(e)
                    )
                    
        except Exception as e:
            logger.error(
                "new_features_processing_error",
                component="orchestrator",
                err_type=type(e).__name__,
                error=str(e)
            )
    
    async def _generate_plan_for_feature(self, feature_id: int, title: str, intent_json: str, created_by: str, env: str):
        """
        Генерирует план для фичи через Architect.
        
        Args:
            feature_id: ID фичи
            title: Название фичи
            intent_json: JSON с описанием намерения
            created_by: Автор фичи
            env: Окружение
        """
        try:
            logger.info(
                "generating_plan_for_feature",
                component="orchestrator",
                feature_id=feature_id,
                feature_title=title
            )
            
            # В реальной реализации здесь будет вызов Architect
            # Для демонстрации создадим простой план по DSL
            
            # Создаем план DSL с блокировками ресурсов
            plan_dsl = {
                "dag": {
                    "tasks": [
                        {
                            "id": str(uuid.uuid4()),
                            "name": f"implement_{title.lower().replace(' ', '_')}",
                            "kind": "code",
                            "role": "Dev",
                            "preconditions": [],
                            "postconditions": [f"feature_{feature_id}_implemented"],
                            "idempotency_key": f"dev.feature.{feature_id}.v1",
                            "retry": {"max": 2, "backoff": "exp:5,30,120"},
                            "deadline": "PT30M",
                            "models": ["qwen", "gemini-fallback"],
                            "outputs": ["files"],
                            "dod": ["Код реализован согласно схеме", "Юнит-тесты написаны"],
                            "severity": "high"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "name": f"test_{title.lower().replace(' ', '_')}",
                            "kind": "test",
                            "role": "QA",
                            "preconditions": [f"feature_{feature_id}_implemented"],
                            "postconditions": [f"feature_{feature_id}_tested"],
                            "idempotency_key": f"qa.tests.{feature_id}.v1",
                            "retry": {"max": 1, "backoff": "exp:10,60"},
                            "deadline": "PT20M",
                            "models": ["gemini-fallback"],
                            "outputs": ["tests", "report"],
                            "dod": ["Интеграционные тесты пройдены", "E2E тесты выполнены"],
                            "severity": "med"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "name": f"document_{title.lower().replace(' ', '_')}",
                            "kind": "doc",
                            "role": "Scribe",
                            "preconditions": [f"feature_{feature_id}_tested"],
                            "postconditions": [f"feature_{feature_id}_documented"],
                            "idempotency_key": f"scribe.docs.{feature_id}.v1",
                            "retry": {"max": 1, "backoff": "exp:10,60"},
                            "deadline": "PT15M",
                            "models": ["gemini-fallback"],
                            "outputs": ["docs"],
                            "dod": ["Документация обновлена", "CHANGELOG дополнен"],
                            "severity": "low"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "name": f"apply_{title.lower().replace(' ', '_')}",
                            "kind": "apply",
                            "role": "Apply",
                            "preconditions": [f"feature_{feature_id}_documented"],
                            "postconditions": [f"feature_{feature_id}_applied"],
                            "idempotency_key": f"apply.gitops.{feature_id}.v1",
                            "retry": {"max": 2, "backoff": "exp:10,60,180"},
                            "deadline": "PT45M",
                            "models": ["qwen", "gemini-fallback"],
                            "outputs": ["git_branch", "pr_url", "commit_sha"],
                            "dod": ["Git ветка создана", "PR создан", "Изменения применены"],
                            "severity": "high"
                        }
                    ]
                },
                "budgets": {
                    "total_tokens": 5000
                },
                "dod": ["Фича реализована", "Тесты пройдены", "Документация обновлена"],
                "resource_locks": [
                    {"resource": "feature_pipeline", "mode": "exclusive"}
                ]
            }
            
            # Создаем записи в БД для каждой задачи 
            dsl_tasks = plan_dsl["dag"]["tasks"]
            
            # Создаем записи в БД для каждой задачи
            for dsl_task in dsl_tasks:
                self.session.execute(
                    text("""
                        INSERT INTO tasks (
                            feature_id, role, dsl_json, status, attempts, budget_tokens, scheduled_at
                        ) VALUES (
                            :feature_id, :role, :dsl_json, 'NEW', 0, :budget_tokens, datetime('now')
                        )
                    """),
                    {
                        "feature_id": feature_id,
                        "role": dsl_task["role"],
                        "dsl_json": json.dumps(dsl_task),
                        "budget_tokens": 1000  # Оценка по умолчанию
                    }
                )
            
            # Обновляем статус фичи (минимальная TEST-схема — без plan_dsl_json)
            self.session.execute(
                text("""
                    UPDATE features 
                    SET status = 'PLANNED'
                    WHERE id = :feature_id
                """),
                {"feature_id": feature_id}
            )
            
            self.session.commit()
            
            logger.info(
                "plan_generated_for_feature",
                component="orchestrator",
                feature_id=feature_id,
                feature_title=title,
                tasks_created=len(dsl_tasks)
            )
            
        except Exception as e:
            logger.error(
                "plan_generation_error",
                component="orchestrator",
                feature_id=feature_id,
                err_type=type(e).__name__,
                error=str(e)
            )
            
            # Откатываем транзакцию в случае ошибки
            self.session.rollback()
    
    async def _check_and_acquire_locks_for_feature(self, feature_id: int, feature_title: str, plan_dsl_json: str):
        """
        Проверяет доступность ресурсов и захватывает блокировки для фичи.
        
        Args:
            feature_id: ID фичи
            feature_title: Название фичи
            plan_dsl_json: JSON с планом выполнения фичи
        """
        try:
            if not plan_dsl_json:
                # Нет подробного плана — сразу переводим в RUNNING (без блокировок)
                self.session.execute(
                    text("UPDATE features SET status = 'RUNNING' WHERE id = :fid"),
                    {"fid": feature_id}
                )
                self.session.commit()
                logger.info(
                    "no_plan_dsl_required_set_running",
                    component="orchestrator",
                    feature_id=feature_id,
                    feature_title=feature_title
                )
                return
                
            # Парсим план DSL
            try:
                plan_data = json.loads(plan_dsl_json)
            except json.JSONDecodeError as e:
                logger.error(
                    "plan_dsl_parse_error",
                    component="orchestrator",
                    feature_id=feature_id,
                    error=str(e)
                )
                return
            
            # Извлекаем требования к блокировкам
            resource_locks = parse_resource_locks_from_plan(plan_data)
            
            if not resource_locks:
                # Нет требований к блокировкам, можно сразу запускать
                logger.info(
                    "no_resource_locks_required",
                    component="orchestrator", 
                    feature_id=feature_id,
                    feature_title=feature_title
                )
                
                # Обновляем статус на RUNNING
                self.session.execute(
                    text("""
                        UPDATE features 
                        SET status = 'RUNNING'
                        WHERE id = :feature_id
                    """),
                    {"feature_id": feature_id}
                )
                self.session.commit()
                return
            
            logger.info(
                "checking_resource_locks",
                component="orchestrator",
                feature_id=feature_id,
                feature_title=feature_title,
                required_locks=resource_locks
            )
            
            # Пытаемся захватить все необходимые блокировки
            resource_names = [lock["resource"] for lock in resource_locks]
            success, failed_resources = lock_manager.acquire_multiple(resource_names, feature_id)
            
            if success:
                # Все блокировки захвачены, можно запускать фичу
                logger.info(
                    "resource_locks_acquired",
                    component="orchestrator",
                    feature_id=feature_id,
                    feature_title=feature_title,
                    acquired_resources=resource_names
                )
                
                # Обновляем статус фичи на RUNNING
                self.session.execute(
                    text("""
                        UPDATE features 
                        SET status = 'RUNNING'
                        WHERE id = :feature_id
                    """),
                    {"feature_id": feature_id}
                )
                self.session.commit()
                
                logger.info(
                    "feature_status_updated_to_running",
                    component="orchestrator",
                    feature_id=feature_id,
                    feature_title=feature_title
                )
                
            else:
                # Не удалось захватить блокировки
                logger.info(
                    "resource_locks_failed",
                    component="orchestrator",
                    feature_id=feature_id,
                    feature_title=feature_title,
                    failed_resources=failed_resources
                )
                
                # Фича остается в статусе PLANNED до освобождения ресурсов
                
        except Exception as e:
            logger.error(
                "lock_check_error",
                component="orchestrator",
                feature_id=feature_id,
                err_type=type(e).__name__,
                error=str(e)
            )
    
    async def _process_new_tasks(self):
        """Обрабатывает новые задачи."""
        try:
            # Выбираем задачи со статусом NEW
            result = self.session.execute(
                text("""
                    SELECT t.id, t.feature_id, t.role, f.title as feature_title
                    FROM tasks t
                    JOIN features f ON t.feature_id = f.id
                    WHERE t.status = 'NEW'
                    ORDER BY t.feature_id, t.role
                    LIMIT 20
                """)
            )
            
            tasks = result.fetchall()
            
            for task_row in tasks:
                task_id = task_row[0]
                feature_id = task_row[1]
                role = task_row[2]
                feature_title = task_row[3]
                
                logger.info(
                    "processing_new_task",
                    component="orchestrator",
                    task_id=task_id,
                    feature_id=feature_id,
                    feature_title=feature_title,
                    role=role
                )
                
                try:
                    # Запускаем или резюмируем граф G1
                    await self._run_or_resume_g1(task_id, feature_id, role)
                    
                except Exception as e:
                    logger.error(
                        "task_processing_error",
                        component="orchestrator",
                        task_id=task_id,
                        feature_id=feature_id,
                        err_type=type(e).__name__,
                        error=str(e)
                    )
                    
                    # Помечаем задачу как FAILED при ошибке
                    self.session.execute(
                        text("""
                            UPDATE tasks 
                            SET status = 'FAILED', finished_at = datetime('now')
                            WHERE id = :task_id
                        """),
                        {"task_id": task_id}
                    )
                    self.session.commit()
                    
        except Exception as e:
            logger.error(
                "new_tasks_processing_error",
                component="orchestrator",
                err_type=type(e).__name__,
                error=str(e)
            )
    
    async def _run_or_resume_g1(self, task_id: int, feature_id: int, role: str):
        """
        Запускает или резюмирует граф G1 для задачи.
        
        Args:
            task_id: ID задачи
            feature_id: ID фичи
            role: Роль задачи
        """
        try:
            logger.info(
                "running_or_resuming_g1",
                component="orchestrator",
                task_id=task_id,
                feature_id=feature_id,
                role=role
            )
            
            # Проверяем, есть ли уже запуск графа для этой фичи
            result = self.session.execute(
                text("""
                    SELECT run_id, status
                    FROM graph_runs
                    WHERE feature_id = :feature_id AND graph_name = 'G1'
                    ORDER BY last_checkpoint_at DESC
                    LIMIT 1
                """),
                {"feature_id": feature_id}
            )
            
            run_row = result.fetchone()
            
            if run_row:
                # Есть существующий запуск, резюмируем
                run_id = run_row[0]
                status = run_row[1]
                
                logger.info(
                    "resuming_g1_run",
                    component="orchestrator",
                    task_id=task_id,
                    feature_id=feature_id,
                    run_id=run_id,
                    current_status=status
                )
                
                # Обновляем статус задачи
                self.session.execute(
                    text("""
                        UPDATE tasks 
                        SET status = 'RUNNING', started_at = datetime('now'), attempts = attempts + 1
                        WHERE id = :task_id
                    """),
                    {"task_id": task_id}
                )
                
                # Обновляем статус запуска графа
                self.session.execute(
                    text("""
                        UPDATE graph_runs 
                        SET status = 'RUNNING', last_checkpoint_at = datetime('now')
                        WHERE run_id = :run_id
                    """),
                    {"run_id": run_id}
                )
                
                self.session.commit()
                
                # Встраиваем формирование контекстного пакета и попытку вызова Dev-узла
                context_md = await self._build_and_log_context(task_id, feature_id, role)
                await self._maybe_call_dev_node(task_id, feature_id, role, context_md, run_id)

                # В реальной реализации здесь будет вызов графа G1 с resume
                # Для демонстрации помечаем как завершенный
                
                # Обновляем статус задачи как завершенной
                self.session.execute(
                    text("""
                        UPDATE tasks 
                        SET status = 'DONE', finished_at = datetime('now')
                        WHERE id = :task_id
                    """),
                    {"task_id": task_id}
                )
                
                # Обновляем статус запуска графа
                self.session.execute(
                    text("""
                        UPDATE graph_runs 
                        SET status = 'DONE', last_checkpoint_at = datetime('now')
                        WHERE run_id = :run_id
                    """),
                    {"run_id": run_id}
                )
                
                self.session.commit()
                
                logger.info(
                    "g1_run_resumed_and_completed",
                    component="orchestrator",
                    task_id=task_id,
                    feature_id=feature_id,
                    run_id=run_id
                )
                
            else:
                # Новый запуск графа
                run_id = str(uuid.uuid4())
                
                logger.info(
                    "starting_new_g1_run",
                    component="orchestrator",
                    task_id=task_id,
                    feature_id=feature_id,
                    run_id=run_id
                )
                
                # Создаем запись о запуске графа
                self.session.execute(
                    text("""
                        INSERT INTO graph_runs (
                            run_id, feature_id, graph_name, thread_id, status, last_checkpoint_at
                        ) VALUES (
                            :run_id, :feature_id, 'G1', :thread_id, 'RUNNING', datetime('now')
                        )
                    """),
                    {
                        "run_id": run_id,
                        "feature_id": feature_id,
                        "thread_id": str(feature_id)  # Используем feature_id как thread_id
                    }
                )
                
                # Обновляем статус задачи
                self.session.execute(
                    text("""
                        UPDATE tasks 
                        SET status = 'RUNNING', started_at = datetime('now'), attempts = attempts + 1
                        WHERE id = :task_id
                    """),
                    {"task_id": task_id}
                )
                
                self.session.commit()
                
                # Встраиваем формирование контекстного пакета и попытку вызова Dev-узла
                context_md = await self._build_and_log_context(task_id, feature_id, role)
                await self._maybe_call_dev_node(task_id, feature_id, role, context_md, run_id)

                # В реальной реализации здесь будет вызов графа G1
                # Для демонстрации помечаем как завершенный
                
                # Обновляем статус задачи как завершенной
                self.session.execute(
                    text("""
                        UPDATE tasks 
                        SET status = 'DONE', finished_at = datetime('now')
                        WHERE id = :task_id
                    """),
                    {"task_id": task_id}
                )
                
                # Обновляем статус запуска графа
                self.session.execute(
                    text("""
                        UPDATE graph_runs 
                        SET status = 'DONE', last_checkpoint_at = datetime('now')
                        WHERE run_id = :run_id
                    """),
                    {"run_id": run_id}
                )
                
                self.session.commit()
                
                logger.info(
                    "new_g1_run_completed",
                    component="orchestrator",
                    task_id=task_id,
                    feature_id=feature_id,
                    run_id=run_id
                )
                
        except Exception as e:
            logger.error(
                "g1_run_error",
                component="orchestrator",
                task_id=task_id,
                feature_id=feature_id,
                err_type=type(e).__name__,
                error=str(e)
            )
            
            # Откатываем транзакцию в случае ошибки
            self.session.rollback()
            
            # Повторно выбрасываем исключение для обработки выше
            raise

    async def _build_and_log_context(self, task_id: int, feature_id: int, role: str) -> str:
        """Формирует контекст с помощью ContextPackager и логирует его в agent_events.

        Это интеграционная точка: в реальном исполнении контекст передается агенту (Dev/QA/...).
        """
        try:
            # Получаем DSL задачи
            row = self.session.execute(
                text("""
                    SELECT id, feature_id, role, dsl_json
                    FROM tasks
                    WHERE id = :task_id
                """),
                {"task_id": task_id}
            ).fetchone()
            if not row:
                return ""
            task_obj: Dict[str, Any] = {
                "id": row[0],
                "feature_id": row[1],
                "role": row[2],
                "dsl_json": row[3],
            }
            context_md = ""
            if self.packager:
                context_md = self.packager.build_context_for_task(task_obj)
            # Укоротим для хранения
            store_md = context_md[:8000] if context_md else ""
            # Запишем в agent_events
            self.session.execute(
                text("""
                    INSERT INTO agent_events (ts, agent_role, task_id, event, details_json)
                    VALUES (datetime('now'), :agent_role, :task_id, :event, :details_json)
                """),
                {
                    "agent_role": role,
                    "task_id": str(task_id),
                    "event": "context_pack_built",
                    "details_json": json.dumps({
                        "feature_id": feature_id,
                        "size": len(context_md),
                        "preview": store_md,
                    }, ensure_ascii=False),
                }
            )
            self.session.commit()
            logger.info(
                "context_pack_built",
                component="orchestrator",
                task_id=task_id,
                feature_id=feature_id,
                role=role,
                size=len(store_md)
            )
            return context_md
        except Exception as e:
            logger.error(
                "context_pack_build_error",
                component="orchestrator",
                task_id=task_id,
                feature_id=feature_id,
                role=role,
                err_type=type(e).__name__,
                error=str(e)
            )
            return ""

    async def _maybe_call_dev_node(self, task_id: int, feature_id: int, role: str, context_md: str, run_id: str) -> None:
        """Пытаемся выполнить Dev-узел с контекстным пакетом, чтобы включить его в промпт.

        Любые ошибки подавляются (орchestrator не должен падать из-за Dev-узла в MVP).
        """
        try:
            if role != 'Dev':
                return
            # Собираем минимальное состояние для узла Dev
            run_ctx = RunCtx(
                run_id=run_id,
                feature_id=str(feature_id),
                task_id=str(task_id),
                correlation_id=run_id,
                env=get_env(),
            )
            state = {
                "run_ctx": run_ctx,
                "context_pack": context_md or "",
                # Поля Watchdog по умолчанию
                "watchdog_failures": [],
                "escalation_context": "",
            }
            # Вызываем Dev-узел (LLM-роутер логирует llm_call_start/llm_call_end)
            await dev_code_node(state)
        except Exception as e:
            logger.warning(
                "dev_node_call_skipped",
                component="orchestrator",
                task_id=task_id,
                feature_id=feature_id,
                err_type=type(e).__name__,
                error=str(e)
            )
    
    async def _process_wait_budget_tasks(self):
        """Обрабатывает задачи в состоянии WAIT_BUDGET."""
        try:
            # Выбираем задачи со статусом WAIT_BUDGET
            result = self.session.execute(
                text("""
                    SELECT id, feature_id, role, attempts
                    FROM tasks 
                    WHERE status = 'WAIT_BUDGET'
                    LIMIT 10
                """)
            )
            
            tasks = result.fetchall()
            
            for task_row in tasks:
                task_id = task_row[0]
                feature_id = task_row[1]
                role = task_row[2]
                attempts = task_row[3] or 0
                
                logger.info(
                    "processing_wait_budget_task",
                    component="orchestrator",
                    task_id=task_id,
                    feature_id=feature_id,
                    role=role,
                    attempts=attempts
                )
                
                try:
                    # Проверяем доступность бюджета токенов
                    # Получаем счетчик токенов
                    token_accountant = get_token_accountant()
                    
                    # Оцениваем количество токенов для задачи (в реальной реализации это будет точнее)
                    estimated_input_tokens = 1000  # Оценка по умолчанию
                    estimated_output_tokens = 500   # Оценка по умолчанию
                    
                    # Проверяем возможность расхода
                    can_spend, remaining = token_accountant.can_spend(
                        role, estimated_input_tokens, estimated_output_tokens
                    )
                    
                    logger.info(
                        "budget_check_result",
                        component="orchestrator",
                        task_id=task_id,
                        feature_id=feature_id,
                        role=role,
                        can_spend=can_spend,
                        remaining=remaining
                    )
                    
                    if can_spend:
                        # Бюджет доступен, переводим задачу в состояние NEW для перезапуска
                        self.session.execute(
                            text("""
                                UPDATE tasks 
                                SET status = 'NEW', scheduled_at = datetime('now')
                                WHERE id = :task_id
                            """),
                            {"task_id": task_id}
                        )
                        
                        self.session.commit()
                        
                        logger.info(
                            "wait_budget_task_resumed",
                            component="orchestrator",
                            task_id=task_id,
                            feature_id=feature_id,
                            role=role,
                            budget_remaining=remaining
                        )
                    else:
                        # Бюджет не доступен
                        # Проверяем, не превышен ли лимит попыток
                        if attempts < DEFAULT_MAX_RETRIES:
                            # Увеличиваем счетчик попыток
                            new_attempts = attempts + 1
                            # Рассчитываем backoff (экспоненциальный)
                            backoff_seconds = DEFAULT_BACKOFF_BASE * (2 ** (new_attempts - 1))
                            
                            self.session.execute(
                                text("""
                                    UPDATE tasks 
                                    SET attempts = :attempts, 
                                        scheduled_at = datetime('now', '+' || :backoff_seconds || ' seconds')
                                    WHERE id = :task_id
                                """),
                                {
                                    "task_id": task_id,
                                    "attempts": new_attempts,
                                    "backoff_seconds": backoff_seconds
                                }
                            )
                            
                            self.session.commit()
                            
                            logger.info(
                                "wait_budget_task_retried",
                                component="orchestrator",
                                task_id=task_id,
                                feature_id=feature_id,
                                role=role,
                                attempts=new_attempts,
                                backoff_seconds=backoff_seconds
                            )
                        else:
                            # Превышен лимит попыток, переводим задачу в FAILED
                            self.session.execute(
                                text("""
                                    UPDATE tasks 
                                    SET status = 'FAILED', finished_at = datetime('now')
                                    WHERE id = :task_id
                                """),
                                {"task_id": task_id}
                            )
                            
                            self.session.commit()
                            
                            logger.info(
                                "wait_budget_task_failed_max_retries",
                                component="orchestrator",
                                task_id=task_id,
                                feature_id=feature_id,
                                role=role,
                                attempts=attempts
                            )
                        
                        logger.info(
                            "llm_budget_exceeded",
                            component="orchestrator",
                            task_id=task_id,
                            feature_id=feature_id,
                            role=role,
                            budget_remaining=remaining
                        )
                        
                except Exception as e:
                    logger.error(
                        "wait_budget_task_processing_error",
                        component="orchestrator",
                        task_id=task_id,
                        feature_id=feature_id,
                        err_type=type(e).__name__,
                        error=str(e)
                    )
                    
        except Exception as e:
            logger.error(
                "wait_budget_tasks_processing_error",
                component="orchestrator",
                err_type=type(e).__name__,
                error=str(e)
            )
    
    async def _check_and_update_feature_status(self):
        """
        Проверяет и обновляет статус фич на основе состояния их задач.
        Освобождает блокировки для завершенных фич.
        """
        try:
            # Выбираем фичи в статусе RUNNING
            result = self.session.execute(
                text("""
                    SELECT f.id, f.title, NULL as plan_dsl_json,
                           COUNT(t.id) as total_tasks,
                           SUM(CASE WHEN t.status = 'DONE' THEN 1 ELSE 0 END) as done_tasks,
                           SUM(CASE WHEN t.status = 'FAILED' THEN 1 ELSE 0 END) as failed_tasks
                    FROM features f
                    LEFT JOIN tasks t ON f.id = t.feature_id
                    WHERE f.status = 'RUNNING'
                    GROUP BY f.id, f.title
                """)
            )
            
            running_features = result.fetchall()
            
            for feature_row in running_features:
                feature_id = feature_row[0]
                feature_title = feature_row[1] 
                plan_dsl_json = feature_row[2]
                total_tasks = feature_row[3] or 0
                done_tasks = feature_row[4] or 0
                failed_tasks = feature_row[5] or 0
                
                logger.info(
                    "checking_running_feature_status",
                    component="orchestrator",
                    feature_id=feature_id,
                    feature_title=feature_title,
                    total_tasks=total_tasks,
                    done_tasks=done_tasks,
                    failed_tasks=failed_tasks
                )
                
                new_status = None
                
                if total_tasks == 0:
                    # Нет задач - странная ситуация, но считаем завершенной
                    new_status = "DONE"
                elif done_tasks == total_tasks and total_tasks > 0:
                    # Все задачи завершены успешно — безопасный GitOps (ветка/PR/merge)
                    try:
                        corr = f"FF-GITOPS-{feature_id}-{uuid.uuid4().hex[:8]}"
                        os.environ.setdefault("REQUESTS_CA_BUNDLE", "/etc/ssl/certs/ca-certificates.crt")
                        os.environ.setdefault("CURL_CA_BUNDLE", "/etc/ssl/certs/ca-certificates.crt")
                        gis = GitIntegrationService()
                        branch = gis.create_feature_branch(feature_id, feature_title, corr)
                        gis.ensure_unique_commit(feature_id, corr)
                        pr_info = gis.create_pull_request(branch, feature_id, feature_title, corr)
                        # persist PR info
                        self.session.execute(
                            text("UPDATE features SET pr_url = :pr, git_branch = :br, branch_name = :br, updated_at = datetime('now') WHERE id = :fid"),
                            {"pr": pr_info.get("pr_url",""), "br": branch, "fid": feature_id}
                        )
                        self.session.commit()
                        # attempt merge (mock in TEST if push disabled)
                        try:
                            merge = gis.merge_pull_request(feature_id, pr_info.get("pr_number", 0), pr_info.get("head_sha",""), corr)
                            self.session.execute(
                                text("UPDATE features SET merged_sha = :sha, updated_at = datetime('now') WHERE id = :fid"),
                                {"sha": merge.get("merge_commit_sha",""), "fid": feature_id}
                            )
                            self.session.commit()
                        except GitIntegrationError as e:
                            logger.warning("gitops_merge_skip", component="orchestrator", feature_id=feature_id, error=str(e))
                    except Exception as e:
                        logger.error("gitops_perform_error", component="orchestrator", feature_id=feature_id, err_type=type(e).__name__, error=str(e))
                    new_status = "DONE"
                elif failed_tasks > 0 and (done_tasks + failed_tasks) == total_tasks:
                    # Есть провалившиеся задачи и все задачи обработаны
                    new_status = "FAILED"
                
                if new_status:
                    # Обновляем статус фичи
                    self.session.execute(
                        text("""
                            UPDATE features 
                            SET status = :new_status, finished_at = datetime('now')
                            WHERE id = :feature_id
                        """),
                        {
                            "feature_id": feature_id,
                            "new_status": new_status
                        }
                    )
                    
                    # Освобождаем блокировки
                    await self._release_locks_for_feature(feature_id, feature_title, plan_dsl_json)
                    
                    self.session.commit()
                    
                    logger.info(
                        "feature_status_updated",
                        component="orchestrator",
                        feature_id=feature_id,
                        feature_title=feature_title,
                        old_status="RUNNING",
                        new_status=new_status,
                        total_tasks=total_tasks,
                        done_tasks=done_tasks,
                        failed_tasks=failed_tasks
                    )
                    
        except Exception as e:
            logger.error(
                "feature_status_check_error",
                component="orchestrator",
                err_type=type(e).__name__,
                error=str(e)
            )
    
    async def _release_locks_for_feature(self, feature_id: int, feature_title: str, plan_dsl_json: str):
        """
        Освобождает блокировки ресурсов для завершенной фичи.
        
        Args:
            feature_id: ID фичи
            feature_title: Название фичи
            plan_dsl_json: JSON с планом выполнения фичи
        """
        try:
            if not plan_dsl_json:
                logger.warning(
                    "no_plan_dsl_for_lock_release",
                    component="orchestrator",
                    feature_id=feature_id
                )
                return
                
            # Парсим план DSL
            try:
                plan_data = json.loads(plan_dsl_json)
            except json.JSONDecodeError as e:
                logger.error(
                    "plan_dsl_parse_error_on_release",
                    component="orchestrator",
                    feature_id=feature_id,
                    error=str(e)
                )
                return
            
            # Извлекаем требования к блокировкам
            resource_locks = parse_resource_locks_from_plan(plan_data)
            
            if not resource_locks:
                logger.info(
                    "no_locks_to_release",
                    component="orchestrator",
                    feature_id=feature_id,
                    feature_title=feature_title
                )
                return
            
            # Освобождаем все блокировки фичи
            released_resources = lock_manager.release_all_for_feature(feature_id)
            
            logger.info(
                "locks_released_for_feature",
                component="orchestrator",
                feature_id=feature_id,
                feature_title=feature_title,
                released_resources=released_resources,
                expected_resources=[lock["resource"] for lock in resource_locks]
            )
            
        except Exception as e:
            logger.error(
                "lock_release_error",
                component="orchestrator",
                feature_id=feature_id,
                err_type=type(e).__name__,
                error=str(e)
            )

# Глобальный экземпляр планировщика
orchestrator_loop = OrchestratorLoop()

def get_orchestrator_loop() -> OrchestratorLoop:
    """
    Получает глобальный экземпляр планировщика оркестратора.
    
    Returns:
        OrchestratorLoop: Глобальный экземпляр планировщика
    """
    return orchestrator_loop

async def main():
    """Основная функция для запуска планировщика."""
    # Проверяем, включен ли цикл
    if not LOOP_ENABLED:
        logger.info("orchestrator_loop_disabled", component="orchestrator")
        return
    
    loop = get_orchestrator_loop()
    try:
        await loop.start()
    except KeyboardInterrupt:
        logger.info("orchestrator_loop_interrupted", component="orchestrator")
    finally:
        await loop.stop()

if __name__ == "__main__":
    asyncio.run(main())
