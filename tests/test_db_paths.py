import unittest
import os
import re


class TestDBPaths(unittest.TestCase):
    """Тесты для аудита путей к БД."""

    def test_no_sqlite_relative_or_memory_paths(self):
        """Fail, если найдены строки вида sqlite:///./ или :memory:."""
        # Рекурсивно пройдемся по всем .py файлам в app/
        app_dir = "/opt/feature-factory/app"
        
        # Паттерны для поиска
        relative_path_pattern = re.compile(r'sqlite:///\.')
        memory_pattern = re.compile(r':memory:')
        
        # Список файлов, где найдены запрещенные паттерны
        files_with_relative_paths = []
        files_with_memory_paths = []
        
        for root, dirs, files in os.walk(app_dir):
            # Исключаем __pycache__ и другие служебные директории
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Проверяем паттерны
                            if relative_path_pattern.search(content):
                                files_with_relative_paths.append(file_path)
                            if memory_pattern.search(content):
                                files_with_memory_paths.append(file_path)
                    except Exception as e:
                        # Пропускаем файлы, которые не удалось прочитать
                        print(f"Warning: Could not read {file_path}: {e}")
        
        # Формируем сообщения об ошибках
        error_messages = []
        if files_with_relative_paths:
            error_messages.append(
                f"Found sqlite relative paths (sqlite:///./) in files: {', '.join(files_with_relative_paths)}"
            )
        if files_with_memory_paths:
            error_messages.append(
                f"Found :memory: paths in files: {', '.join(files_with_memory_paths)}"
            )
        
        # Если есть ошибки, тест падает
        if error_messages:
            self.fail("; ".join(error_messages))
    
    def test_app_and_index_read_different_urls(self):
        """Проверка, что app и index читают разные URL по ключам ENV."""
        # Импортируем функции для получения DATABASE_URL
        from app.db.guard import get_db_connection_string as get_app_db_url
        from app.index.api import get_db_connection_string as get_index_db_url
        
        # Получаем URL для app и index
        app_db_url = get_app_db_url()
        index_db_url = get_index_db_url()
        
        # Проверяем, что они разные
        self.assertNotEqual(
            app_db_url, index_db_url,
            f"App and index read the same DATABASE_URL: {app_db_url}"
        )
        
        # Проверяем, что оба URL абсолютные (начинаются с sqlite:////)
        self.assertTrue(
            app_db_url.startswith("sqlite:////"),
            f"App DATABASE_URL is not absolute: {app_db_url}"
        )
        self.assertTrue(
            index_db_url.startswith("sqlite:////"),
            f"Index DATABASE_URL is not absolute: {index_db_url}"
        )


if __name__ == '__main__':
    unittest.main()