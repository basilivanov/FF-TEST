#!/usr/bin/env python3
"""
Утилиты для работы с датами и временем.
"""

from datetime import datetime, timezone
from typing import Optional


def serialize_datetime_utc(dt: Optional[datetime]) -> str:
    """
    Сериализует datetime в ISO-8601 UTC формат с 'Z'.
    
    Args:
        dt: datetime объект для сериализации (может быть None)
        
    Returns:
        str: ISO-8601 строка с 'Z' или пустая строка если dt is None
    """
    if dt is None:
        return ""
    
    # Если объект не имеет timezone info, считаем его UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        # Конвертируем в UTC
        dt = dt.astimezone(timezone.utc)
    
    # Возвращаем ISO формат с 'Z' (убираем микросекунды для простоты)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def serialize_datetime_safe(dt) -> str:
    """
    Безопасная сериализация datetime объектов.
    Обрабатывает разные типы входных данных.
    
    Args:
        dt: datetime объект, строка или None
        
    Returns:
        str: ISO-8601 строка с 'Z' или пустая строка
    """
    if dt is None:
        return ""
    
    # Если это уже строка
    if isinstance(dt, str):
        if dt == "":
            return ""
        # Если уже есть 'Z', возвращаем как есть
        if dt.endswith('Z'):
            return dt
        # Если это SQLite формат "YYYY-MM-DD HH:MM:SS", конвертируем в ISO с 'Z'
        if ' ' in dt and 'T' not in dt:
            return dt.replace(' ', 'T') + 'Z'
        # Добавляем 'Z' если это ISO формат
        if 'T' in dt:
            return dt + 'Z'
        else:
            return dt
    
    # Если это datetime объект
    if hasattr(dt, 'isoformat'):
        return serialize_datetime_utc(dt)
    
    # Если это другой тип, пытаемся конвертировать в строку
    return str(dt)