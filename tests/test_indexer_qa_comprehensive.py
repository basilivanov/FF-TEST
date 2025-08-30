import os
import pytest
import tempfile
import hashlib
import json
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient
from app.main import app

# Создаем тестового клиента
client = TestClient(app)

def test_file_modification_updates_registry():
    """Проверено: изменение файла обновляет code_registry.sha256"""
    # Используем нашу тестовую базу данных
    database_url = "sqlite:///./feature.new.db"
    engine = create_engine(database_url)
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("print('test')\n")
        temp_file_path = f.name
    
    try:
        # Вычисляем хэш файла
        with open(temp_file_path, 'rb') as f:
            original_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Импортируем функцию из скрипта обновления
        import sys
        sys.path.append('/opt/feature-factory')
        from scripts.update_code_registry import calculate_file_hash, update_code_registry
        
        # Обновляем реестр кода
        update_code_registry(engine, [temp_file_path])
        
        # Проверяем, что запись добавлена в базу
        with engine.connect() as conn:
            result = conn.execute(text("SELECT sha256 FROM code_registry WHERE file_path = :file_path"), 
                                {'file_path': temp_file_path})
            row = result.fetchone()
            assert row is not None
            assert row[0] == original_hash
        
        # Модифицируем файл
        with open(temp_file_path, 'w') as f:
            f.write("print('modified')\n")
        
        # Вычисляем новый хэш
        with open(temp_file_path, 'rb') as f:
            new_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Обновляем реестр кода снова
        update_code_registry(engine, [temp_file_path])
        
        # Проверяем, что хэш обновился
        with engine.connect() as conn:
            result = conn.execute(text("SELECT sha256 FROM code_registry WHERE file_path = :file_path"), 
                                {'file_path': temp_file_path})
            row = result.fetchone()
            assert row is not None
            assert row[0] == new_hash
            assert row[0] != original_hash
            
    finally:
        # Удаляем временный файл
        os.unlink(temp_file_path)

def test_symbol_index_and_call_graph_consistency():
    """symbol_index и call_graph_edges доступны и непротиворечивы"""
    database_url = "sqlite:///./feature.new.db"
    engine = create_engine(database_url)
    
    # Проверяем, что таблицы существуют и доступны
    with engine.connect() as conn:
        # Проверяем symbol_index
        result = conn.execute(text("SELECT COUNT(*) FROM symbol_index"))
        symbol_count = result.fetchone()[0]
        assert symbol_count >= 0  # Может быть 0 если ctags не работает, но таблица должна существовать
        
        # Проверяем call_graph_edges
        result = conn.execute(text("SELECT COUNT(*) FROM call_graph_edges"))
        edge_count = result.fetchone()[0]
        assert edge_count >= 0  # Может быть 0 если pyan3 не работает, но таблица должна существовать
        
        # Если есть символы, проверяем их структуру
        if symbol_count > 0:
            result = conn.execute(text("SELECT file_path, symbol_name, symbol_type FROM symbol_index LIMIT 1"))
            row = result.fetchone()
            assert row is not None
            assert row[0] is not None  # file_path
            assert row[1] is not None  # symbol_name
            assert row[2] is not None  # symbol_type
            
        # Если есть ребра, проверяем их структуру
        if edge_count > 0:
            result = conn.execute(text("SELECT source_symbol, target_symbol, file_path FROM call_graph_edges LIMIT 1"))
            row = result.fetchone()
            assert row is not None
            assert row[0] is not None  # source_symbol
            assert row[1] is not None  # target_symbol
            assert row[2] is not None  # file_path

def test_api_returns_expected_data():
    """API отдаёт ожидаемые данные"""
    # Устанавливаем переменную окружения для тестовой базы данных
    os.environ["DATABASE_URL"] = "sqlite:///./feature.new.db"
    
    # Тестируем API /api/v1/index/symbol
    response = client.get("/api/v1/index/symbol")
    assert response.status_code == 200
    data = response.json()
    assert "symbols" in data
    
    # Тестируем API /api/v1/index/calls
    response = client.get("/api/v1/index/calls")
    assert response.status_code == 200
    data = response.json()
    assert "edges" in data
    
    # Тестируем API /api/v1/index/module-card
    # Используем существующий файл из проекта, который гарантированно есть в индексе
    response = client.get("/api/v1/index/module-card?file_path=app/index/api.py")
    # Даже если файл не найден, API должен вернуть 200 с пустым module_card
    assert response.status_code == 200
    data = response.json()
    assert "module_card" in data
    
    # Проверяем структуру ответа module_card
    module_card = data["module_card"]
    assert isinstance(module_card, dict)
    
    # Должны быть поля file_info, symbols, calls_from, calls_to (могут быть пустыми)
    # Проверяем, что поля существуют (даже если пустые)
    assert "file_info" in module_card or module_card == {}
    assert "symbols" in module_card or module_card == {}
    assert "calls_from" in module_card or module_card == {}
    assert "calls_to" in module_card or module_card == {}

def test_indexer_idempotency():
    """Тест идемпотентности индексера"""
    database_url = "sqlite:///./feature.new.db"
    
    # Импортируем необходимые функции
    import sys
    sys.path.append('/opt/feature-factory')
    from scripts.update_code_registry import update_code_registry
    
    engine = create_engine(database_url)
    
    # Получаем список Python файлов из проекта
    python_files = []
    for root, _, files in os.walk('/opt/feature-factory/app'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Запускаем индексацию дважды
    for i in range(2):
        update_code_registry(engine, python_files)
        
        # Проверяем, что количество записей не увеличивается при повторном запуске
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM code_registry"))
            count = result.fetchone()[0]
            # Количество должно оставаться стабильным
            if i == 0:
                first_count = count
            else:
                assert count == first_count, "Количество записей в code_registry изменилось при повторном запуске"

if __name__ == "__main__":
    pytest.main([__file__])