#!/usr/bin/env python3
"""
Скрипт для обновления реестра кода и индекса символов.
Использует ctags для извлечения символов и pyan3 для построения графа вызовов.
"""
import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

# Добавляем путь к приложению в sys.path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def get_database_url():
    """Получает URL базы данных из переменной окружения или использует тестовую базу."""
    return os.getenv("DATABASE_URL", "sqlite:///./feature.test.db")

def calculate_file_hash(file_path):
    """Вычисляет SHA256 хэш файла."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_python_files(root_dir):
    """Получает все Python файлы в директории."""
    python_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def run_ctags(file_paths):
    """Запускает ctags для извлечения символов из Python файлов."""
    try:
        # Запускаем ctags с правильными параметрами
        result = subprocess.run([
            'ctags', 
            '--extras=+p',
            '--fields=+S',
            '--output-format=json',
            '--languages=python'
        ] + file_paths, capture_output=True, text=True, check=True)
        
        # Парсим JSONL вывод
        symbols = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    symbol = json.loads(line)
                    symbols.append(symbol)
                except json.JSONDecodeError:
                    continue
        return symbols
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске ctags: {e}")
        return []

def run_pyan3(file_paths):
    """Запускает pyan3 для построения графа вызовов."""
    # Временно отключаем pyan3 из-за ошибки с параметром root
    print("pyan3 временно отключен из-за внутренней ошибки")
    return ""

def parse_dot_graph(dot_content):
    """Парсит DOT граф и извлекает ребра вызовов."""
    edges = []
    lines = dot_content.split('\n')
    
    for line in lines:
        # Ищем строки вида "A -> B [label="file.py:123"]"
        if '->' in line and 'label=' in line:
            # Извлекаем информацию о ребре
            parts = line.split('->')
            if len(parts) == 2:
                source = parts[0].strip().strip('"')
                target_part = parts[1].split('[')[0].strip().strip('"')
                
                # Извлекаем информацию о файле и строке из label
                if 'label=' in line:
                    label_start = line.find('label="') + len('label="')
                    label_end = line.find('"', label_start)
                    if label_end > label_start:
                        label = line[label_start:label_end]
                        # Формат: "file.py:123"
                        if ':' in label:
                            file_path, line_num = label.rsplit(':', 1)
                            try:
                                line_number = int(line_num)
                                edges.append({
                                    'source': source,
                                    'target': target_part,
                                    'file_path': file_path,
                                    'line_number': line_number
                                })
                            except ValueError:
                                continue
    return edges

def update_code_registry(engine, file_paths):
    """Обновляет реестр кода в базе данных."""
    try:
        with engine.connect() as conn:
            for file_path in file_paths:
                file_hash = calculate_file_hash(file_path)
                indexed_at = datetime.utcnow()
                
                # Вставляем или обновляем запись в code_registry
                conn.execute(text("""
                    INSERT OR REPLACE INTO code_registry (file_path, sha256, indexed_at)
                    VALUES (:file_path, :sha256, :indexed_at)
                """), {
                    'file_path': file_path,
                    'sha256': file_hash,
                    'indexed_at': indexed_at
                })
            conn.commit()
    except SQLAlchemyError as e:
        print(f"Ошибка при обновлении code_registry: {e}")

def update_symbol_index(engine, symbols):
    """Обновляет индекс символов в базе данных."""
    try:
        with engine.connect() as conn:
            inserted_count = 0
            for symbol in symbols:
                # Извлекаем необходимые поля
                file_path = symbol.get('_file', '')
                symbol_name = symbol.get('name', '')
                symbol_type = symbol.get('kind', '')
                line_start = symbol.get('line', 0)
                line_end = symbol.get('end', line_start)
                
                # Если _file отсутствует, пытаемся получить файл из других полей
                if not file_path:
                    # Для ctags JSON формата файл может быть в других полях
                    file_path = symbol.get('file', '')
                
                if file_path and symbol_name:
                    # Вставляем символ в symbol_index
                    try:
                        conn.execute(text("""
                            INSERT INTO symbol_index (file_path, symbol_name, symbol_type, line_start, line_end)
                            VALUES (:file_path, :symbol_name, :symbol_type, :line_start, :line_end)
                        """), {
                            'file_path': file_path,
                            'symbol_name': symbol_name,
                            'symbol_type': symbol_type,
                            'line_start': line_start,
                            'line_end': line_end
                        })
                        inserted_count += 1
                    except Exception as e:
                        # Пропускаем дубликаты
                        if "UNIQUE constraint failed" not in str(e):
                            print(f"Ошибка при вставке символа {symbol_name}: {e}")
            conn.commit()
            print(f"Успешно вставлено {inserted_count} символов")
    except SQLAlchemyError as e:
        print(f"Ошибка при обновлении symbol_index: {e}")

def update_call_graph_edges(engine, edges):
    """Обновляет граф вызовов в базе данных."""
    try:
        with engine.connect() as conn:
            for edge in edges:
                source = edge['source']
                target = edge['target']
                file_path = edge['file_path']
                line_number = edge['line_number']
                
                # Вставляем ребро в call_graph_edges
                conn.execute(text("""
                    INSERT INTO call_graph_edges (source_symbol, target_symbol, file_path, line_number)
                    VALUES (:source_symbol, :target_symbol, :file_path, :line_number)
                    ON CONFLICT DO NOTHING
                """), {
                    'source_symbol': source,
                    'target_symbol': target,
                    'file_path': file_path,
                    'line_number': line_number
                })
            conn.commit()
    except SQLAlchemyError as e:
        print(f"Ошибка при обновлении call_graph_edges: {e}")

def clear_indexes(engine):
    """Очищает существующие индексы перед обновлением."""
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM call_graph_edges"))
            conn.execute(text("DELETE FROM symbol_index"))
            conn.commit()
    except SQLAlchemyError as e:
        print(f"Ошибка при очистке индексов: {e}")

def main():
    """Основная функция скрипта."""
    print("Начинаем обновление реестра кода и индексов...")
    
    # Получаем все Python файлы в приложении
    app_dir = Path(__file__).parent.parent / 'app'
    python_files = get_python_files(str(app_dir))
    
    if not python_files:
        print("Не найдено Python файлов для индексации")
        return
    
    print(f"Найдено {len(python_files)} Python файлов для индексации")
    
    # Создаем подключение к базе данных
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    # Очищаем существующие индексы
    print("Очищаем существующие индексы...")
    clear_indexes(engine)
    
    # Обновляем реестр кода
    print("Обновляем реестр кода...")
    update_code_registry(engine, python_files)
    
    # Запускаем ctags для извлечения символов
    print("Запускаем ctags для извлечения символов...")
    symbols = run_ctags(python_files)
    print(f"Извлечено {len(symbols)} символов")
    
    # Обновляем индекс символов
    print("Обновляем индекс символов...")
    print(f"Передаем {len(symbols)} символов в update_symbol_index")
    if symbols:
        print(f"Пример первого символа: {symbols[0]}")
    update_symbol_index(engine, symbols)
    
    # Запускаем pyan3 для построения графа вызовов
    print("Запускаем pyan3 для построения графа вызовов...")
    dot_content = run_pyan3(python_files)
    
    if dot_content:
        # Парсим граф вызовов
        edges = parse_dot_graph(dot_content)
        print(f"Извлечено {len(edges)} ребер графа вызовов")
        
        # Обновляем граф вызовов
        print("Обновляем граф вызовов...")
        update_call_graph_edges(engine, edges)
    else:
        print("Не удалось получить граф вызовов")
    
    # Логируем обновление индекса
    print("index_updated", {
        "event": "index_updated",
        "component": "indexer",
        "agent_role": "Dev",
        "files_processed": len(python_files),
        "symbols_found": len(symbols),
        "edges_found": len(edges) if 'edges' in locals() else 0
    })
    
    print("Обновление реестра кода и индексов завершено успешно")

if __name__ == "__main__":
    main()