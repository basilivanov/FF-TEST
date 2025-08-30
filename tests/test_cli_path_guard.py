#!/usr/bin/env python3
"""
Тесты для модуля cli_path_guard.py
"""

import unittest
import os
import tempfile
import yaml
import subprocess
from unittest.mock import patch, MagicMock
from app.llm.cli_path_guard import (
    validate_cli_paths, 
    get_health_check_result, 
    check_cli_dependencies,
    _load_cli_config,
    _get_binary_path,
    CliConfigError,
    CliBinaryNotFoundError,
    CliPermissionError
)

class TestCliPathGuard(unittest.TestCase):
    """Тесты для модуля cli_path_guard.py"""

    def setUp(self):
        """Подготовка к тестам."""
        # Создаем временный файл конфигурации
        self.temp_config_fd, self.temp_config_path = tempfile.mkstemp(suffix='.yaml')
        self.original_config_path = "/opt/feature-factory/configs/llm_cli.yaml"
        
        # Заменяем путь к конфигурации на временный
        import app.llm.cli_path_guard
        app.llm.cli_path_guard.CLI_CONFIG_PATH = self.temp_config_path

    def tearDown(self):
        """Очистка после тестов."""
        # Восстанавливаем оригинальный путь к конфигурации
        import app.llm.cli_path_guard
        app.llm.cli_path_guard.CLI_CONFIG_PATH = self.original_config_path
        
        # Закрываем и удаляем временный файл
        os.close(self.temp_config_fd)
        if os.path.exists(self.temp_config_path):
            os.unlink(self.temp_config_path)

    def test_load_cli_config_success(self):
        """Тест успешной загрузки конфигурации CLI."""
        # Создаем тестовую конфигурацию
        test_config = {
            "qwen": {
                "cmd": ["qwen", "--model", "qwen3-coder:14b", "--no-interactive", "-p"],
                "env": ["QWEN_API_KEY"],
                "expects": "json"
            }
        }
        
        # Записываем конфигурацию в временный файл
        with open(self.temp_config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Проверяем загрузку конфигурации
        config = _load_cli_config()
        self.assertEqual(config, test_config)

    def test_load_cli_config_file_not_found(self):
        """Тест ошибки при отсутствии файла конфигурации."""
        # Удаляем временный файл
        os.unlink(self.temp_config_path)
        
        # Проверяем, что возникает ошибка
        with self.assertRaises(CliConfigError):
            _load_cli_config()

    def test_load_cli_config_invalid_yaml(self):
        """Тест ошибки при невалидном YAML."""
        # Создаем файл с невалидным YAML
        with open(self.temp_config_path, 'w') as f:
            f.write("invalid: yaml: [")
        
        # Проверяем, что возникает ошибка
        with self.assertRaises(CliConfigError):
            _load_cli_config()

    @patch('subprocess.run')
    def test_get_binary_path_absolute(self, mock_run):
        """Тест получения пути к бинарному файлу по абсолютному пути."""
        # Создаем тестовую команду с абсолютным путем
        cmd_list = ["/usr/local/bin/qwen", "--model", "test"]
        
        # Проверяем, что возвращается абсолютный путь
        binary_path = _get_binary_path(cmd_list)
        self.assertEqual(binary_path, "/usr/local/bin/qwen")

    @patch('subprocess.run')
    def test_get_binary_path_relative_success(self, mock_run):
        """Тест успешного получения пути к бинарному файлу по относительному пути."""
        # Настраиваем mock для subprocess.run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "/usr/local/bin/qwen\n"
        mock_run.return_value = mock_result
        
        # Создаем тестовую команду с относительным путем
        cmd_list = ["qwen", "--model", "test"]
        
        # Проверяем, что возвращается путь из which
        binary_path = _get_binary_path(cmd_list)
        self.assertEqual(binary_path, "/usr/local/bin/qwen")
        mock_run.assert_called_once_with(
            ['which', 'qwen'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    @patch('subprocess.run')
    def test_get_binary_path_relative_not_found(self, mock_run):
        """Тест ошибки при не найденном бинарном файле по относительному пути."""
        # Настраиваем mock для subprocess.run
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        # Создаем тестовую команду с относительным путем
        cmd_list = ["nonexistent_binary", "--model", "test"]
        
        # Проверяем, что возникает ошибка
        with self.assertRaises(CliBinaryNotFoundError):
            _get_binary_path(cmd_list)

    @patch('os.path.exists')
    @patch('os.access')
    @patch('app.llm.cli_path_guard._get_binary_path')
    @patch('app.llm.cli_path_guard._load_cli_config')
    def test_validate_cli_paths_success(self, mock_load_config, mock_get_binary_path, mock_access, mock_exists):
        """Тест успешной валидации путей CLI."""
        # Настраиваем mocks
        mock_load_config.return_value = {
            "qwen": {
                "cmd": ["qwen", "--model", "qwen3-coder:14b", "--no-interactive", "-p"],
                "env": ["QWEN_API_KEY"],
                "expects": "json"
            }
        }
        mock_get_binary_path.return_value = "/usr/local/bin/qwen"
        mock_exists.return_value = True
        mock_access.return_value = True
        
        # Проверяем валидацию
        results = validate_cli_paths()
        
        # Проверяем результаты
        self.assertIn("qwen", results)
        self.assertEqual(results["qwen"]["status"], "ok")
        self.assertEqual(results["qwen"]["path"], "/usr/local/bin/qwen")

    @patch('app.llm.cli_path_guard._load_cli_config')
    def test_validate_cli_paths_config_error(self, mock_load_config):
        """Тест ошибки конфигурации при валидации путей CLI."""
        # Настраиваем mock для ошибки загрузки конфигурации
        mock_load_config.side_effect = CliConfigError("Config error")
        
        # Проверяем, что возникает ошибка
        with self.assertRaises(CliConfigError):
            validate_cli_paths()

    @patch('os.path.exists')
    @patch('app.llm.cli_path_guard._get_binary_path')
    @patch('app.llm.cli_path_guard._load_cli_config')
    def test_validate_cli_paths_binary_not_found(self, mock_load_config, mock_get_binary_path, mock_exists):
        """Тест ошибки при отсутствии бинарного файла."""
        # Настраиваем mocks
        mock_load_config.return_value = {
            "qwen": {
                "cmd": ["qwen", "--model", "qwen3-coder:14b", "--no-interactive", "-p"],
                "env": ["QWEN_API_KEY"],
                "expects": "json"
            }
        }
        mock_get_binary_path.return_value = "/usr/local/bin/qwen"
        mock_exists.return_value = False
        
        # Проверяем валидацию
        results = validate_cli_paths()
        
        # Проверяем результаты
        self.assertIn("qwen", results)
        self.assertEqual(results["qwen"]["status"], "error")
        self.assertIn("Binary file does not exist", results["qwen"]["error"])

    @patch('os.access')
    @patch('os.path.exists')
    @patch('app.llm.cli_path_guard._get_binary_path')
    @patch('app.llm.cli_path_guard._load_cli_config')
    def test_validate_cli_paths_permission_error(self, mock_load_config, mock_get_binary_path, mock_exists, mock_access):
        """Тест ошибки прав доступа к бинарному файлу."""
        # Настраиваем mocks
        mock_load_config.return_value = {
            "qwen": {
                "cmd": ["qwen", "--model", "qwen3-coder:14b", "--no-interactive", "-p"],
                "env": ["QWEN_API_KEY"],
                "expects": "json"
            }
        }
        mock_get_binary_path.return_value = "/usr/local/bin/qwen"
        mock_exists.return_value = True
        mock_access.return_value = False  # Нет прав на выполнение
        
        # Проверяем валидацию
        results = validate_cli_paths()
        
        # Проверяем результаты
        self.assertIn("qwen", results)
        self.assertEqual(results["qwen"]["status"], "error")
        self.assertIn("Binary file is not executable", results["qwen"]["error"])

    @patch('app.llm.cli_path_guard.validate_cli_paths')
    def test_get_health_check_result_success(self, mock_validate):
        """Тест успешного получения результата health check."""
        # Настраиваем mock
        mock_validate.return_value = {
            "qwen": {
                "status": "ok",
                "path": "/usr/local/bin/qwen",
                "version": "qwen 1.0.0"
            },
            "stub": {
                "status": "ok",
                "path": "/usr/bin/python3",
                "version": "Python 3.12.3"
            }
        }
        
        # Проверяем получение результата health check
        result = get_health_check_result()
        
        # Проверяем результат
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["component"], "llm_cli")
        self.assertEqual(result["working_providers"], 2)
        self.assertEqual(result["total_providers"], 2)
        self.assertEqual(len(result["providers"]), 2)

    @patch('app.llm.cli_path_guard.validate_cli_paths')
    def test_get_health_check_result_with_errors(self, mock_validate):
        """Тест получения результата health check с ошибками."""
        # Настраиваем mock
        mock_validate.return_value = {
            "qwen": {
                "status": "error",
                "error": "Binary not found"
            },
            "stub": {
                "status": "ok",
                "path": "/usr/bin/python3",
                "version": "Python 3.12.3"
            }
        }
        
        # Проверяем получение результата health check
        result = get_health_check_result()
        
        # Проверяем результат
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["component"], "llm_cli")
        self.assertEqual(result["working_providers"], 1)
        self.assertEqual(result["total_providers"], 2)
        self.assertEqual(len(result["providers"]), 2)

    @patch('app.llm.cli_path_guard.validate_cli_paths')
    def test_get_health_check_result_config_error(self, mock_validate):
        """Тест ошибки конфигурации при получении результата health check."""
        # Настраиваем mock для ошибки
        mock_validate.side_effect = CliConfigError("Config error")
        
        # Проверяем получение результата health check
        result = get_health_check_result()
        
        # Проверяем результат
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["component"], "llm_cli")
        self.assertIn("Configuration error", result["error"])

    @patch('app.llm.cli_path_guard.validate_cli_paths')
    def test_check_cli_dependencies_success(self, mock_validate):
        """Тест успешной проверки CLI зависимостей."""
        # Настраиваем mock
        mock_validate.return_value = {
            "qwen": {
                "status": "ok",
                "path": "/usr/local/bin/qwen"
            }
        }
        
        # Проверяем проверку зависимостей
        success, message = check_cli_dependencies()
        
        # Проверяем результат
        self.assertTrue(success)
        self.assertIn("CLI providers are valid", message)

    @patch('app.llm.cli_path_guard.validate_cli_paths')
    def test_check_cli_dependencies_with_errors(self, mock_validate):
        """Тест проверки CLI зависимостей с ошибками."""
        # Настраиваем mock
        mock_validate.return_value = {
            "qwen": {
                "status": "error",
                "error": "Binary not found"
            }
        }
        
        # Проверяем проверку зависимостей
        success, message = check_cli_dependencies()
        
        # Проверяем результат
        self.assertFalse(success)
        self.assertIn("CLI dependency errors", message)

if __name__ == '__main__':
    unittest.main()