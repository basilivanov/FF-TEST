#!/usr/bin/env python3
"""
Логирование для планировщика задач и графов выполнения.
Согласно стандарту Logging-001.md
"""

import uuid
from app.logging_helpers import log, get_env


def log_task_status_change(task_id: str, feature_id: int, role: str, 
                          old_status: str, new_status: str, run_id: str = None,
                          correlation_id: str = None, **extra):
    """
    Логирует изменение статуса задачи.
    
    Args:
        task_id: ID задачи
        feature_id: ID фичи
        role: Роль задачи (Dev, QA, Scribe, etc.)
        old_status: Предыдущий статус
        new_status: Новый статус
        run_id: ID запуска графа
        correlation_id: ID корреляции
        **extra: Дополнительные поля для kv
    """
    log.info(
        event="task_status_changed",
        env=get_env(),
        component="scheduler",
        agent_role="TaskScheduler",
        run_id=run_id or str(uuid.uuid4()),
        task_id=task_id,
        correlation_id=correlation_id or str(uuid.uuid4()),
        kv={
            "feature_id": feature_id,
            "task_role": role,
            "status_from": old_status,
            "status_to": new_status,
            **extra
        }
    )


def log_feature_status_change(feature_id: int, title: str, old_status: str, 
                             new_status: str, run_id: str = None,
                             correlation_id: str = None, **extra):
    """
    Логирует изменение статуса фичи.
    
    Args:
        feature_id: ID фичи
        title: Название фичи
        old_status: Предыдущий статус
        new_status: Новый статус
        run_id: ID запуска графа
        correlation_id: ID корреляции
        **extra: Дополнительные поля для kv
    """
    log.info(
        event="feature_status_changed",
        env=get_env(),
        component="scheduler",
        agent_role="FeatureManager",
        run_id=run_id or str(uuid.uuid4()),
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id or str(uuid.uuid4()),
        kv={
            "feature_id": feature_id,
            "feature_title": title[:50],  # Truncate long titles
            "status_from": old_status,
            "status_to": new_status,
            **extra
        }
    )


def log_graph_status_change(run_id: str, feature_id: int, graph_name: str,
                           old_status: str, new_status: str,
                           correlation_id: str = None, **extra):
    """
    Логирует изменение статуса графа выполнения.
    
    Args:
        run_id: ID запуска графа
        feature_id: ID фичи
        graph_name: Название графа (G1, G2, etc.)
        old_status: Предыдущий статус
        new_status: Новый статус
        correlation_id: ID корреляции
        **extra: Дополнительные поля для kv
    """
    log.info(
        event="graph_status_changed",
        env=get_env(),
        component="scheduler",
        agent_role="GraphManager",
        run_id=run_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id or str(uuid.uuid4()),
        kv={
            "feature_id": feature_id,
            "graph_name": graph_name,
            "status_from": old_status,
            "status_to": new_status,
            **extra
        }
    )


def log_scheduler_iteration(scheduled_tasks_count: int, running_tasks_count: int,
                           correlation_id: str = None, **extra):
    """
    Логирует итерацию планировщика.
    
    Args:
        scheduled_tasks_count: Количество запланированных задач
        running_tasks_count: Количество выполняющихся задач
        correlation_id: ID корреляции
        **extra: Дополнительные поля для kv
    """
    log.info(
        event="scheduler_iteration",
        env=get_env(),
        component="scheduler",
        agent_role="TaskScheduler",
        run_id=str(uuid.uuid4()),
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id or str(uuid.uuid4()),
        kv={
            "scheduled_tasks": scheduled_tasks_count,
            "running_tasks": running_tasks_count,
            **extra
        }
    )


async def _send_feature_status_telegram_notification(feature_id: int, title: str, 
                                                   old_status: str, new_status: str,
                                                   run_id: str = None, correlation_id: str = None):
    """
    Отправляет Telegram уведомление об изменении статуса фичи.
    """
    try:
        from app.api.notifications import send_telegram_message_with_retry, TelegramMessage
        
        # Реальный токен бота и chat_id
        bot_token = "8255054922:AAF7tM68DgVKM1s3B5I-5kuobSB7YIxVIEg"
        # Пока используем тестовый chat_id - в production нужно получить real chat_id для basil_ivanov@inbox.ru
        chat_id = 123456789
        
        # Формируем текст уведомления
        message_text = f"""🔄 Статус фичи изменился

📋 Feature #{feature_id}: {title}
📍 {old_status} → {new_status}
🕐 {get_env()} environment
⚡ Run ID: {run_id or 'N/A'}"""

        message = TelegramMessage(
            chat_id=chat_id,
            text=message_text,
            parse_mode=None
        )
        
        result = await send_telegram_message_with_retry(bot_token, message)
        
        if result.ok:
            log.info("Telegram notification sent successfully", 
                    feature_id=feature_id, chat_id=chat_id)
        else:
            log.warning("Telegram notification failed", 
                       feature_id=feature_id, error_code=result.error_code)
                       
    except Exception as e:
        log.error("Failed to send Telegram notification", 
                 feature_id=feature_id, error=str(e))
