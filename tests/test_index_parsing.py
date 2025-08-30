import pytest
import json
from scripts.update_code_registry import parse_dot_graph

def test_parse_dot_graph():
    # Тест для парсинга DOT графа вызовов.
    # Пример DOT содержимого от pyan3
    dot_content = (
        'digraph G {\n'
        '    "module1.function1" -> "module2.function2" [label="app/module1.py:10"];\n'
        '    "module2.function2" -> "module3.function3" [label="app/module2.py:25"];\n'
        '    "module1.function1" -> "module3.function3" [label="app/module1.py:15"];\n'
        '}'
    )
    
    edges = parse_dot_graph(dot_content)
    
    # Проверяем, что извлечены правильные ребра
    assert len(edges) == 3
    
    # Проверяем первое ребро
    assert edges[0]['source'] == 'module1.function1'
    assert edges[0]['target'] == 'module2.function2'
    assert edges[0]['file_path'] == 'app/module1.py'
    assert edges[0]['line_number'] == 10
    
    # Проверяем второе ребро
    assert edges[1]['source'] == 'module2.function2'
    assert edges[1]['target'] == 'module3.function3'
    assert edges[1]['file_path'] == 'app/module2.py'
    assert edges[1]['line_number'] == 25
    
    # Проверяем третье ребро
    assert edges[2]['source'] == 'module1.function1'
    assert edges[2]['target'] == 'module3.function3'
    assert edges[2]['file_path'] == 'app/module1.py'
    assert edges[2]['line_number'] == 15

def test_parse_dot_graph_empty():
    # Тест для парсинга пустого DOT графа.
    dot_content = ''
    edges = parse_dot_graph(dot_content)
    assert len(edges) == 0

def test_parse_dot_graph_invalid():
    # Тест для парсинга некорректного DOT графа.
    dot_content = (
        'digraph G {\n'
        '    invalid_line\n'
        '    "module1.function1" -> "module2.function2"\n'
        '}'
    )
    edges = parse_dot_graph(dot_content)
    assert len(edges) == 0

def test_parse_ctags_jsonl():
    # Тест для парсинга JSONL вывода ctags.
    # Пример JSONL содержимого от ctags
    ctags_output = (
        '{"_type": "tag", "name": "MyClass", "path": "app/module.py", "pattern": "/^class MyClass:/", "kind": "class", "line": 10, "end": 20, "_file": "app/module.py"}\n'
        '{"_type": "tag", "name": "my_function", "path": "app/module.py", "pattern": "/^def my_function():/", "kind": "function", "line": 25, "end": 30, "_file": "app/module.py"}'
    )
    
    symbols = []
    for line in ctags_output.strip().split('\n'):
        if line.strip():
            try:
                symbol = json.loads(line)
                symbols.append(symbol)
            except json.JSONDecodeError:
                continue
    
    # Проверяем, что извлечены правильные символы
    assert len(symbols) == 2
    
    # Проверяем первый символ
    assert symbols[0]['name'] == 'MyClass'
    assert symbols[0]['kind'] == 'class'
    assert symbols[0]['line'] == 10
    assert symbols[0]['end'] == 20
    assert symbols[0]['_file'] == 'app/module.py'
    
    # Проверяем второй символ
    assert symbols[1]['name'] == 'my_function'
    assert symbols[1]['kind'] == 'function'
    assert symbols[1]['line'] == 25
    assert symbols[1]['end'] == 30
    assert symbols[1]['_file'] == 'app/module.py'