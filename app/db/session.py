from __future__ import annotations
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from typing import Generator
import os

# Получаем DATABASE_URL из переменных окружения или завершаем работу с ошибкой
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Функция для настройки SQLite PRAGMA
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Устанавливает PRAGMA для SQLite."""
    if DATABASE_URL.startswith("sqlite:///"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Получает сессию базы данных.
    
    Yields:
        Session: Сессия базы данных
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()