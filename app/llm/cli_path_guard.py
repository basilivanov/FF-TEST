#!/usr/bin/env python3
"""
Модуль для валидации путей CLI провайдеров и их проверки.
Обеспечивает безопасность и надежность CLI транспорта.
"""

import os
import subprocess
import yaml
from typing import Dict, Any, List, Tuple, Optional
import structlog

# Настройка логгера
logger = structlog.get_logger()

# Путь к конфигурационному файлу CLI
CLI_CONFIG_PATH = "/opt/feature-factory/configs/llm_cli.yaml"

class CliPathError(Exception):
    """Базовый класс для ошибок путей CLI."""
    pass

class CliBinaryNotFoundError(CliPathError):
    """Ошибка, когда бинарный файл CLI не найден."""
    pass

class CliPermissionError(CliPathError):
    """Ошибка прав доступа к бинарному файлу CLI."""
    pass

class CliConfigError(CliPathError):
    """Ошибка в конфигурации CLI."""
    pass

def _load_cli_config() -> Dict[str, Any]:
    """
    Загружает конфигурацию CLI из файла.
    
    Returns:
        Dict[str, Any]: Конфигурация CLI провайдеров
        
    Raises:
        CliConfigError: При ошибке загрузки или парсинга конфигурации
    """
    try:
        with open(CLI_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
            if not isinstance(config, dict):
                raise CliConfigError(f"Invalid config format in {CLI_CONFIG_PATH}")
            return config
    except FileNotFoundError:
        logger.error("cli_config_not_found", path=CLI_CONFIG_PATH)
        raise CliConfigError(f"CLI config file not found: {CLI_CONFIG_PATH}")
    except yaml.YAMLError as e:
        logger.error("cli_config_yaml_error", path=CLI_CONFIG_PATH, error=str(e))
        raise CliConfigError(f"Invalid YAML in CLI config: {e}")
    except Exception as e:
        logger.error("cli_config_load_error", path=CLI_CONFIG_PATH, error=str(e))
        raise CliConfigError(f"Failed to load CLI config: {e}")

def _get_binary_path(cmd_list: List[str]) -> str:
    """
    Извлекает путь к бинарному файлу из списка команд.
    
    Args:
        cmd_list: Список команд из конфигурации
        
    Returns:
        str: Путь к бинарному файлу
    """
    if not cmd_list:
        raise CliConfigError("Empty command list")
    
    # Первый элемент списка команд - это путь к бинарному файлу
    binary_name = cmd_list[0]
    
    # Если это абсолютный путь, возвращаем его как есть
    if binary_name.startswith('/'):
        return binary_name
    
    # Иначе ищем в PATH
    binary_path = subprocess.run(
        ['which', binary_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if binary_path.returncode != 0:
        raise CliBinaryNotFoundError(f"Binary not found in PATH: {binary_name}")
    
    return binary_path.stdout.strip()

def validate_cli_paths() -> Dict[str, Dict[str, Any]]:
    """
    Валидирует пути к CLI бинарным файлам для всех провайдеров.
    
    Returns:
        Dict[str, Dict[str, Any]]: Результаты валидации для каждого провайдера
        
    Raises:
        CliConfigError: При ошибке загрузки конфигурации
    """
    logger.info("cli_path_validation_start", component="health")
    
    # Загружаем конфигурацию
    config = _load_cli_config()
    
    results = {}
    
    # Проверяем каждый провайдер
    for provider_name, provider_config in config.items():
        try:
            # Проверяем, что конфигурация провайдера корректна
            if not isinstance(provider_config, dict):
                raise CliConfigError(f"Invalid provider config for {provider_name}")
            
            if 'cmd' not in provider_config:
                raise CliConfigError(f"Missing 'cmd' in provider config for {provider_name}")
            
            cmd_list = provider_config['cmd']
            if not isinstance(cmd_list, list) or len(cmd_list) == 0:
                raise CliConfigError(f"Invalid 'cmd' format for {provider_name}")
            
            # Получаем путь к бинарному файлу
            binary_path = _get_binary_path(cmd_list)
            
            # Проверяем существование файла
            if not os.path.exists(binary_path):
                raise CliBinaryNotFoundError(f"Binary file does not exist: {binary_path}")
            
            # Проверяем права доступа на выполнение
            if not os.access(binary_path, os.X_OK):
                raise CliPermissionError(f"Binary file is not executable: {binary_path}")
            
            # Получаем версию бинарного файла, если возможно
            version = _get_binary_version(binary_path, cmd_list)
            
            # Сохраняем результаты
            results[provider_name] = {
                "status": "ok",
                "path": binary_path,
                "version": version
            }

            # Выполняем login probe в зависимости от провайдера
            logged_in = False
            probe_command_executed = ""

            if provider_name.startswith("anthropic_"):
                probe_command = [binary_path, "whoami"]
                logged_in = _run_login_probe(provider_name, probe_command)
                probe_command_executed = " ".join(probe_command)
            elif provider_name.startswith("gemini_"):
                # gemini: не использовать auth status. Последовательно пробовать: gemini status || gemini whoami || gemini --version; при отсутствии — mini-run «echo ok» через gemini generate в строгом JSON.
                probe_commands = [
                    [binary_path, "status"],
                    [binary_path, "whoami"],
                    [binary_path, "--version"]
                ]
                for cmd in probe_commands:
                    logged_in = _run_login_probe(provider_name, cmd)
                    if logged_in:
                        probe_command_executed = " ".join(cmd)
                        break
                if not logged_in:
                    # mini-run "echo ok" through gemini generate in strict JSON
                    try:
                        mini_run_cmd = [binary_path, "generate", "-y", "--quiet"]
                        mini_run_input = '{"messages": [{"role": "user", "content": "echo ok"}]}'
                        mini_run_result = subprocess.run(
                            mini_run_cmd,
                            input=mini_run_input,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=15
                        )
                        logged_in = mini_run_result.returncode == 0
                        probe_command_executed = " ".join(mini_run_cmd) + " (mini-run)"
                        if not logged_in:
                            logger.warning(
                                "cli_gemini_mini_run_failed",
                                component="health",
                                provider=provider_name,
                                stderr=mini_run_result.stderr.strip()
                            )
                    except Exception as mini_run_e:
                        logger.error(
                            "cli_gemini_mini_run_error",
                            component="health",
                            provider=provider_name,
                            error=str(mini_run_e)
                        )
            elif provider_name.startswith("qwen_"):
                # qwen: не использовать auth status. Пробовать: qwen whoami || qwen account || qwen --version; при отсутствии — mini-run «echo ok» через основной сабкоманд (см. llm_cli.yaml).
                probe_commands = [
                    [binary_path, "whoami"],
                    [binary_path, "account"],
                    [binary_path, "--version"]
                ]
                for cmd in probe_commands:
                    logged_in = _run_login_probe(provider_name, cmd)
                    if logged_in:
                        probe_command_executed = " ".join(cmd)
                        break
                if not logged_in:
                    # mini-run "echo ok" through main subcommand
                    try:
                        mini_run_cmd = [binary_path, "run", "-y", "--no-color", "--quiet"]
                        mini_run_input = 'echo ok'
                        mini_run_result = subprocess.run(
                            mini_run_cmd,
                            input=mini_run_input,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=15
                        )
                        logged_in = mini_run_result.returncode == 0
                        probe_command_executed = " ".join(mini_run_cmd) + " (mini-run)"
                        if not logged_in:
                            logger.warning(
                                "cli_qwen_mini_run_failed",
                                component="health",
                                provider=provider_name,
                                stderr=mini_run_result.stderr.strip()
                            )
                    except Exception as mini_run_e:
                        logger.error(
                            "cli_qwen_mini_run_error",
                            component="health",
                            provider=provider_name,
                            error=str(mini_run_e)
                        )
            elif provider_name == "openai_gpt5_via_codex":
                # codex: CI=1 /opt/feature-factory/bin/codex status ИЛИ --version; если rc!=0, выполнить мини-run через stdin JSON (без записи артефактов).
                codex_env = os.environ.copy()
                codex_env["CI"] = "1"
                probe_commands = [
                    [binary_path, "status"],
                    [binary_path, "--version"]
                ]
                for cmd in probe_commands:
                    logged_in = _run_login_probe(provider_name, cmd, env=codex_env)
                    if logged_in:
                        probe_command_executed = " ".join(cmd)
                        break
                if not logged_in:
                    # mini-run
                    try:
                        mini_run_cmd = [binary_path, "run"]
                        mini_run_input = '{"messages": [{"role": "user", "content": "echo ok"}]}'
                        mini_run_result = subprocess.run(
                            mini_run_cmd,
                            input=mini_run_input,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=15,
                            env=codex_env
                        )
                        logged_in = mini_run_result.returncode == 0
                        probe_command_executed = " ".join(mini_run_cmd) + " (mini-run)"
                        if not logged_in:
                            logger.warning(
                                "cli_codex_mini_run_failed",
                                component="health",
                                provider=provider_name,
                                stderr=mini_run_result.stderr.strip()
                            )
                    except Exception as mini_run_e:
                        logger.error(
                            "cli_codex_mini_run_error",
                            component="health",
                            provider=provider_name,
                            error=str(mini_run_e)
                        )
            
            results[provider_name]["logged_in"] = logged_in
            results[provider_name]["probe_command"] = probe_command_executed
            
            logger.info(
                "cli_provider_validated",
                component="health",
                provider=provider_name,
                path=binary_path,
                version=version
            )
            
        except CliPathError as e:
            results[provider_name] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(
                "cli_provider_validation_failed",
                component="health",
                provider=provider_name,
                error=str(e)
            )
        except Exception as e:
            results[provider_name] = {
                "status": "error",
                "error": f"Unexpected error: {str(e)}"
            }
            logger.error(
                "cli_provider_validation_unexpected_error",
                component="health",
                provider=provider_name,
                error=str(e),
                err_type=type(e).__name__
            )
    
    logger.info("cli_path_validation_complete", component="health", providers=len(results))
    return results

def _get_binary_version(binary_path: str, cmd_list: List[str]) -> Optional[str]:
    """
    Получает версию бинарного файла, запуская его с флагом --version или аналогичным.
    
    Args:
        binary_path: Путь к бинарному файлу
        cmd_list: Список команд из конфигурации
        
    Returns:
        Optional[str]: Версия бинарного файла или None, если не удалось получить
    """
    # Пробуем стандартные флаги для получения версии
    version_flags = ['--version', '-v', 'version']
    
    for flag in version_flags:
        try:
            # Для некоторых провайдеров (например, Python скриптов) не нужно добавлять флаг
            if binary_path.endswith('.py') or 'python' in binary_path.lower():
                cmd = [binary_path] + cmd_list[1:] if len(cmd_list) > 1 else [binary_path]
            else:
                cmd = [binary_path, flag]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Возвращаем первую строку вывода как версию
                version_output = (result.stdout or result.stderr).strip()
                return version_output.split('\n')[0] if version_output else None
        except Exception:
            # Продолжаем пробовать другие флаги
            continue
    
    return None

def _run_login_probe(provider_name: str, probe_cmd: List[str], env: Optional[Dict[str, str]] = None) -> bool:
    """
    Выполняет login probe для провайдера и возвращает статус логина.
    """
    try:
        result = subprocess.run(
            probe_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            env=env
        )
        if result.returncode != 0:
            logger.warning(
                "cli_login_probe_failed",
                component="health",
                provider=provider_name,
                cmd=" ".join(probe_cmd),
                stderr=result.stderr.strip()
            )
        return result.returncode == 0
    except Exception as e:
        logger.error(
            "cli_login_probe_error",
            component="health",
            provider=provider_name,
            cmd=" ".join(probe_cmd),
            error=str(e)
        )
        return False

def get_health_check_result() -> Dict[str, Any]:
    """
    Получает результат health check для CLI зависимостей.
    
    Returns:
        Dict[str, Any]: Результат health check
    """
    try:
        validation_results = validate_cli_paths()
        
        # Подсчитываем количество рабочих провайдеров
        working_providers = sum(1 for result in validation_results.values() if result.get("status") == "ok")
        total_providers = len(validation_results)
        
        # Формируем список провайдеров для ответа
        providers_list = []
        for provider_name, result in validation_results.items():
            display_name = provider_name
            if provider_name == "openai_gpt5_via_codex":
                display_name = "openai (via codex)"

            provider_info = {
                "provider": display_name,
                "status": result["status"]
            }
            
            if result["status"] == "ok":
                provider_info["path"] = result["path"]
                if result.get("version"):
                    provider_info["version"] = result["version"]
            else:
                provider_info["error"] = result["error"]
            
            if "logged_in" in result:
                provider_info["logged_in"] = result["logged_in"]
            if "probe_command" in result:
                provider_info["probe_command"] = result["probe_command"]
            
            providers_list.append(provider_info)
        
        return {
            "status": "ok",
            "component": "llm_cli",
            "providers": providers_list,
            "working_providers": working_providers,
            "total_providers": total_providers
        }
        
    except CliConfigError as e:
        logger.error("cli_health_check_config_error", component="health", error=str(e))
        return {
            "status": "error",
            "component": "llm_cli",
            "error": f"Configuration error: {str(e)}"
        }
    except Exception as e:
        logger.error("cli_health_check_unexpected_error", component="health", error=str(e))
        return {
            "status": "error",
            "component": "llm_cli",
            "error": f"Unexpected error: {str(e)}"
        }

# Функции для интеграции с существующими health check endpoints
def check_cli_dependencies() -> Tuple[bool, str]:
    """
    Проверяет зависимости CLI для интеграции с health check endpoints.
    
    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    try:
        results = validate_cli_paths()
        
        # Проверяем, есть ли ошибки
        errors = [f"{name}: {result['error']}" for name, result in results.items() 
                 if result.get("status") != "ok"]
        
        if errors:
            return False, f"CLI dependency errors: {'; '.join(errors)}"
        
        return True, f"All {len(results)} CLI providers are valid"
        
    except Exception as e:
        return False, f"CLI dependency check failed: {str(e)}"

if __name__ == "__main__":
    # Пример использования
    print("Validating CLI paths...")
    try:
        results = validate_cli_paths()
        for provider, result in results.items():
            if result["status"] == "ok":
                print(f"✓ {provider}: {result['path']}")
                if result.get("version"):
                    print(f"  Version: {result['version']}")
            else:
                print(f"✗ {provider}: {result['error']}")
    except Exception as e:
        print(f"Validation failed: {e}")