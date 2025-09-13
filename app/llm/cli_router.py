from __future__ import annotations
import yaml
import os
from typing import Dict, Any

def get_llm_providers() -> Dict[str, Any]:
    """
    Получает конфигурацию провайдеров LLM из файла конфигурации.
    
    Returns:
        Dict[str, Any]: Словарь с конфигурациями провайдеров
    """
    config_path = "/opt/feature-factory/configs/llm_cli_config.yaml"
    
    # Проверяем существование файла конфигурации
    if not os.path.exists(config_path):
        return {}
    
    # Читаем конфигурацию
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Преобразуем конфигурацию в формат, ожидаемый health check
    providers = {}
    for provider_name, provider_config in config.items():
        # Формируем путь к CLI бинарнику (первый элемент в cmd)
        if 'cmd' in provider_config and provider_config['cmd']:
            cli_path = provider_config['cmd'][0]
            providers[provider_name] = {
                "cli_path": cli_path,
                "config": provider_config
            }
    
    return providers