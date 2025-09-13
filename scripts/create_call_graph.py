#!/usr/bin/env python3
"""
Альтернативный генератор графа вызовов для замены проблемного pyan3
Использует AST для анализа Python файлов и создания графа вызовов
"""

import ast
import os
import sys
import sqlite3
from typing import Dict, List, Set, Tuple
from pathlib import Path


class CallGraphAnalyzer(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.module_name = self._get_module_name(filepath)
        self.calls = []  # (caller, callee, line_number)
        self.current_function = None
        self.current_class = None
        
    def _get_module_name(self, filepath: str) -> str:
        """Получить имя модуля из пути файла"""
        path = Path(filepath)
        if path.name == '__init__.py':
            return str(path.parent).replace('/', '.').replace('\\', '.')
        else:
            return str(path.with_suffix('')).replace('/', '.').replace('\\', '.')
    
    def visit_FunctionDef(self, node):
        old_function = self.current_function
        if self.current_class:
            self.current_function = f"{self.current_class}.{node.name}"
        else:
            self.current_function = node.name
        
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Call(self, node):
        if self.current_function:
            callee = self._get_call_name(node)
            if callee:
                caller = f"{self.module_name}.{self.current_function}"
                self.calls.append((caller, callee, node.lineno))
        
        self.generic_visit(node)
    
    def _get_call_name(self, node) -> str:
        """Получить имя вызываемой функции"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return f"{self._get_attr_name(node.func.value)}.{node.func.attr}"
        return ""
    
    def _get_attr_name(self, node) -> str:
        """Получить имя атрибута/объекта"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attr_name(node.value)}.{node.attr}"
        return ""


def analyze_file(filepath: str) -> List[Tuple[str, str, int]]:
    """Анализировать один Python файл и вернуть список вызовов"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source, filepath)
        analyzer = CallGraphAnalyzer(filepath)
        analyzer.visit(tree)
        return analyzer.calls
    
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
        print(f"Ошибка анализа {filepath}: {e}")
        return []


def create_call_graph_from_files(py_files_path: str, output_db: str):
    """Создать граф вызовов из списка Python файлов и записать в БД"""
    
    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()
    
    # Очистить существующие данные
    cursor.execute("DELETE FROM call_graph_edges")
    
    total_edges = 0
    
    with open(py_files_path, 'r') as f:
        for line_num, filepath in enumerate(f, 1):
            filepath = filepath.strip()
            if not filepath or not filepath.endswith('.py'):
                continue
                
            print(f"Анализ {line_num}: {filepath}")
            
            calls = analyze_file(filepath)
            
            for caller, callee, line_no in calls:
                # Записываем в БД
                cursor.execute("""
                    INSERT INTO call_graph_edges 
                    (source_symbol, target_symbol, file_path, line_number) 
                    VALUES (?, ?, ?, ?)
                """, (caller, callee, filepath, line_no))
                total_edges += 1
    
    conn.commit()
    conn.close()
    
    print(f"Создано {total_edges} рёбер графа вызовов")
    return total_edges


def main():
    if len(sys.argv) < 3:
        print("Использование: python create_call_graph.py <py_files.txt> <output.db>")
        return 1
    
    py_files_path = sys.argv[1]
    output_db = sys.argv[2]
    
    if not os.path.exists(py_files_path):
        print(f"Файл {py_files_path} не найден")
        return 1
    
    edges_count = create_call_graph_from_files(py_files_path, output_db)
    
    print(f"✅ Граф вызовов успешно создан: {edges_count} рёбер")
    return 0


if __name__ == "__main__":
    sys.exit(main())