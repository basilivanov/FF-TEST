#!/usr/bin/env python3
"""
E2E тест для механизма Watchdog в графе G1.
"""

import pytest
import asyncio
import uuid
from unittest.mock import patch, AsyncMock

from app.db.session import SessionLocal, engine
from app.db.models import Feature, Task, Base
from app.graph.g1_feature import create_g1_graph
from app.graph.types import RunCtx

# Создаем таблицы в тестовой БД (если нужно)
Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Фикстура для создания чистой сессии БД для каждого теста."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        # Очищаем таблицы после теста
        session.query(Task).delete()
        session.query(Feature).delete()
        session.commit()
        session.close()

@pytest.mark.asyncio
async def test_watchdog_triggers_and_escalates(db_session, caplog):
    """
    Проверяет, что Watchdog срабатывает после 3 одинаковых ошибок,
    запускает эскалацию Уровня 1 и позволяет графу продолжиться после исправления.
    """
    # 1. Настройка тестовых данных
    feature_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    test_feature = Feature(id=feature_id, name="Test Watchdog Feature", status="NEW")
    test_task = Task(id=task_id, feature_id=feature_id, name="Test Watchdog Task", role="Dev", status="NEW", dsl_json='{}')
    db_session.add(test_feature)
    db_session.add(test_task)
    db_session.commit()

    # 2. Мокирование узла dev_code_node
    from app.graph.nodes import dev_code
    original_dev_code_node = dev_code.dev_code_node
    call_count = 0

    async def mock_dev_code_node(state):
        nonlocal call_count
        call_count += 1

        # На 4-м вызове проверяем, что пришел контекст эскалации
        if call_count == 4:
            assert "Контекст предыдущих ошибок" in state.get("escalation_context", "")
        
        # Вызываем оригинальный узел
        result_state = await original_dev_code_node(state)

        # Для первых 3 вызовов симулируем ошибку
        if call_count <= 3:
            result_state["tool_errors"] = [
                {"tool_name": "test_tool", "error_message": "simulated consecutive error"}
            ]
        else:
            # На 4-м вызове ошибки нет, чтобы цикл прервался
            result_state["tool_errors"] = []
        
        return result_state

    # 3. Запуск графа с моком
    with patch('app.graph.nodes.dev_code.dev_code_node', new=mock_dev_code_node):
        graph = create_g1_graph()
        app = graph.compile()

        run_ctx = RunCtx(run_id=run_id, correlation_id=run_id, feature_id=feature_id, task_id=task_id)
        initial_state = {
            "run_ctx": run_ctx,
            "package_contract": {},
            # Убедимся, что начальное состояние чистое
            "watchdog_failures": [],
            "escalation_context": ""
        }

        # Прогоняем граф
        final_state = None
        async for output in app.astream(initial_state):
            final_state = output

    # 4. Проверка результатов
    # Проверяем, что dev_code_node был вызван 4 раза (3 сбоя + 1 успешный ретрай)
    assert call_count == 4, f"Dev node was called {call_count} times, expected 4"

    # Проверяем логи
    log_text = caplog.text
    assert "watchdog_triggered" in log_text
    assert "task_escalated" in log_text
    assert "dev_node_retry_with_context" in log_text

    # Проверяем, что граф дошел до узла gate после успешного перезапуска
    assert "gate" in final_state, "Graph did not proceed to gate node"
    assert final_state["gate"]["status"] == "gate_completed"

    print("\nE2E test for Watchdog successful!")
    print(f"Final graph state keys: {list(final_state.keys())}")
    print(f"Final gate status: {final_state.get('gate', {}).get('status')}")
