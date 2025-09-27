#!/usr/bin/env python3
"""
Cortex Analysis Service - анализ полноты контекста и документированности системы.
Запускается каждый час для оценки здоровья кортекса.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import sqlite3

from app.logging_helpers import log, get_env, generate_correlation_id


def _log(level: str, event: str, analysis_id: str, task_id: Optional[str] = None, **kv: Any) -> None:
    getattr(log, level)(
        event=event,
        env=get_env(),
        component="cortex_analyzer",
        agent_role="Cortex",
        run_id=analysis_id,
        task_id=task_id or analysis_id,
        correlation_id=analysis_id,
        kv=kv,
    )


@dataclass
class FileAnalysis:
    path: str
    size: int
    lines: int
    last_modified: datetime
    content_hash: str
    content_quality: float  # 0-100%

@dataclass
class RoleAnalysis:
    role: str
    cortex_files: List[FileAnalysis]
    prompt_files: List[FileAnalysis]
    doc_coverage: float  # 0-100%
    context_completeness: float  # 0-100%
    content_freshness: float  # 0-100%
    overall_score: float  # 0-100%
    issues: List[str]

@dataclass
class CortexHealthReport:
    timestamp: datetime
    overall_score: float
    roles: List[RoleAnalysis]
    system_coverage: Dict[str, float]
    recommendations: List[str]

class CortexAnalyzer:
    """Анализатор полноты и качества кортекса"""

    def __init__(self):
        self.base_path = Path("/opt/feature-factory")
        self.cortex_path = self.base_path / "cortex"
        self.prompts_path = self.base_path / "app" / "agents" / "prompts"
        self.docs_path = self.base_path / "docs"
        self.data_path = self.base_path / "data"

        # Роли системы
        self.roles = ["architect", "dev", "qa", "scribe", "maintainer"]

        # Ожидаемые категории документации
        self.expected_categories = [
            "api", "core", "db", "contracts", "patterns",
            "policies", "reference", "security", "stack"
        ]

    def analyze_file(self, file_path: Path, analysis_id: Optional[str] = None) -> FileAnalysis:
        """Анализирует отдельный файл"""
        analysis_id = analysis_id or generate_correlation_id()
        try:
            stat = file_path.stat()
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Базовые метрики
            size = stat.st_size
            lines = len(content.splitlines())
            last_modified = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            # Оценка качества контента
            quality = self._assess_content_quality(content, file_path)

            return FileAnalysis(
                path=str(file_path),
                size=size,
                lines=lines,
                last_modified=last_modified,
                content_hash=content_hash,
                content_quality=quality
            )
        except Exception as e:
            _log("error", "cortex_file_analysis_failed", analysis_id, path=str(file_path), err_type=type(e).__name__, err_msg=str(e))
            return FileAnalysis(
                path=str(file_path),
                size=0,
                lines=0,
                last_modified=datetime.now(timezone.utc),
                content_hash="error",
                content_quality=0.0
            )

    def _assess_content_quality(self, content: str, file_path: Path) -> float:
        """Оценивает качество содержимого файла"""
        if not content.strip():
            return 0.0

        score = 0.0
        factors = 0

        # 1. Длина контента (20%)
        if len(content) > 100:
            score += min(20, len(content) / 50)  # 1 балл за каждые 50 символов, макс 20
        factors += 20

        # 2. Структурированность (30%)
        structure_score = 0
        if "##" in content or "###" in content:  # Заголовки
            structure_score += 10
        if "```" in content:  # Примеры кода
            structure_score += 10
        if "- " in content or "* " in content:  # Списки
            structure_score += 5
        if content.count('\n\n') > 2:  # Абзацы
            structure_score += 5
        score += min(30, structure_score)
        factors += 30

        # 3. Специфичность для типа файла (25%)
        file_score = 0
        if file_path.name.endswith('.md'):
            # Для markdown проверяем наличие ключевых элементов
            if "# " in content:  # Главный заголовок
                file_score += 10
            if "context" in content.lower() or "инструкция" in content.lower():
                file_score += 10
            if "пример" in content.lower() or "example" in content.lower():
                file_score += 5
        score += min(25, file_score)
        factors += 25

        # 4. Актуальность (25%)
        # Проверяем наличие современных паттернов и отсутствие устаревших
        freshness_score = 25  # Начинаем с полного балла
        outdated_patterns = ["TODO", "FIXME", "deprecated", "устарел"]
        for pattern in outdated_patterns:
            if pattern.lower() in content.lower():
                freshness_score -= 5
        modern_patterns = ["typescript", "fastapi", "async", "await"]
        for pattern in modern_patterns:
            if pattern.lower() in content.lower():
                freshness_score += 2

        score += max(0, min(25, freshness_score))
        factors += 25

        return min(100.0, (score / factors) * 100)

    def analyze_role(self, role: str, analysis_id: Optional[str] = None) -> RoleAnalysis:
        """Анализирует документацию для конкретной роли"""

        analysis_id = analysis_id or generate_correlation_id()
        task_id = f"role-{role}"
        _log("info", "cortex_role_analysis_started", analysis_id, task_id=task_id, role=role)

        cortex_files = []
        role_cortex_file = self.cortex_path / "roles" / f"{role}.md"
        if role_cortex_file.exists():
            cortex_files.append(self.analyze_file(role_cortex_file, analysis_id=analysis_id))

        prompt_files = []
        for prompt_file in self.prompts_path.glob(f"{role}*.md"):
            prompt_files.append(self.analyze_file(prompt_file, analysis_id=analysis_id))

        doc_coverage = self._calculate_doc_coverage(role, cortex_files, prompt_files)
        context_completeness = self._calculate_context_completeness(cortex_files, prompt_files)
        content_freshness = self._calculate_content_freshness(cortex_files + prompt_files)

        overall_score = (doc_coverage * 0.4 + context_completeness * 0.4 + content_freshness * 0.2)
        issues = self._identify_issues(role, cortex_files, prompt_files, overall_score)

        _log("info", "cortex_role_analysis_completed", analysis_id, task_id=task_id, role=role, overall_score=overall_score, issues=len(issues))

        return RoleAnalysis(
            role=role,
            cortex_files=cortex_files,
            prompt_files=prompt_files,
            doc_coverage=doc_coverage,
            context_completeness=context_completeness,
            content_freshness=content_freshness,
            overall_score=overall_score,
            issues=issues
        )

    def _calculate_doc_coverage(self, role: str, cortex_files: List[FileAnalysis], prompt_files: List[FileAnalysis]) -> float:
        """Вычисляет покрытие документацией"""
        score = 0.0

        # Наличие основных файлов (60%)
        if cortex_files:
            score += 30  # Есть описание роли в кортексе
        if prompt_files:
            score += 30  # Есть промпты для роли

        # Качество документации (40%)
        all_files = cortex_files + prompt_files
        if all_files:
            avg_quality = sum(f.content_quality for f in all_files) / len(all_files)
            score += (avg_quality * 0.4)

        return min(100.0, score)

    def _calculate_context_completeness(self, cortex_files: List[FileAnalysis], prompt_files: List[FileAnalysis]) -> float:
        """Вычисляет полноту контекста"""
        all_files = cortex_files + prompt_files
        if not all_files:
            return 0.0

        # Базовая полнота по объёму
        total_lines = sum(f.lines for f in all_files)
        volume_score = min(50, total_lines / 10)  # 1 балл за каждые 10 строк, макс 50

        # Разнообразие контента
        total_files = len(all_files)
        diversity_score = min(30, total_files * 10)  # 10 баллов за файл, макс 30

        # Средняя качество контента
        avg_quality = sum(f.content_quality for f in all_files) / len(all_files)
        quality_score = avg_quality * 0.2  # 20% от среднего качества

        return volume_score + diversity_score + quality_score

    def _calculate_content_freshness(self, files: List[FileAnalysis]) -> float:
        """Вычисляет свежесть контента"""
        if not files:
            return 0.0

        now = datetime.now(timezone.utc)
        total_score = 0.0

        for file in files:
            # Возраст файла в днях
            age_days = (now - file.last_modified).days

            # Штраф за возраст: -1% за каждый день после недели
            if age_days <= 7:
                freshness = 100.0
            elif age_days <= 30:
                freshness = max(80.0, 100.0 - (age_days - 7) * 1)
            elif age_days <= 90:
                freshness = max(50.0, 80.0 - (age_days - 30) * 0.5)
            else:
                freshness = max(20.0, 50.0 - (age_days - 90) * 0.1)

            total_score += freshness

        return total_score / len(files)

    def _identify_issues(self, role: str, cortex_files: List[FileAnalysis],
                        prompt_files: List[FileAnalysis], overall_score: float) -> List[str]:
        """Выявляет проблемы в документации роли"""
        issues = []

        # Критические проблемы
        if not cortex_files:
            issues.append(f"Missing cortex definition for {role}")
        if not prompt_files:
            issues.append(f"Missing prompts for {role}")

        # Проблемы качества
        all_files = cortex_files + prompt_files
        if all_files:
            avg_quality = sum(f.content_quality for f in all_files) / len(all_files)
            if avg_quality < 50:
                issues.append("Low content quality")

            # Проблемы свежести
            old_files = [f for f in all_files if
                        (datetime.now(timezone.utc) - f.last_modified).days > 30]
            if old_files:
                issues.append(f"Outdated files: {len(old_files)}")

        # Общие проблемы
        if overall_score < 70:
            issues.append("Below acceptable quality threshold")

        return issues

    def analyze_system_coverage(self) -> Dict[str, float]:
        """Анализирует покрытие системных компонентов"""
        coverage = {}

        # Проверяем основные категории кортекса
        for category in self.expected_categories:
            category_path = self.cortex_path / category
            if category_path.exists():
                files = list(category_path.glob("*.md"))
                if files:
                    total_quality = sum(self.analyze_file(f).content_quality for f in files)
                    coverage[category] = total_quality / len(files)
                else:
                    coverage[category] = 0.0
            else:
                coverage[category] = 0.0

        return coverage

    def generate_recommendations(self, role_analyses: List[RoleAnalysis],
                                system_coverage: Dict[str, float]) -> List[str]:
        """Генерирует рекомендации по улучшению"""
        recommendations = []

        # Рекомендации по ролям
        for analysis in role_analyses:
            if analysis.overall_score < 70:
                recommendations.append(f"Improve documentation for {analysis.role} role")
            if analysis.content_freshness < 60:
                recommendations.append(f"Update outdated content for {analysis.role}")

        # Рекомендации по системным компонентам
        low_coverage = [cat for cat, score in system_coverage.items() if score < 50]
        if low_coverage:
            recommendations.append(f"Improve coverage for: {', '.join(low_coverage)}")

        return recommendations

    def run_analysis(self, analysis_id: Optional[str] = None) -> CortexHealthReport:
        """Запускает полный анализ кортекса"""
        analysis_id = analysis_id or generate_correlation_id()
        _log("info", "cortex_analysis_started", analysis_id)

        role_analyses = []
        for role in self.roles:
            analysis = self.analyze_role(role, analysis_id=analysis_id)
            role_analyses.append(analysis)

        system_coverage = self.analyze_system_coverage()

        overall_score = (sum(r.overall_score for r in role_analyses) / len(role_analyses)) if role_analyses else 0.0
        recommendations = self.generate_recommendations(role_analyses, system_coverage)

        report = CortexHealthReport(
            timestamp=datetime.now(timezone.utc),
            overall_score=overall_score,
            roles=role_analyses,
            system_coverage=system_coverage,
            recommendations=recommendations
        )

        _log("info", "cortex_analysis_completed", analysis_id, overall_score=overall_score, roles=len(role_analyses))
        return report

    def save_report(self, report: CortexHealthReport, db_path: str = None, analysis_id: Optional[str] = None):
        """Сохраняет отчёт в базу данных"""
        if db_path is None:
            db_path = str(self.data_path / "cortex_health.db")

        # Создаём таблицы если их нет
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cortex_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                overall_score REAL NOT NULL,
                report_data TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                role TEXT NOT NULL,
                doc_coverage REAL NOT NULL,
                context_completeness REAL NOT NULL,
                content_freshness REAL NOT NULL,
                overall_score REAL NOT NULL
            )
        ''')

        # Сохраняем основной отчёт
        cursor.execute('''
            INSERT INTO cortex_reports (timestamp, overall_score, report_data)
            VALUES (?, ?, ?)
        ''', (
            report.timestamp.isoformat(),
            report.overall_score,
            json.dumps(asdict(report), default=str)
        ))

        # Сохраняем метрики по ролям
        for role_analysis in report.roles:
            cursor.execute('''
                INSERT INTO role_metrics (timestamp, role, doc_coverage,
                                        context_completeness, content_freshness, overall_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                report.timestamp.isoformat(),
                role_analysis.role,
                role_analysis.doc_coverage,
                role_analysis.context_completeness,
                role_analysis.content_freshness,
                role_analysis.overall_score
            ))

        conn.commit()
        conn.close()

        analysis_id = analysis_id or generate_correlation_id()
        _log("info", "cortex_analysis_saved", analysis_id, db_path=db_path)

def main():
    """Основная функция для запуска анализа"""
    analyzer = CortexAnalyzer()
    report = analyzer.run_analysis()
    analyzer.save_report(report)

    print(f"Cortex Health Report - {report.timestamp}")
    print(f"Overall Score: {report.overall_score:.1f}%")
    print("\nRole Analysis:")
    for role in report.roles:
        print(f"  {role.role.capitalize()}: {role.overall_score:.1f}%")
        if role.issues:
            print(f"    Issues: {', '.join(role.issues)}")

    if report.recommendations:
        print(f"\nRecommendations:")
        for rec in report.recommendations:
            print(f"  - {rec}")

if __name__ == "__main__":
    main()