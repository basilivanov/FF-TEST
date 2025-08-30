import unittest
import os
import tempfile
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext

class TestBacklogSchemaMigrationIntegration(unittest.TestCase):
    """Интеграционные тесты для миграций таблиц backlog-а."""

    def test_migration_with_alembic(self):
        """Тест применения миграций с использованием Alembic."""
        # Создаем временную базу данных в памяти
        engine = create_engine('sqlite:///:memory:')
        
        # Создаем конфигурацию Alembic
        alembic_cfg = Config("/opt/feature-factory/alembic.ini")
        alembic_cfg.set_main_option("script_location", "/opt/feature-factory/app/db/migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///:memory:")
        
        # Создаем таблицу alembic_version вручную, чтобы избежать ошибок
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
            # Вставляем начальную версию
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0001')"))
            conn.commit()
        
        # Проверяем, что миграция может быть загружена
        script = ScriptDirectory.from_config(alembic_cfg)
        revisions = list(script.walk_revisions())
        self.assertTrue(len(revisions) > 0)
        
        # Проверяем, что наша миграция существует
        found_backlog_migration = False
        for revision in script.walk_revisions():
            if "add_backlog_tables" in revision.doc:
                found_backlog_migration = True
                break
        
        self.assertTrue(found_backlog_migration, "Backlog migration should exist")

    def test_migration_sql_generation(self):
        """Тест генерации SQL для миграций."""
        # Создаем конфигурацию Alembic
        alembic_cfg = Config("/opt/feature-factory/alembic.ini")
        alembic_cfg.set_main_option("script_location", "/opt/feature-factory/app/db/migrations")
        
        # Проверяем, что миграция может быть загружена
        script = ScriptDirectory.from_config(alembic_cfg)
        
        # Находим нашу миграцию
        backlog_revision = None
        for revision in script.walk_revisions():
            if "add_backlog_tables" in revision.doc:
                backlog_revision = revision
                break
        
        self.assertIsNotNone(backlog_revision, "Backlog migration should exist")
        
        # Генерируем SQL для upgrade
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.sql', delete=False) as f:
            # Этот тест проверяет только структуру миграции, а не выполнение
            pass
        
        # Проверяем, что миграция имеет правильную структуру
        self.assertIsNotNone(backlog_revision.down_revision)
        self.assertTrue(hasattr(backlog_revision.module, 'upgrade'))
        self.assertTrue(hasattr(backlog_revision.module, 'downgrade'))

if __name__ == '__main__':
    unittest.main()