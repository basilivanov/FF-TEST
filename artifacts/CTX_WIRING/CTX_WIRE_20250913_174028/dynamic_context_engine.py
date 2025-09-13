#!/usr/bin/env python3
"""
Динамический движок контекста через symbol_index и call_graph
"""
import re
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import json

@dataclass
class SymbolInfo:
    """Информация о символе из БД"""
    file_path: str
    symbol_name: str
    symbol_type: str  # function, class, variable, etc.
    line_start: int
    line_end: int
    relevance_score: float = 0.0

@dataclass
class FileContext:
    """Контекст файла с символами"""
    file_path: str
    symbols: List[SymbolInfo]
    content: str
    relevance_score: float = 0.0

class DynamicContextEngine:
    """Движок для динамического поиска релевантного контекста"""
    
    def __init__(self, db_path: str = "/opt/feature-factory/data/test.db"):
        self.db_path = db_path
        self.project_root = Path("/opt/feature-factory")
        
        # Паттерны для извлечения ключевых слов
        self.keyword_patterns = {
            "entities": r'\b(user|project|task|feature|job|agent)\b',
            "operations": r'\b(create|update|delete|get|post|put|patch)\b',
            "technologies": r'\b(fastapi|pydantic|sqlalchemy|alembic|pytest)\b',
            "components": r'\b(api|endpoint|schema|model|service|controller)\b'
        }
    
    def build_dynamic_context(self, task: Dict[str, Any], role: str) -> str:
        """Строит динамический контекст на основе задачи и роли"""
        user_intent = task.get("user_intent", "")
        task_title = task.get("title", "")
        
        # 1. Извлекаем ключевые слова
        keywords = self._extract_keywords(user_intent + " " + task_title)
        
        # 2. Ищем релевантные символы в БД
        symbols = self._find_relevant_symbols(keywords, role)
        
        # 3. Расширяем контекст через call graph
        expanded_files = self._expand_via_call_graph(symbols)
        
        # 4. Получаем содержимое файлов
        file_contexts = self._get_file_contexts(expanded_files, keywords)
        
        # 5. Формируем финальный контекст
        return self._build_context_markdown(file_contexts, keywords, role)
    
    def _extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """Извлекает ключевые слова по категориям"""
        text_lower = text.lower()
        keywords = {}
        
        for category, pattern in self.keyword_patterns.items():
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            keywords[category] = list(set(matches))  # Убираем дубли
        
        # Дополнительные ключевые слова через простой парсинг
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', text)
        keywords['custom'] = [w.lower() for w in words if len(w) > 3][:10]  # Топ-10 слов
        
        return keywords
    
    def _find_relevant_symbols(self, keywords: Dict[str, List[str]], role: str) -> List[SymbolInfo]:
        """Находит релевантные символы в symbol_index"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Объединяем все ключевые слова
                all_keywords = []
                for category, words in keywords.items():
                    all_keywords.extend(words)
                
                if not all_keywords:
                    return []
                
                # Создаем LIKE паттерны для поиска
                like_patterns = [f"%{keyword}%" for keyword in all_keywords[:20]]  # Ограничиваем количество
                placeholders = ",".join("?" * len(like_patterns))
                
                # SQL запрос с приоритизацией по типу символа и роли
                query = f"""
                SELECT 
                    si.file_path,
                    si.symbol_name,
                    si.symbol_type,
                    si.line_start,
                    si.line_end,
                    CASE 
                        WHEN si.symbol_type = 'function' THEN 3
                        WHEN si.symbol_type = 'class' THEN 2
                        WHEN si.symbol_type = 'variable' THEN 1
                        ELSE 0
                    END as type_priority,
                    CASE
                        WHEN si.file_path LIKE '%/api/%' AND ? = 'Dev' THEN 2
                        WHEN si.file_path LIKE '%/models/%' AND ? = 'Dev' THEN 2
                        WHEN si.file_path LIKE '%/schemas/%' AND ? = 'Dev' THEN 2
                        WHEN si.file_path LIKE '%test%' AND ? = 'QA' THEN 2
                        ELSE 1
                    END as role_priority
                FROM symbol_index si
                WHERE (
                    {" OR ".join([f"si.symbol_name LIKE ?" for _ in like_patterns])}
                    OR {" OR ".join([f"si.file_path LIKE ?" for _ in like_patterns])}
                )
                ORDER BY type_priority DESC, role_priority DESC, si.symbol_name
                LIMIT 50
                """
                
                params = [role, role, role] + like_patterns * 2
                cursor.execute(query, params)
                
                symbols = []
                for row in cursor.fetchall():
                    symbol = SymbolInfo(
                        file_path=row['file_path'],
                        symbol_name=row['symbol_name'],
                        symbol_type=row['symbol_type'],
                        line_start=row['line_start'],
                        line_end=row['line_end'],
                        relevance_score=row['type_priority'] + row['role_priority']
                    )
                    symbols.append(symbol)
                
                return symbols
                
        except Exception as e:
            print(f"Ошибка поиска символов: {e}")
            return []
    
    def _expand_via_call_graph(self, symbols: List[SymbolInfo]) -> List[str]:
        """Расширяет список файлов через call_graph_edges"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Получаем уникальные файлы из символов
                primary_files = list(set(s.file_path for s in symbols))
                
                if not primary_files:
                    return []
                
                # Ищем связанные файлы через call graph
                placeholders = ",".join("?" * len(primary_files))
                query = f"""
                SELECT DISTINCT target_file 
                FROM call_graph_edges 
                WHERE source_file IN ({placeholders})
                
                UNION
                
                SELECT DISTINCT source_file
                FROM call_graph_edges 
                WHERE target_file IN ({placeholders})
                
                LIMIT 20
                """
                
                cursor.execute(query, primary_files * 2)
                related_files = [row[0] for row in cursor.fetchall()]
                
                # Объединяем primary + related файлы
                all_files = list(set(primary_files + related_files))
                return all_files[:25]  # Ограничиваем общее количество
                
        except Exception as e:
            print(f"Ошибка расширения через call graph: {e}")
            return list(set(s.file_path for s in symbols))
    
    def _get_file_contexts(self, file_paths: List[str], keywords: Dict[str, List[str]]) -> List[FileContext]:
        """Получает содержимое файлов и создает контексты"""
        contexts = []
        
        for file_path in file_paths:
            full_path = self.project_root / file_path.lstrip('/')
            
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Ограничиваем размер файла
                if len(content) > 5000:
                    content = content[:5000] + "\n# ... (файл обрезан)"
                
                # Вычисляем релевантность файла
                relevance = self._calculate_file_relevance(content, keywords)
                
                context = FileContext(
                    file_path=file_path,
                    symbols=[],  # Можно заполнить символами из этого файла
                    content=content,
                    relevance_score=relevance
                )
                contexts.append(context)
                
            except Exception as e:
                print(f"Ошибка чтения файла {file_path}: {e}")
                continue
        
        # Сортируем по релевантности
        contexts.sort(key=lambda x: x.relevance_score, reverse=True)
        return contexts[:10]  # Топ-10 наиболее релевантных файлов
    
    def _calculate_file_relevance(self, content: str, keywords: Dict[str, List[str]]) -> float:
        """Вычисляет релевантность файла по ключевым словам"""
        content_lower = content.lower()
        relevance = 0.0
        
        # Веса для разных категорий ключевых слов
        category_weights = {
            'entities': 3.0,
            'operations': 2.0,
            'technologies': 1.5,
            'components': 2.0,
            'custom': 1.0
        }
        
        for category, words in keywords.items():
            weight = category_weights.get(category, 1.0)
            for word in words:
                count = content_lower.count(word.lower())
                relevance += count * weight
        
        return relevance
    
    def _build_context_markdown(self, file_contexts: List[FileContext], keywords: Dict[str, List[str]], role: str) -> str:
        """Строит финальный markdown контекст"""
        if not file_contexts:
            return "# Динамический контекст\n\nРелевантные файлы не найдены."
        
        sections = []
        sections.append("# Динамический контекст")
        
        # Секция с ключевыми словами
        all_keywords = []
        for words in keywords.values():
            all_keywords.extend(words)
        
        if all_keywords:
            sections.append(f"## Анализ задачи\n\n**Ключевые понятия**: {', '.join(all_keywords[:15])}")
        
        # Секция с релевантными файлами
        sections.append("## Релевантные файлы")
        
        for i, context in enumerate(file_contexts):
            sections.append(f"### {i+1}. {context.file_path}")
            sections.append(f"**Релевантность**: {context.relevance_score:.1f}")
            
            # Определяем язык для подсветки синтаксиса
            if context.file_path.endswith('.py'):
                lang = 'python'
            elif context.file_path.endswith('.yaml') or context.file_path.endswith('.yml'):
                lang = 'yaml'
            elif context.file_path.endswith('.json'):
                lang = 'json'
            else:
                lang = ''
            
            sections.append(f"```{lang}\n{context.content}\n```")
        
        return "\n\n".join(sections)

# Функция для тестирования
def test_dynamic_context():
    """Тестирует работу динамического контекста"""
    engine = DynamicContextEngine()
    
    test_task = {
        "title": "Создать CRUD endpoint для пользователей",
        "user_intent": "Необходимо реализовать FastAPI endpoint /api/v1/users с методами GET, POST, PUT, DELETE для управления пользователями",
        "role": "Dev"
    }
    
    context = engine.build_dynamic_context(test_task, "Dev")
    return context

if __name__ == "__main__":
    # Запуск теста
    result = test_dynamic_context()
    print(result[:2000])  # Первые 2000 символов