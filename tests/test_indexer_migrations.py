import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def test_indexer_migrations():
    """Тест для проверки миграций индексера."""
    # Получаем DATABASE_URL из переменных окружения
    database_url = os.getenv("DATABASE_URL", "sqlite:///tmp/feature.test.db")
    
    try:
        # Создаем подключение к базе данных
        engine = create_engine(database_url)
        
        # Проверяем, что таблицы индексера созданы
        with engine.connect() as conn:
            # Проверяем таблицу code_registry
            result = conn.execute(text("SELECT COUNT(*) FROM code_registry"))
            assert result.fetchone()[0] >= 0
            
            # Проверяем таблицу symbol_index
            result = conn.execute(text("SELECT COUNT(*) FROM symbol_index"))
            assert result.fetchone()[0] >= 0
            
            # Проверяем таблицу call_graph_edges
            result = conn.execute(text("SELECT COUNT(*) FROM call_graph_edges"))
            assert result.fetchone()[0] >= 0
            
    except OperationalError as e:
        pytest.fail(f"Ошибка подключения к базе данных: {e}")
    except Exception as e:
        pytest.fail(f"Ошибка при выполнении теста: {e}")

def test_code_registry_content():
    """Тест для проверки содержимого реестра кода."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///tmp/feature.test.db")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Проверяем, что в code_registry есть записи
            result = conn.execute(text("SELECT COUNT(*) FROM code_registry"))
            count = result.fetchone()[0]
            # Должно быть как минимум несколько записей (наши Python файлы)
            assert count >= 6
            
            # Проверяем структуру данных
            result = conn.execute(text("SELECT file_path, sha256 FROM code_registry LIMIT 1"))
            row = result.fetchone()
            assert row is not None
            assert len(row) == 2
            assert isinstance(row[0], str)  # file_path
            assert isinstance(row[1], str)  # sha256
            
    except OperationalError as e:
        pytest.fail(f"Ошибка подключения к базе данных: {e}")
    except Exception as e:
        pytest.fail(f"Ошибка при выполнении теста: {e}")