import unittest
import asyncio
import uuid
from unittest.mock import patch, MagicMock
from app.graph.base import start_run, resume_run, get_graph_manager
from app.graph.g1_feature import get_g1_graph, GraphState
from app.graph.types import RunCtx

class TestLangGraphSetup(unittest.TestCase):
    """Тесты для настройки LangGraph."""

    def setUp(self):
        """Подготовка к тестам."""
        # Создаем контекст выполнения
        self.run_ctx = RunCtx(
            run_id=str(uuid.uuid4()),
            feature_id="test-feature-123",
            task_id="test-task-456",
            correlation_id="test-correlation-789",
            env="TEST"
        )

    def test_start_run(self):
        """Тест начала нового запуска."""
        feature_id = "test-feature-123"
        run_id = start_run(feature_id)
        
        self.assertIsInstance(run_id, str)
        self.assertTrue(len(run_id) > 0)
        self.assertNotEqual(run_id, feature_id)

    def test_resume_run(self):
        """Тест возобновления запуска."""
        run_id = "test-run-123"
        # Вызов не должен выбрасывать исключение
        try:
            resume_run(run_id)
        except Exception:
            self.fail("resume_run() raised Exception unexpectedly!")

    def test_graph_manager_initialization(self):
        """Тест инициализации менеджера графа."""
        graph_manager = get_graph_manager()
        self.assertIsNotNone(graph_manager)
        self.assertIsNotNone(graph_manager.checkpointer)

    def test_g1_graph_creation(self):
        """Тест создания графа G1."""
        graph = get_g1_graph()
        self.assertIsNotNone(graph)
        
        # Проверяем, что граф имеет правильную структуру
        self.assertTrue(hasattr(graph, 'nodes'))
        self.assertTrue(hasattr(graph, 'edges'))

    def test_dev_node_execution(self):
        """Тест выполнения узла Dev."""
        from app.graph.g1_feature import dev_node
        
        # Создаем состояние графа
        state = GraphState({
            "run_ctx": self.run_ctx,
            "status": "initialized"
        })
        
        # Выполняем узел
        result = asyncio.run(dev_node(state))
        
        # Проверяем результат
        self.assertIn("status", result)
        self.assertEqual(result["status"], "dev_completed")
        self.assertIn("result", result)
        self.assertEqual(result["result"], "Dev work completed")

    def test_gate_node_execution(self):
        """Тест выполнения узла Gate."""
        from app.graph.g1_feature import gate_node
        
        # Создаем состояние графа
        state = GraphState({
            "run_ctx": self.run_ctx,
            "status": "initialized"
        })
        
        # Выполняем узел
        result = asyncio.run(gate_node(state))
        
        # Проверяем результат
        self.assertIn("status", result)
        self.assertEqual(result["status"], "gate_completed")
        self.assertIn("result", result)
        self.assertEqual(result["result"], "Gate validation completed")

    def test_qa_node_execution(self):
        """Тест выполнения узла QA."""
        from app.graph.g1_feature import qa_node
        
        # Создаем состояние графа
        state = GraphState({
            "run_ctx": self.run_ctx,
            "status": "initialized"
        })
        
        # Выполняем узел
        result = asyncio.run(qa_node(state))
        
        # Проверяем результат
        self.assertIn("status", result)
        self.assertEqual(result["status"], "qa_completed")
        self.assertIn("result", result)
        self.assertEqual(result["result"], "QA testing completed")

    def test_scribe_node_execution(self):
        """Тест выполнения узла Scribe."""
        from app.graph.g1_feature import scribe_node
        
        # Создаем состояние графа
        state = GraphState({
            "run_ctx": self.run_ctx,
            "status": "initialized"
        })
        
        # Выполняем узел
        result = asyncio.run(scribe_node(state))
        
        # Проверяем результат
        self.assertIn("status", result)
        self.assertEqual(result["status"], "scribe_completed")
        self.assertIn("result", result)
        self.assertEqual(result["result"], "Documentation updated")

    def test_apply_node_execution(self):
        """Тест выполнения узла Apply."""
        from app.graph.g1_feature import apply_node
        
        # Создаем состояние графа
        state = GraphState({
            "run_ctx": self.run_ctx,
            "status": "initialized"
        })
        
        # Выполняем узел
        result = asyncio.run(apply_node(state))
        
        # Проверяем результат
        self.assertIn("status", result)
        self.assertEqual(result["status"], "apply_completed")
        self.assertIn("result", result)
        self.assertEqual(result["result"], "Artifacts applied")

if __name__ == '__main__':
    unittest.main()