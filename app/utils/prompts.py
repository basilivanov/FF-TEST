#!/usr/bin/env python3
"""
Утилиты для работы с промптами агентов.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Optional


def load_prompt_from_file(prompt_file: str) -> str:
    """
    Загружает промпт из файла.
    
    Args:
        prompt_file: Путь к файлу с промптом относительно корня проекта
        
    Returns:
        Содержимое файла промпта как строка
    """
    project_root = Path("/opt/feature-factory")
    full_path = project_root / prompt_file
    
    if not full_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {full_path}")
    
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_role_prompt(role: str, prompt_type: Optional[str] = None) -> str:
    """
    Получает промпт для роли из конфигурации с fallback поддержкой.
    
    Args:
        role: Название роли (Maintainer, Dev, QA, etc.)
        prompt_type: Тип промпта (например "chat" для диалогового режима)
        
    Returns:
        Содержимое промпта как строка
    """
    config_path = Path("/opt/feature-factory/configs/prompts.yaml")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    role_config = config.get('roles', {}).get(role)
    if not role_config:
        raise ValueError(f"Role {role} not found in prompts.yaml")
    
    # Если указан специальный тип промпта, попробуем найти его
    if prompt_type:
        prompt_file = role_config['file'].replace('.md', f'_{prompt_type}.md')
        try:
            return load_prompt_from_file(prompt_file)
        except FileNotFoundError:
            # Если специальный промпт не найден, используем основной
            pass
    
    # Пробуем загрузить основной промпт роли
    try:
        return load_prompt_from_file(role_config['file'])
    except FileNotFoundError:
        # Если основной промпт не найден, пробуем fallback
        fallback_file = role_config.get('fallback_file')
        if fallback_file:
            try:
                return load_prompt_from_file(fallback_file)
            except FileNotFoundError:
                pass
        
        # Если ничего не найдено, поднимаем ошибку
        raise FileNotFoundError(f"Neither main prompt file '{role_config['file']}' nor fallback file '{fallback_file}' found for role {role}")


def load_prompt_content(prompt_filename: str) -> str:
    """
    Загружает содержимое промпта из папки app/agents/prompts/.
    
    Args:
        prompt_filename: Имя файла промпта (например, "internal_analyst.md")
        
    Returns:
        Содержимое файла промпта как строка
    """
    prompt_path = Path("/opt/feature-factory/app/agents/prompts") / prompt_filename
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()
