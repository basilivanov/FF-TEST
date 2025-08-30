#!/usr/bin/env python3
"""
Утилиты для работы с шаблонами фичей.
Поддерживает двухрежимную логику BusinessAnalyst:
- Режим 1: Использование существующих шаблонов
- Режим 2: Протокол Обнаружения для неизвестных задач
"""

import os
import yaml
import glob
from typing import Dict, List, Optional, Any, Tuple
import structlog

logger = structlog.get_logger()

TEMPLATES_DIR = "/opt/feature-factory/configs/feature_templates"

class FeatureTemplate:
    """Класс для работы с отдельным шаблоном фичи."""
    
    def __init__(self, template_path: str, data: Dict[str, Any]):
        self.path = template_path
        self.data = data
        self.name = data.get("name", "")
        self.description = data.get("description", "")
        self.category = data.get("category", "")
        self.keywords = data.get("keywords", [])
        self.required_slots = data.get("required_slots", {})
        self.optional_slots = data.get("optional_slots", {})
        self.clarification_questions = data.get("clarification_questions", [])
        self.technical_spec = data.get("technical_spec", {})
    
    def matches_query(self, query: str) -> float:
        """
        Проверяет, соответствует ли запрос этому шаблону.
        Возвращает score от 0.0 до 1.0.
        """
        query_lower = query.lower()
        score = 0.0
        
        # Проверяем ключевые слова
        for keyword in self.keywords:
            if keyword.lower() in query_lower:
                score += 0.3
        
        # Проверяем название шаблона
        if self.name.lower() in query_lower:
            score += 0.4
        
        # Проверяем описание
        if any(word in query_lower for word in self.description.lower().split()):
            score += 0.2
        
        # Проверяем категорию
        if self.category.lower() in query_lower:
            score += 0.1
            
        return min(score, 1.0)
    
    def get_missing_slots(self, provided_data: Dict[str, Any]) -> List[str]:
        """Возвращает список обязательных полей, которые не предоставлены."""
        missing = []
        for slot_name, slot_info in self.required_slots.items():
            if slot_name not in provided_data:
                missing.append(slot_name)
        return missing
    
    def generate_questions(self, missing_slots: List[str]) -> List[str]:
        """Генерирует вопросы для недостающих обязательных полей."""
        questions = []
        for slot_name in missing_slots:
            if slot_name in self.required_slots:
                slot_info = self.required_slots[slot_name]
                prompt = slot_info.get("prompt", f"Укажите {slot_name}")
                example = slot_info.get("example", "")
                
                question = prompt
                if example:
                    question += f"\nПример: {example}"
                questions.append(question)
        
        return questions


class FeatureTemplateManager:
    """Менеджер для работы с библиотекой шаблонов фичей."""
    
    def __init__(self):
        self.templates: List[FeatureTemplate] = []
        self.load_templates()
    
    def load_templates(self):
        """Загружает все шаблоны из директории."""
        self.templates = []
        
        if not os.path.exists(TEMPLATES_DIR):
            logger.warning("Templates directory not found", path=TEMPLATES_DIR)
            return
        
        # Ищем все YAML файлы в поддиректориях
        pattern = os.path.join(TEMPLATES_DIR, "**", "*.yaml")
        template_files = glob.glob(pattern, recursive=True)
        
        for template_file in template_files:
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                template = FeatureTemplate(template_file, data)
                self.templates.append(template)
                
                logger.info(
                    "Template loaded",
                    path=template_file,
                    name=template.name,
                    keywords=template.keywords
                )
                
            except Exception as e:
                logger.error(
                    "Failed to load template",
                    path=template_file,
                    error=str(e)
                )
    
    def find_best_template(self, query: str, threshold: float = 0.3) -> Optional[FeatureTemplate]:
        """
        Находит наиболее подходящий шаблон для запроса.
        Возвращает None, если ни один шаблон не подходит (score < threshold).
        """
        if not self.templates:
            return None
        
        best_template = None
        best_score = 0.0
        
        for template in self.templates:
            score = template.matches_query(query)
            if score > best_score:
                best_score = score
                best_template = template
        
        if best_score >= threshold:
            logger.info(
                "Template found",
                query=query,
                template=best_template.name,
                score=best_score
            )
            return best_template
        
        logger.info(
            "No suitable template found",
            query=query,
            best_score=best_score,
            threshold=threshold
        )
        return None
    
    def get_discovery_protocol_questions(self) -> List[str]:
        """
        Возвращает базовые вопросы для "Протокола Обнаружения"
        когда подходящий шаблон не найден.
        """
        return [
            "🎯 **Какую систему или сервис нужно интегрировать?** (название, ссылка на документацию)",
            "🔑 **Как происходит аутентификация?** (API ключи, OAuth, токены и т.д.)",
            "📡 **Какие данные нужно получать или отправлять?** (формат, частота, объем)",
            "✅ **Критерии успеха:** Как понять, что интеграция работает правильно?",
            "⚡ **Приоритет задачи:** Высокий / Средний / Низкий?",
            "🚀 **Дедлайн:** Есть ли временные ограничения?"
        ]
    
    def extract_data_from_query(self, query: str) -> Dict[str, Any]:
        """
        Извлекает данные из текста запроса (простая эвристика).
        В реальной реализации можно использовать NLP.
        """
        extracted = {}
        query_lower = query.lower()
        
        # Примеры простого извлечения данных
        if "telegram" in query_lower or "телеграм" in query_lower:
            extracted["platform"] = "telegram"
        
        if "уведомления" in query_lower or "notification" in query_lower:
            extracted["type"] = "notifications"
        
        # Поиск токенов (примитивная проверка)
        import re
        token_pattern = r'\b\d{8,10}:[A-Za-z0-9_-]{35}\b'
        tokens = re.findall(token_pattern, query)
        if tokens:
            extracted["bot_token"] = tokens[0]
        
        # Поиск username/chat_id
        username_pattern = r'@(\w+)'
        usernames = re.findall(username_pattern, query)
        if usernames:
            extracted["recipient"] = f"@{usernames[0]}"
        
        return extracted


# Глобальный экземпляр менеджера шаблонов
template_manager = FeatureTemplateManager()

def reload_templates():
    """Перезагружает все шаблоны (для использования в development)."""
    global template_manager
    template_manager.load_templates()

def find_template_for_query(query: str) -> Tuple[Optional[FeatureTemplate], Dict[str, Any]]:
    """
    Основная функция для поиска шаблона и извлечения данных из запроса.
    
    Returns:
        Tuple[Optional[FeatureTemplate], Dict[str, Any]]: 
        (найденный шаблон или None, извлеченные из запроса данные)
    """
    template = template_manager.find_best_template(query)
    extracted_data = template_manager.extract_data_from_query(query)
    
    return template, extracted_data

def get_discovery_questions() -> List[str]:
    """Возвращает вопросы для Протокола Обнаружения."""
    return template_manager.get_discovery_protocol_questions()