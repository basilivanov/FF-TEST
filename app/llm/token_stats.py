#!/usr/bin/env python3
"""
Модуль для хранения и управления статистикой токенов.
"""

import sqlite3
from datetime import datetime, date
from typing import Dict, Optional
import os

class TokenStats:
    """Класс для хранения статистики токенов."""
    
    def __init__(self, db_path: str = None):
        """
        Инициализирует статистику токенов.
        
        Args:
            db_path (str): Путь к базе данных. Если None, используется DATABASE_URL из переменных окружения.
        """
        if db_path is None:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL environment variable is required")
            if database_url.startswith("sqlite:///"):
                db_path = database_url.replace("sqlite:///", "")
            else:
                raise NotImplementedError("Only SQLite database is supported for token stats")
        
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализирует таблицу для хранения статистики токенов."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS token_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        agent_role TEXT NOT NULL,
                        model TEXT NOT NULL,
                        input_tokens INTEGER NOT NULL DEFAULT 0,
                        output_tokens INTEGER NOT NULL DEFAULT 0,
                        total_calls INTEGER NOT NULL DEFAULT 0,
                        UNIQUE(date, agent_role, model)
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"Ошибка инициализации базы данных: {e}")
    
    def record_tokens(self, agent_role: str, model: str, input_tokens: int, output_tokens: int):
        """
        Записывает статистику токенов.
        
        Args:
            agent_role (str): Роль агента
            model (str): Название модели
            input_tokens (int): Количество входных токенов
            output_tokens (int): Количество выходных токенов
        """
        try:
            today = date.today()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Обновляем или вставляем запись
                cursor.execute("""
                    INSERT OR REPLACE INTO token_stats 
                    (date, agent_role, model, input_tokens, output_tokens, total_calls)
                    VALUES (?, ?, ?, 
                           COALESCE((SELECT input_tokens FROM token_stats WHERE date = ? AND agent_role = ? AND model = ?), 0) + ?,
                           COALESCE((SELECT output_tokens FROM token_stats WHERE date = ? AND agent_role = ? AND model = ?), 0) + ?,
                           COALESCE((SELECT total_calls FROM token_stats WHERE date = ? AND agent_role = ? AND model = ?), 0) + 1)
                """, (
                    today, agent_role, model,
                    today, agent_role, model, input_tokens,
                    today, agent_role, model, output_tokens,
                    today, agent_role, model
                ))
                conn.commit()
        except Exception as e:
            print(f"Ошибка записи статистики токенов: {e}")
    
    def get_daily_stats(self, target_date: Optional[date] = None) -> Dict:
        """
        Получает статистику токенов за день.
        
        Args:
            target_date (Optional[date]): Дата для получения статистики (по умолчанию сегодня)
            
        Returns:
            Dict: Статистика токенов
        """
        if target_date is None:
            target_date = date.today()
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT agent_role, model, input_tokens, output_tokens, total_calls
                    FROM token_stats
                    WHERE date = ?
                    ORDER BY agent_role, model
                """, (target_date,))
                
                stats = {}
                for row in cursor.fetchall():
                    agent_role, model, input_tokens, output_tokens, total_calls = row
                    if agent_role not in stats:
                        stats[agent_role] = {}
                    stats[agent_role][model] = {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_calls": total_calls
                    }
                
                return stats
        except Exception as e:
            print(f"Ошибка получения статистики токенов: {e}")
            return {}

# Глобальный экземпляр статистики токенов
token_stats = TokenStats()

def get_token_stats() -> TokenStats:
    """
    Получает глобальный экземпляр статистики токенов.
    
    Returns:
        TokenStats: Глобальный экземпляр статистики токенов
    """
    return token_stats