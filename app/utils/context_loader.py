#!/usr/bin/env python3
"""
Загрузка контекста системы для LLM.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Any
import os
import yaml
import json

def load_system_context(db: Session) -> str:
    """
    Загружает полный контекст системы для передачи в LLM.
    
    Args:
        db: Сессия базы данных
        
    Returns:
        str: Форматированный контекст системы
    """
    context_parts = []
    
    # 1. Основная информация о системе
    context_parts.append("=== КОНТЕКСТ СИСТЕМЫ FEATURE FACTORY ===")
    context_parts.append("")
    context_parts.append("Вы работаете с системой Feature Factory - платформой для автоматизации бизнес-процессов.")
    context_parts.append("Ваша роль: помогать пользователям создавать автоматизированные решения.")
    context_parts.append("")
    
    # 2. Существующие фичи
    try:
        features_result = db.execute(
            text("""
                SELECT id, title, status, created_at, intent_json
                FROM features 
                ORDER BY created_at DESC 
                LIMIT 20
            """)
        )
        features = features_result.fetchall()
        
        if features:
            context_parts.append("=== СУЩЕСТВУЮЩИЕ АВТОМАТИЗАЦИИ ===")
            for feature in features:
                fid, title, status, created_at, intent_json_str = feature
                
                # Извлекаем описание из intent_json
                summary = ""
                if intent_json_str:
                    try:
                        intent_data = json.loads(intent_json_str)
                        # В intent.json описание лежит в intent -> summary
                        summary = intent_data.get("intent", {}).get("summary", "")
                    except json.JSONDecodeError:
                        summary = "Не удалось прочитать описание."
                
                context_parts.append(f"• [{status}] {title}")
                if summary:
                    context_parts.append(f"  Описание: {summary}")
                context_parts.append(f"  ID: {fid}, Создано: {created_at}")
            context_parts.append("")
        else:
            context_parts.append("=== СУЩЕСТВУЮЩИЕ АВТОМАТИЗАЦИИ ===")
            context_parts.append("Пока нет созданных автоматизаций.")
            context_parts.append("")
    except Exception as e:
        context_parts.append(f"⚠️ Ошибка загрузки фичей: {e}")
        context_parts.append("")
    
    # 3. Доступные типы автоматизации
    context_parts.append("=== ТИПЫ АВТОМАТИЗАЦИИ ===")
    context_parts.append("• Telegram уведомления")
    context_parts.append("• Сбор данных с веб-сайтов")
    context_parts.append("• Создание отчетов (Excel, Google Sheets)")
    context_parts.append("• Интеграции с маркетплейсами")
    context_parts.append("• Email рассылки")
    context_parts.append("• Мониторинг сервисов")
    context_parts.append("• Обработка файлов")
    context_parts.append("")
    
    # 4. Краткая архитектурная информация
    context_parts.append("=== ВОЗМОЖНОСТИ СИСТЕМЫ ===")
    context_parts.append("• Поддержка Python, JavaScript, SQL автоматизации")
    context_parts.append("• Интеграция с Telegram, Email, Google Sheets")
    context_parts.append("• Веб-скрапинг и API интеграции")
    context_parts.append("• Периодические задачи (cron-like)")
    context_parts.append("")
        
    # 5. Бюджеты и лимиты  
    try:
        budgets_path = "/opt/feature-factory/configs/llm_budgets.yaml"
        if os.path.exists(budgets_path):
            with open(budgets_path, 'r') as f:
                budgets = yaml.safe_load(f)
            context_parts.append("=== ЛИМИТЫ СИСТЕМЫ ===")
            context_parts.append("Дневные лимиты токенов по ролям:")
            for role, limit in budgets.items():
                context_parts.append(f"• {role}: {limit} токенов")
            context_parts.append("")
    except Exception:
        pass
        
    # 6. Инструкции по общению
    context_parts.append("=== ИНСТРУКЦИИ ПО ОБЩЕНИЮ ===")
    context_parts.append("• Используйте простой язык, избегайте технических терминов")
    context_parts.append("• НЕ используйте слова: API, эндпоинт, webhook, cron, JSON, база данных")
    context_parts.append("• Задавайте уточняющие вопросы с конкретными вариантами")
    context_parts.append("• Предлагайте готовые решения")
    context_parts.append("• Будьте дружелюбны и терпеливы")
    context_parts.append("")
    
    return "\n".join(context_parts)

def get_features_summary(db: Session) -> List[Dict[str, Any]]:
    """
    Получает краткую сводку по фичам для быстрого доступа.
    
    Args:
        db: Сессия базы данных
        
    Returns:
        List[Dict]: Список фичей с краткой информацией
    """
    try:
        result = db.execute(
            text("""
                SELECT id, title, status, created_at 
                FROM features 
                ORDER BY 
                    CASE status 
                        WHEN 'IN_PROGRESS' THEN 1
                        WHEN 'DONE' THEN 2 
                        WHEN 'FAILED' THEN 3
                        ELSE 4 
                    END,
                    created_at DESC 
                LIMIT 10
            """)
        )
        
        features = []
        for row in result.fetchall():
            features.append({
                "id": row[0],
                "title": row[1], 
                "status": row[2],
                "created_at": str(row[3])
            })
        return features
    except Exception:
        return []