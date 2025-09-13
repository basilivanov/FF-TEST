#!/usr/bin/env python3
"""
Роле-специфичные шаблоны контекста для ContextPackager V2
"""
import os
from typing import Dict, List, Any
from pathlib import Path

class RoleContextBuilder:
    """Строитель роле-специфичного контекста"""
    
    def __init__(self, cortex_root: str = "/opt/feature-factory/cortex"):
        self.cortex_root = Path(cortex_root)
        self.role_templates = self._init_role_templates()
    
    def _init_role_templates(self) -> Dict[str, Dict[str, Any]]:
        """Инициализация шаблонов контекста для каждой роли"""
        return {
            "Architect": {
                "priority_docs": [
                    "docs/Architecture.md",
                    "docs/Schemas-Index.md", 
                    "docs/API-Contracts.md",
                    "api/openapi.yaml",
                    "playbook/task_handoff_protocol.md"
                ],
                "examples": [
                    "examples/architect/*.yaml",
                    "templates/feature_plan.yaml"
                ],
                "context_focus": "system_design",
                "token_budget": 2000
            },
            
            "Dev": {
                "priority_docs": [
                    "docs/Security-Guide.md",
                    "docs/API-Development-Guide.md",
                    "policies/agent_file_access.md",
                    "stack/fastapi_patterns.md",
                    "db_rules.md",
                    "logging_rules.md"
                ],
                "examples": [
                    "app/api/*.py",
                    "app/models/*.py", 
                    "app/schemas/*.py",
                    "examples/fastapi/*.py",
                    "examples/sqlalchemy/*.py"
                ],
                "context_focus": "code_implementation",
                "token_budget": 2500
            },
            
            "QA": {
                "priority_docs": [
                    "docs/QA-Checklists/*.md",
                    "docs/API-Testing-Guide.md",
                    "docs/E2E-Testing-Guide.md",
                    "docs/Gate-Rules-Roles.md"
                ],
                "examples": [
                    "examples/testing/*.py",
                    "templates/qa_report.json",
                    "scripts/ci/*.sh"
                ],
                "context_focus": "quality_validation",
                "token_budget": 2000
            },
            
            "Gate": {
                "priority_docs": [
                    "docs/Gate-Rules-Roles.md",
                    "docs/LangGraph-Nodes-Contracts.md",
                    "policies/security_policies.md",
                    "docs/Risk-Assessment.md"
                ],
                "examples": [
                    "templates/gate_decision.json",
                    "examples/approval_criteria.yaml"
                ],
                "context_focus": "approval_criteria",
                "token_budget": 1500
            },
            
            "Scribe": {
                "priority_docs": [
                    "docs/Documentation-Standards.md",
                    "docs/ChangePolicy*.md",
                    "docs/Versioning-Guide.md"
                ],
                "examples": [
                    "templates/changelog.md",
                    "templates/release_notes.md",
                    "examples/documentation/*.md"
                ],
                "context_focus": "documentation",
                "token_budget": 1500
            },
            
            "Apply": {
                "priority_docs": [
                    "docs/Ops-Guide.md",
                    "docs/Deployment-Guide.md", 
                    "docs/Git-Operations.md",
                    "scripts/ops/*.sh"
                ],
                "examples": [
                    "examples/deployment/*.yaml",
                    "scripts/deploy/*.sh",
                    "templates/pr_template.md"
                ],
                "context_focus": "operations",
                "token_budget": 1500
            }
        }
    
    def build_role_context(self, role: str, task_keywords: List[str] = None) -> str:
        """Строит роле-специфичный контекст"""
        if role not in self.role_templates:
            return f"# Неизвестная роль: {role}\n"
            
        template = self.role_templates[role]
        context_parts = []
        
        # Заголовок роли
        context_parts.append(f"# Контекст для роли {role}\n")
        
        # Приоритетные документы
        context_parts.append(self._build_priority_docs(template["priority_docs"]))
        
        # Примеры кода/конфигураций
        context_parts.append(self._build_examples_section(template["examples"], task_keywords))
        
        # Роле-специфичные правила
        context_parts.append(self._build_role_specific_rules(role))
        
        return "\n\n".join(filter(None, context_parts))
    
    def _build_priority_docs(self, doc_paths: List[str]) -> str:
        """Строит секцию с приоритетными документами"""
        docs_content = []
        
        for doc_path in doc_paths:
            full_path = self.cortex_root / doc_path
            
            # Поддержка glob паттернов
            if "*" in doc_path:
                import glob
                matching_files = glob.glob(str(full_path))
                for file_path in matching_files[:3]:  # Ограничиваем количество
                    content = self._read_file_safe(file_path)
                    if content:
                        docs_content.append(f"## {os.path.basename(file_path)}\n{content}")
            else:
                content = self._read_file_safe(full_path)
                if content:
                    docs_content.append(f"## {doc_path}\n{content}")
        
        if docs_content:
            return "# Ключевые документы\n\n" + "\n\n".join(docs_content)
        return ""
    
    def _build_examples_section(self, example_patterns: List[str], keywords: List[str] = None) -> str:
        """Строит секцию с примерами кода"""
        examples = []
        
        for pattern in example_patterns:
            # Для файлов приложения используем поиск в app/
            if pattern.startswith("app/"):
                app_path = Path("/opt/feature-factory") / pattern
                if "*" in pattern:
                    import glob
                    matching_files = glob.glob(str(app_path))
                    for file_path in matching_files[:5]:  # Ограничиваем количество
                        if self._is_relevant_file(file_path, keywords):
                            content = self._read_file_safe(file_path, max_lines=50)
                            if content:
                                examples.append(f"### {os.path.relpath(file_path, '/opt/feature-factory')}\n```python\n{content}\n```")
                else:
                    content = self._read_file_safe(app_path, max_lines=50)
                    if content:
                        examples.append(f"### {pattern}\n```python\n{content}\n```")
            
            # Для cortex файлов
            else:
                cortex_path = self.cortex_root / pattern
                if cortex_path.exists():
                    content = self._read_file_safe(cortex_path, max_lines=30)
                    if content:
                        examples.append(f"### {pattern}\n```\n{content}\n```")
        
        if examples:
            return "# Примеры и шаблоны\n\n" + "\n\n".join(examples)
        return ""
    
    def _build_role_specific_rules(self, role: str) -> str:
        """Строит роле-специфичные правила"""
        rules = {
            "Architect": """# Правила для Architect
            
• ВСЕГДА использовать Task Handoff Protocol с YAML блоком
• Обязательные поля: task, corr_id, context, prechecks, plan, dod, artifacts_dir
• DoD критерии должны быть проверяемыми
• Один YAML блок = одна задача
• Указывать абсолютные пути и полные URL
""",
            
            "Dev": """# Правила для Dev

• Все изменения БД только через Alembic: `alembic revision --autogenerate -m "description"`
• Uvicorn запускать только из корня проекта: `cd /opt/feature-factory && uvicorn app.main:app`
• Секреты только через secret_store.get_secret(key)
• FastAPI endpoints следуют паттернам из app/api/
• Обязательная валидация через Pydantic схемы
• Тесты для критических путей кода
""",

            "QA": """# Правила для QA

• Проверяем все DoD критерии из задач Architect
• Валидация API через OpenAPI схемы
• Тестирование аутентификации и авторизации
• Проверка обработки ошибок и edge cases
• Документирование найденных проблем в структурированном формате
• Smoke тесты для критических функций
""",

            "Gate": """# Правила для Gate

• Решения только: allow/deny с confidence и reasons
• Проверка соответствия роли и задаче
• Валидация безопасности (no secrets, allowed paths)
• Оценка рисков и потенциального воздействия
• Эскалация при высоких рисках или неопределенности
""",

            "Scribe": """# Правила для Scribe

• Changelog в семантическом формате
• Документация изменений API
• Версионирование согласно SemVer
• Связывание с correlation_id задач
• Обновление документации при изменении интерфейсов
""",

            "Apply": """# Правила для Apply

• Git операции через безопасные скрипты
• PR создание с proper базовой веткой
• Проверка CI статусов перед merge
• Откат при проблемах деплоя
• Обновление метрик и мониторинга
"""
        }
        
        return rules.get(role, "")
    
    def _read_file_safe(self, file_path, max_lines: int = None) -> str:
        """Безопасное чтение файла с ограничениями"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if max_lines:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f"... (обрезано на {max_lines} строк)")
                            break
                        lines.append(line.rstrip())
                    return "\n".join(lines)
                else:
                    return f.read()
        except Exception as e:
            return f"# Ошибка чтения файла {file_path}: {e}"
    
    def _is_relevant_file(self, file_path: str, keywords: List[str] = None) -> bool:
        """Проверяет релевантность файла по ключевым словам"""
        if not keywords:
            return True
            
        file_name = os.path.basename(file_path).lower()
        file_content = self._read_file_safe(file_path, max_lines=20).lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in file_name or keyword_lower in file_content:
                return True
        
        return False

# Пример использования
if __name__ == "__main__":
    builder = RoleContextBuilder()
    
    # Тест для роли Dev с ключевыми словами
    dev_context = builder.build_role_context("Dev", ["users", "crud", "fastapi"])
    print("=== Dev Context ===")
    print(dev_context[:1000])  # Первые 1000 символов
    
    # Тест для роли Architect
    architect_context = builder.build_role_context("Architect")
    print("\n=== Architect Context ===")
    print(architect_context[:1000])  # Первые 1000 символов