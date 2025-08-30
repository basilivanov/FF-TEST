import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Тест для проверки миграций
def test_migrations():
    # Получаем DATABASE_URL из переменных окружения
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL не установлена, пропускаем тест")
    
    try:
        # Создаем подключение к базе данных
        engine = create_engine(database_url)
        
        # Выполняем миграции
        os.system("cd /opt/feature-factory && alembic upgrade head")
        
        # Проверяем, что таблицы созданы
        with engine.connect() as conn:
            # Проверяем таблицу postings_raw
            result = conn.execute(text("SELECT COUNT(*) FROM postings_raw"))
            assert result.fetchone()[0] >= 0
            
            # Проверяем таблицу postings_flat
            result = conn.execute(text("SELECT COUNT(*) FROM postings_flat"))
            assert result.fetchone()[0] >= 0
            
            # Проверяем таблицу etl_watermarks
            result = conn.execute(text("SELECT COUNT(*) FROM etl_watermarks"))
            assert result.fetchone()[0] >= 0
            
            # Проверяем таблицу jobs
            result = conn.execute(text("SELECT COUNT(*) FROM jobs"))
            assert result.fetchone()[0] >= 0
            
            # Проверяем таблицу settings
            result = conn.execute(text("SELECT COUNT(*) FROM settings"))
            assert result.fetchone()[0] >= 0
            
            # Проверяем таблицу agent_events
            result = conn.execute(text("SELECT COUNT(*) FROM agent_events"))
            assert result.fetchone()[0] >= 0
            
            # Проверяем таблицу doc_registry
            result = conn.execute(text("SELECT COUNT(*) FROM doc_registry"))
            assert result.fetchone()[0] >= 0
            
            # Проверяем таблицу change_log
            result = conn.execute(text("SELECT COUNT(*) FROM change_log"))
            assert result.fetchone()[0] >= 0
            
        # Проверяем идемпотентность - повторный запуск upgrade head
        result = os.system("cd /opt/feature-factory && alembic upgrade head")
        assert result == 0
        
    except OperationalError as e:
        pytest.fail(f"Ошибка подключения к базе данных: {e}")
    except Exception as e:
        pytest.fail(f"Ошибка при выполнении теста: {e}")