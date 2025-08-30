#!/usr/bin/env python3
"""
Сервис индексации кода.
Предоставляет функции для работы с индексом кода, включая поиск символов и анализ графа вызовов.
"""

import os
import json
from typing import List, Dict, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import structlog

# Настройка логгера
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()

class IndexService:
    """Сервис для работы с индексом кода."""
    
    def __init__(self, database_url: str = None):
        """Инициализирует сервис индексации.
        
        Args:
            database_url (str, optional): URL базы данных. Если не указан, используется из переменной окружения.
        """
        if database_url is None:
            self.database_url = os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/index.db")
        else:
            self.database_url = database_url
        self.engine = create_engine(self.database_url)
    
    def get_symbol(self, symbol_name: str = None, file_path: str = None) -> List[Dict]:
        """Получает информацию о символах из индекса.
        
        Args:
            symbol_name (str, optional): Имя символа для поиска
            file_path (str, optional): Путь к файлу для поиска
            
        Returns:
            List[Dict]: Список символов
        """
        try:
            with self.engine.connect() as conn:
                if symbol_name and file_path:
                    result = conn.execute(text("""
                        SELECT * FROM symbol_index 
                        WHERE symbol_name = :symbol_name AND file_path = :file_path
                    """), {
                        'symbol_name': symbol_name,
                        'file_path': file_path
                    })
                elif symbol_name:
                    result = conn.execute(text("""
                        SELECT * FROM symbol_index 
                        WHERE symbol_name = :symbol_name
                    """), {
                        'symbol_name': symbol_name
                    })
                elif file_path:
                    result = conn.execute(text("""
                        SELECT * FROM symbol_index 
                        WHERE file_path = :file_path
                    """), {
                        'file_path': file_path
                    })
                else:
                    result = conn.execute(text("SELECT * FROM symbol_index LIMIT 100"))
                
                symbols = []
                for row in result:
                    symbols.append({
                        'id': row[0],
                        'file_path': row[1],
                        'symbol_name': row[2],
                        'symbol_type': row[3],
                        'line_start': row[4],
                        'line_end': row[5]
                    })
                
                return symbols
        except SQLAlchemyError as e:
            log.error("db_error", error=str(e))
            raise
    
    def get_calls(self, source_symbol: str = None, target_symbol: str = None, file_path: str = None) -> List[Dict]:
        """Получает информацию о вызовах из графа вызовов.
        
        Args:
            source_symbol (str, optional): Имя исходного символа
            target_symbol (str, optional): Имя целевого символа
            file_path (str, optional): Путь к файлу для поиска
            
        Returns:
            List[Dict]: Список ребер графа вызовов
        """
        try:
            with self.engine.connect() as conn:
                if source_symbol and target_symbol and file_path:
                    result = conn.execute(text("""
                        SELECT * FROM call_graph_edges 
                        WHERE source_symbol = :source_symbol 
                        AND target_symbol = :target_symbol 
                        AND file_path = :file_path
                    """), {
                        'source_symbol': source_symbol,
                        'target_symbol': target_symbol,
                        'file_path': file_path
                    })
                elif source_symbol and target_symbol:
                    result = conn.execute(text("""
                        SELECT * FROM call_graph_edges 
                        WHERE source_symbol = :source_symbol 
                        AND target_symbol = :target_symbol
                    """), {
                        'source_symbol': source_symbol,
                        'target_symbol': target_symbol
                    })
                elif source_symbol:
                    result = conn.execute(text("""
                        SELECT * FROM call_graph_edges 
                        WHERE source_symbol = :source_symbol
                    """), {
                        'source_symbol': source_symbol
                    })
                elif target_symbol:
                    result = conn.execute(text("""
                        SELECT * FROM call_graph_edges 
                        WHERE target_symbol = :target_symbol
                    """), {
                        'target_symbol': target_symbol
                    })
                elif file_path:
                    result = conn.execute(text("""
                        SELECT * FROM call_graph_edges 
                        WHERE file_path = :file_path
                    """), {
                        'file_path': file_path
                    })
                else:
                    result = conn.execute(text("SELECT * FROM call_graph_edges LIMIT 100"))
                
                edges = []
                for row in result:
                    edges.append({
                        'id': row[0],
                        'source_symbol': row[1],
                        'target_symbol': row[2],
                        'file_path': row[3],
                        'line_number': row[4]
                    })
                
                return edges
        except SQLAlchemyError as e:
            log.error("db_error", error=str(e))
            raise
    
    def get_module_card(self, file_path: str) -> Dict:
        """Получает карточку модуля.
        
        Args:
            file_path (str): Путь к файлу модуля
            
        Returns:
            Dict: Карточка модуля с информацией о символах и вызовах
        """
        try:
            # Получаем информацию о файле из code_registry
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM code_registry 
                    WHERE file_path = :file_path
                """), {
                    'file_path': file_path
                })
                
                file_info = None
                for row in result:
                    file_info = {
                        'id': row[0],
                        'file_path': row[1],
                        'sha256': row[2],
                        'indexed_at': row[3]
                    }
                    break
            
            if not file_info:
                return {}
            
            # Получаем символы из файла
            symbols = self.get_symbol(file_path=file_path)
            
            # Получаем вызовы из файла
            calls = self.get_calls(file_path=file_path)
            
            # Получаем вызовы в файл
            calls_to = []
            for symbol in symbols:
                symbol_calls = self.get_calls(target_symbol=symbol['symbol_name'])
                calls_to.extend(symbol_calls)
            
            return {
                'file_info': file_info,
                'symbols': symbols,
                'calls_from': calls,
                'calls_to': calls_to
            }
        except SQLAlchemyError as e:
            log.error("db_error", error=str(e))
            raise

def get_index_service() -> IndexService:
    """Фабричная функция для получения экземпляра IndexService."""
    return IndexService()