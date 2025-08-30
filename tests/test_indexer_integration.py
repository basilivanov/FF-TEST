import os
import pytest
import subprocess
from sqlalchemy import create_engine, text

def test_indexer_full_integration():
    """Полный интеграционный тест индексера."""
    database_url = "sqlite:///tmp/feature.test.db"
    
    # 1. Проверяем, что миграции применены
    engine = create_engine(database_url)
    with engine.connect() as conn:
        # Проверяем наличие таблиц
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('code_registry', 'symbol_index', 'call_graph_edges')"))
        tables = [row[0] for row in result]
        assert 'code_registry' in tables
        assert 'symbol_index' in tables
        assert 'call_graph_edges' in tables
    
    # 2. Запускаем скрипт индексации
    env = os.environ.copy()
    env['DATABASE_URL'] = database_url
    result = subprocess.run([
        '/opt/feature-factory/.venv/bin/python3', 
        '/opt/feature-factory/scripts/update_code_registry.py'
    ], cwd='/opt/feature-factory', env=env, 
       capture_output=True, text=True)
    
    assert result.returncode == 0
    
    # 3. Проверяем, что в code_registry есть записи
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM code_registry"))
        count = result.fetchone()[0]
        assert count >= 6  # Как минимум наши Python файлы

def test_indexer_idempotency():
    """Тест идемпотентности индексера."""
    database_url = "sqlite:///tmp/feature.test.db"
    
    # Запускаем скрипт дважды
    env = os.environ.copy()
    env['DATABASE_URL'] = database_url
    for i in range(2):
        result = subprocess.run([
            '/opt/feature-factory/.venv/bin/python3', 
            '/opt/feature-factory/scripts/update_code_registry.py'
        ], cwd='/opt/feature-factory', env=env, 
           capture_output=True, text=True)
        
        assert result.returncode == 0, f"Run {i+1} failed with output: {result.stdout} {result.stderr}"

def test_indexer_logging():
    """Тест логирования индексера."""
    # Проверяем наличие логов
    assert os.path.exists('/opt/feature-factory/logs/indexer.log')
    
    # Проверяем, что в логах есть событие index_updated
    with open('/opt/feature-factory/logs/indexer.log', 'r') as f:
        log_content = f.read()
        assert 'index_updated' in log_content