import unittest
import asyncio
import uuid
from unittest.mock import patch, MagicMock, call

from app.graph.g1_feature import get_g1_graph, GraphState
from app.graph.types import RunCtx
from app.graph.base import get_graph_manager

class TestWatchdogE2E(unittest.TestCase):
    """E2E-тест для проверки логики Watchdog в графе G1."""

    def setUp(self):
        """Настройка тестового окружения."""
        self.run_ctx = RunCtx(
            run_id=str(uuid.uuid4()),
            feature_id="test-feature-watchdog-e2e",
            task_id="test-task-watchdog-e2e",
            correlation_id="test-correlation-watchdog-e2e",
            env="TEST"
        )
        # LangGraph требует checkpointer для компиляции и выполнения графа
        self.checkpointer = get_graph_manager().checkpointer

    @patch('app.graph.nodes.dev_code.completion')
    @patch('app.logging_helpers.log.warning')
    @patch('app.logging_helpers.log.info')
    def test_watchdog_triggers_and_escalates_on_consecutive_failures(self, mock_log_info, mock_log_warning, mock_completion):
        """
        Проверяет, что Watchdog срабатывает после 3 последовательных ошибок
        и инициирует эскалацию L1, после чего граф успешно завершается.
        """
        # 1. Настраиваем мок для `completion`, чтобы симулировать 3 ошибки, а затем успех
        consecutive_error = ValueError("Simulated LLM Error")
        # Мок для `dev_code._parse_llm_response`
        successful_response = {
            "text": "```yaml\nfiles: [\"main.py\"]\npackage_contract: {}\n```\n```python\n# main.py\nprint('hello world')\n```"
        }

        mock_completion.side_effect = [
            consecutive_error,  # 1-й вызов -> ошибка
            consecutive_error,  # 2-й вызов -> ошибка
            consecutive_error,  # 3-й вызов -> ошибка, Watchdog должен сработать
            successful_response # 4-й вызов (после эскалации) -> успех
        ]

        # 2. Задаем начальное состояние графа
        initial_state = GraphState({
            "run_ctx": self.run_ctx,
            "package_contract": {"description": "Test contract for watchdog"},
            "strict_hard": False, # Не падать на ошибках LLM, чтобы Watchdog мог их поймать
        })

        # 3. Компилируем и запускаем граф
        graph = get_g1_graph()
        app = graph.compile(checkpointer=self.checkpointer)
        config = {"configurable": {"thread_id": self.run_ctx.feature_id}}

        # Запускаем граф. Ожидаем, что он завершится без исключений.
        try:
            final_state = app.invoke(initial_state, config)
        except Exception as e:
            self.fail(f"Graph invocation failed unexpectedly: {e}")

        # 4. Проверяем результаты
        # Проверяем, что LLM был вызван 4 раза
        self.assertEqual(mock_completion.call_count, 4, "LLM completion should have been called 4 times")

        # Проверяем, что Watchdog залогировал предупреждение о срабатывании
        mock_log_warning.assert_any_call(
            event="watchdog_triggered",
            run_id=self.run_ctx.run_id,
            task_id=self.run_ctx.task_id,
            correlation_id=self.run_ctx.correlation_id,
            kv={
                'threshold': 3,
                'failures': [
                    {'tool': 'llm_completion', 'type': 'ValueError'},
                    {'tool': 'llm_completion', 'type': 'ValueError'},
                    {'tool': 'llm_completion', 'type': 'ValueError'}
                ]
            }
        )

        # Проверяем, что была залогирована эскалация
        mock_log_info.assert_any_call(
            event="task_escalated",
            run_id=self.run_ctx.run_id,
            task_id=self.run_ctx.task_id,
            correlation_id=self.run_ctx.correlation_id,
            kv={"level": 1, "action": "retry_with_error_context"}
        )

        # Проверяем, что узел dev был перезапущен с контекстом
        mock_log_warning.assert_any_call("dev_node_retry_with_context", run_id=self.run_ctx.run_id, task_id=self.run_ctx.task_id)

        # Проверяем, что в системный промпт при повторном вызове был добавлен контекст
        last_call_args = mock_completion.call_args_list[-1]
        messages = last_call_args.kwargs['messages']
        system_prompt = messages[0]['content']
        self.assertIn("Контекст предыдущих ошибок", system_prompt)
        self.assertIn("Simulated LLM Error", system_prompt)
