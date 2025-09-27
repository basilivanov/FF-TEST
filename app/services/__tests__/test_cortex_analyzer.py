#!/usr/bin/env python3
"""
Тесты для CortexAnalyzer - системы анализа полноты контекста.
"""

import pytest
import tempfile
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from app.services.cortex_analyzer import (
    CortexAnalyzer, FileAnalysis, RoleAnalysis, CortexHealthReport
)


class TestCortexAnalyzer:
    """Тесты для класса CortexAnalyzer"""

    @pytest.fixture
    def temp_dir(self):
        """Создаёт временную директорию для тестов"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def analyzer(self, temp_dir):
        """Создаёт анализатор с тестовой структурой файлов"""
        # Создаём тестовую структуру
        cortex_dir = temp_dir / "cortex"
        cortex_dir.mkdir()

        roles_dir = cortex_dir / "roles"
        roles_dir.mkdir()

        prompts_dir = temp_dir / "app" / "agents" / "prompts"
        prompts_dir.mkdir(parents=True)

        data_dir = temp_dir / "data"
        data_dir.mkdir()

        analyzer = CortexAnalyzer()
        analyzer.base_path = temp_dir
        analyzer.cortex_path = cortex_dir
        analyzer.prompts_path = prompts_dir
        analyzer.data_path = data_dir

        return analyzer

    def test_analyze_file_basic(self, analyzer, temp_dir):
        """Тест базового анализа файла"""
        # Создаём тестовый файл
        test_file = temp_dir / "test.md"
        content = """# Test Document

This is a test document with:
- Lists
- Examples
- Multiple paragraphs

## Section 2
Some more content here.

```python
def example():
    return "code example"
```
"""
        test_file.write_text(content)

        # Анализируем файл
        analysis = analyzer.analyze_file(test_file)

        # Проверяем результат
        assert analysis.path == str(test_file)
        assert analysis.size > 0
        assert analysis.lines > 10
        assert analysis.content_quality > 50  # Хорошо структурированный файл
        assert len(analysis.content_hash) == 16

    def test_analyze_file_empty(self, analyzer, temp_dir):
        """Тест анализа пустого файла"""
        test_file = temp_dir / "empty.md"
        test_file.write_text("")

        analysis = analyzer.analyze_file(test_file)

        assert analysis.content_quality == 0.0
        assert analysis.lines == 0

    def test_analyze_file_low_quality(self, analyzer, temp_dir):
        """Тест анализа файла низкого качества"""
        test_file = temp_dir / "low_quality.md"
        test_file.write_text("TODO: write documentation\nFIXME: this is deprecated")

        analysis = analyzer.analyze_file(test_file)

        assert analysis.content_quality < 50  # Низкое качество из-за TODO/FIXME

    def test_content_quality_assessment(self, analyzer):
        """Тест оценки качества контента"""
        # Высококачественный контент
        high_quality = """# Role: Developer

## Responsibilities
- Write clean code
- Follow best practices
- Use modern patterns like async/await

## Examples
```typescript
async function example() {
    return await someFunction();
}
```

This role focuses on implementation.
"""

        quality = analyzer._assess_content_quality(high_quality, Path("dev.md"))
        assert quality > 80

        # Низкокачественный контент
        low_quality = "TODO"
        quality = analyzer._assess_content_quality(low_quality, Path("todo.md"))
        assert quality < 30

    def test_analyze_role_complete(self, analyzer):
        """Тест анализа роли с полным набором файлов"""
        # Создаём файлы для роли
        cortex_file = analyzer.cortex_path / "roles" / "dev.md"
        cortex_file.parent.mkdir(exist_ok=True)
        cortex_file.write_text("""# Developer Role

## Responsibilities
- Code implementation
- Testing
- Documentation
""")

        prompt_file = analyzer.prompts_path / "dev.md"
        prompt_file.write_text("""# Developer Prompt

You are a skilled developer...

## Context
- Use TypeScript
- Follow async patterns
- Write tests first
""")

        # Анализируем роль
        analysis = analyzer.analyze_role("dev")

        assert analysis.role == "dev"
        assert len(analysis.cortex_files) == 1
        assert len(analysis.prompt_files) == 1
        assert analysis.doc_coverage > 50
        assert analysis.context_completeness > 0
        assert analysis.overall_score > 0

    def test_analyze_role_missing_files(self, analyzer):
        """Тест анализа роли с отсутствующими файлами"""
        analysis = analyzer.analyze_role("nonexistent")

        assert analysis.role == "nonexistent"
        assert len(analysis.cortex_files) == 0
        assert len(analysis.prompt_files) == 0
        assert "Missing cortex definition" in analysis.issues
        assert "Missing prompts" in analysis.issues
        assert analysis.overall_score < 50

    def test_doc_coverage_calculation(self, analyzer):
        """Тест расчёта покрытия документацией"""
        # Создаём файлы с разным качеством
        cortex_files = [
            FileAnalysis("cortex.md", 100, 10, datetime.now(timezone.utc), "hash1", 80.0)
        ]
        prompt_files = [
            FileAnalysis("prompt.md", 200, 20, datetime.now(timezone.utc), "hash2", 90.0)
        ]

        coverage = analyzer._calculate_doc_coverage("test", cortex_files, prompt_files)

        assert coverage > 80  # Должно быть высокое покрытие
        assert coverage <= 100

        # Тест без файлов
        coverage = analyzer._calculate_doc_coverage("test", [], [])
        assert coverage == 0

    def test_context_completeness_calculation(self, analyzer):
        """Тест расчёта полноты контекста"""
        files = [
            FileAnalysis("file1.md", 100, 50, datetime.now(timezone.utc), "hash1", 80.0),
            FileAnalysis("file2.md", 200, 30, datetime.now(timezone.utc), "hash2", 70.0)
        ]

        completeness = analyzer._calculate_context_completeness(files, [])

        assert completeness > 0
        assert completeness <= 100

        # Тест без файлов
        completeness = analyzer._calculate_context_completeness([], [])
        assert completeness == 0

    def test_content_freshness_calculation(self, analyzer):
        """Тест расчёта свежести контента"""
        now = datetime.now(timezone.utc)

        # Свежие файлы (< 7 дней)
        fresh_files = [
            FileAnalysis("fresh.md", 100, 10, now, "hash1", 80.0)
        ]
        freshness = analyzer._calculate_content_freshness(fresh_files)
        assert freshness == 100.0

        # Старые файлы (> 90 дней)
        from datetime import timedelta
        old_date = now - timedelta(days=100)
        old_files = [
            FileAnalysis("old.md", 100, 10, old_date, "hash2", 80.0)
        ]
        freshness = analyzer._calculate_content_freshness(old_files)
        assert freshness < 50

    def test_issue_identification(self, analyzer):
        """Тест выявления проблем"""
        # Роль без файлов
        issues = analyzer._identify_issues("test", [], [], 30.0)

        assert "Missing cortex definition for test" in issues
        assert "Missing prompts for test" in issues
        assert "Below acceptable quality threshold" in issues

        # Роль с низким качеством
        low_quality_files = [
            FileAnalysis("low.md", 100, 10, datetime.now(timezone.utc), "hash1", 30.0)
        ]
        issues = analyzer._identify_issues("test", low_quality_files, [], 40.0)

        assert "Low content quality" in issues

    def test_system_coverage_analysis(self, analyzer):
        """Тест анализа системного покрытия"""
        # Создаём тестовые категории
        for category in ["api", "core"]:
            cat_dir = analyzer.cortex_path / category
            cat_dir.mkdir()
            (cat_dir / f"{category}.md").write_text(f"# {category.upper()}\nDocumentation")

        coverage = analyzer.analyze_system_coverage()

        assert "api" in coverage
        assert "core" in coverage
        assert coverage["api"] > 0
        assert coverage["core"] > 0

    def test_recommendations_generation(self, analyzer):
        """Тест генерации рекомендаций"""
        # Создаём анализ с проблемами
        poor_role = RoleAnalysis(
            role="poor",
            cortex_files=[],
            prompt_files=[],
            doc_coverage=30.0,
            context_completeness=40.0,
            content_freshness=20.0,
            overall_score=30.0,
            issues=[]
        )

        system_coverage = {"api": 20.0, "core": 80.0}

        recommendations = analyzer.generate_recommendations([poor_role], system_coverage)

        assert any("Improve documentation for poor" in r for r in recommendations)
        assert any("Update outdated content for poor" in r for r in recommendations)
        assert any("api" in r for r in recommendations)

    def test_run_analysis_integration(self, analyzer):
        """Интеграционный тест полного анализа"""
        # Создаём минимальную структуру
        analyzer.roles = ["test_role"]  # Ограничиваем для теста

        cortex_file = analyzer.cortex_path / "roles" / "test_role.md"
        cortex_file.parent.mkdir(exist_ok=True)
        cortex_file.write_text("# Test Role\nBasic documentation")

        # Запускаем анализ
        report = analyzer.run_analysis()

        assert isinstance(report, CortexHealthReport)
        assert len(report.roles) == 1
        assert report.roles[0].role == "test_role"
        assert 0 <= report.overall_score <= 100
        assert isinstance(report.system_coverage, dict)
        assert isinstance(report.recommendations, list)

    def test_save_report(self, analyzer, temp_dir):
        """Тест сохранения отчёта в БД"""
        db_path = str(temp_dir / "test.db")

        # Создаём тестовый отчёт
        role_analysis = RoleAnalysis(
            role="test",
            cortex_files=[],
            prompt_files=[],
            doc_coverage=75.0,
            context_completeness=80.0,
            content_freshness=85.0,
            overall_score=80.0,
            issues=[]
        )

        report = CortexHealthReport(
            timestamp=datetime.now(timezone.utc),
            overall_score=80.0,
            roles=[role_analysis],
            system_coverage={"api": 75.0},
            recommendations=["Test recommendation"]
        )

        # Сохраняем отчёт
        analyzer.save_report(report, db_path)

        # Проверяем что данные сохранились
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем основной отчёт
        cursor.execute("SELECT * FROM cortex_reports")
        reports = cursor.fetchall()
        assert len(reports) == 1
        assert reports[0][2] == 80.0  # overall_score

        # Проверяем метрики ролей
        cursor.execute("SELECT * FROM role_metrics")
        metrics = cursor.fetchall()
        assert len(metrics) == 1
        assert metrics[0][2] == "test"  # role
        assert metrics[0][6] == 80.0  # overall_score

        conn.close()

    def test_error_handling(self, analyzer):
        """Тест обработки ошибок"""
        # Анализ несуществующего файла
        analysis = analyzer.analyze_file(Path("/nonexistent/file.md"))

        assert analysis.content_quality == 0.0
        assert analysis.content_hash == "error"

    @patch('app.services.cortex_analyzer._log')
    def test_logging(self, mock_log, analyzer):
        """Тест логирования"""
        analyzer.roles = ["test"]
        analyzer.run_analysis(analysis_id='test-id')

        mock_log.assert_called()


class TestFileAnalysis:
    """Тесты для класса FileAnalysis"""

    def test_file_analysis_creation(self):
        """Тест создания FileAnalysis"""
        analysis = FileAnalysis(
            path="/test/file.md",
            size=100,
            lines=10,
            last_modified=datetime.now(timezone.utc),
            content_hash="abc123",
            content_quality=75.5
        )

        assert analysis.path == "/test/file.md"
        assert analysis.size == 100
        assert analysis.lines == 10
        assert analysis.content_quality == 75.5


class TestRoleAnalysis:
    """Тесты для класса RoleAnalysis"""

    def test_role_analysis_creation(self):
        """Тест создания RoleAnalysis"""
        analysis = RoleAnalysis(
            role="dev",
            cortex_files=[],
            prompt_files=[],
            doc_coverage=80.0,
            context_completeness=75.0,
            content_freshness=90.0,
            overall_score=81.7,
            issues=["Test issue"]
        )

        assert analysis.role == "dev"
        assert analysis.overall_score == 81.7
        assert "Test issue" in analysis.issues


if __name__ == "__main__":
    pytest.main([__file__, "-v"])