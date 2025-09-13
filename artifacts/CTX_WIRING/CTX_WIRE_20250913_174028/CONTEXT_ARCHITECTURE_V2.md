# ContextPackager V2 - Трёхслойная архитектура

## Проблема текущего ContextPackager

Анализ показал критические недостатки:
- **20/100 баллов** для роли Dev
- Только правила/запреты, нет технических примеров
- Отсутствует файловая аналитика задач
- Нет адаптации под конкретные роли

## Новая архитектура: 3 слоя

### Слой 1: Универсальный контекст (BASE_CONTEXT)
**Для всех ролей, статический, 2000-2500 токенов**

```
├── SSOT Capsule (из SSoT документа пользователя)
├── Mission & Principles (context_first, corr_id_required, etc.)
├── Core Architecture (API endpoints, services, database)
├── Critical Invariants (Alembic only, no mocks in prod, etc.)
├── Universal Rules (Git, OAuth, CLI wrappers)
└── Current Environment Status (TEST контур, сервисы up)
```

### Слой 2: Роле-специфичный контекст (ROLE_CONTEXT)
**Адаптивный под роль, 1500-2500 токенов**

```
Architect:
├── Task Handoff Protocol (YAML format, DoD requirements)
├── API Design Patterns
├── Schema definitions
├── Integration contracts
└── Planning templates

Dev:
├── Code Examples (FastAPI, Pydantic, SQLAlchemy)
├── File Structure patterns
├── Authentication flows  
├── Testing frameworks
├── Deployment procedures
└── Security guidelines

QA:
├── Testing strategies
├── Validation schemas
├── Quality gates
├── Coverage requirements
└── Bug reporting formats

Gate:
├── Approval criteria per role
├── Risk assessment templates
├── Security checks
├── Compliance rules
└── Escalation procedures

Scribe:
├── Documentation standards
├── Changelog formats
├── API documentation
├── Release notes templates
└── Versioning rules

Apply:
├── Deployment procedures
├── Git operations
├── PR management
├── CI/CD pipelines
└── Rollback procedures
```

### Слой 3: Динамический контекст (DYNAMIC_CONTEXT)
**На основе задачи и ctag из БД, 2000-4000 токенов**

```
Task Analysis:
├── Keyword extraction от user_intent
├── Relevance scoring по symbol_index
├── File discovery через call_graph_edges
├── Similar task patterns
└── Related components

Symbol Index Integration:
├── Функции/классы по keyword match
├── API endpoints для CRUD задач
├── Database models для entity operations
├── Test files для validation tasks
└── Config files для system changes

Context Graph:
├── Primary files (прямое совпадение)
├── Dependency files (call graph edges) 
├── Similar patterns (ML similarity)
├── Test coverage files
└── Documentation files
```

## Реализация

### 1. Базовый контекст (универсальный)

```python
class BaseContextBuilder:
    def build_universal_context(self) -> str:
        sections = [
            self._build_ssot_capsule(),      # SSoT из документа пользователя
            self._build_core_architecture(), # Основная архитектура системы
            self._build_universal_rules(),   # Правила для всех ролей
            self._build_environment_status() # Текущий статус TEST контура
        ]
        return "\n\n".join(sections)
```

### 2. Роле-специфичный контекст

```python
class RoleContextBuilder:
    ROLE_TEMPLATES = {
        "Dev": {
            "code_examples": "cortex/examples/fastapi/*.py",
            "patterns": "cortex/patterns/dev/*.md", 
            "guidelines": "cortex/docs/Security-Guide.md"
        },
        "Architect": {
            "schemas": "cortex/api/openapi.yaml",
            "contracts": "cortex/docs/API-Contracts.md",
            "templates": "cortex/templates/task_handoff.yaml"
        }
        # ... остальные роли
    }

    def build_role_context(self, role: str, task_keywords: List[str]) -> str:
        template = self.ROLE_TEMPLATES.get(role, {})
        return self._assemble_role_specific_docs(template, task_keywords)
```

### 3. Динамический контекст

```python
class DynamicContextBuilder:
    def __init__(self, db_session):
        self.db = db_session
        
    def build_dynamic_context(self, task: Dict, role: str) -> str:
        keywords = self._extract_keywords(task["user_intent"])
        
        # Поиск по symbol_index
        symbols = self._find_relevant_symbols(keywords)
        
        # Расширение через call_graph
        related_files = self._expand_via_call_graph(symbols)
        
        # Формирование контекста
        return self._build_file_context(related_files, task, role)
        
    def _find_relevant_symbols(self, keywords: List[str]) -> List[Dict]:
        query = """
        SELECT si.file_path, si.symbol_name, si.symbol_type, si.line_start, si.line_end
        FROM symbol_index si 
        JOIN code_registry cr ON si.file_path = cr.file_path
        WHERE si.symbol_name ILIKE ANY(%s) 
        OR si.file_path ILIKE ANY(%s)
        ORDER BY 
            CASE WHEN si.symbol_type = 'function' THEN 1
                 WHEN si.symbol_type = 'class' THEN 2
                 ELSE 3 END
        LIMIT 20
        """
        return self.db.execute(query, (keywords, keywords)).fetchall()
```

## Токеновый бюджет

| Слой | Роль | Мин. токены | Макс. токены | Приоритет |
|------|------|-------------|--------------|-----------|
| BASE_CONTEXT | Все | 2000 | 2500 | Всегда |
| ROLE_CONTEXT | Architect | 1500 | 2000 | Высокий |
| ROLE_CONTEXT | Dev | 2000 | 2500 | Высокий |  
| ROLE_CONTEXT | QA/Gate | 1500 | 2000 | Высокий |
| ROLE_CONTEXT | Scribe/Apply | 1000 | 1500 | Средний |
| DYNAMIC_CONTEXT | Все | 2000 | 4000 | Адаптивный |
| **ИТОГО** | | **6500** | **10000** | |

## Интеграция с существующей системой

### Патч для ContextPackager

```python
class ContextPackagerV2(ContextPackager):
    def __init__(self):
        super().__init__()
        self.base_builder = BaseContextBuilder()
        self.role_builder = RoleContextBuilder() 
        self.dynamic_builder = DynamicContextBuilder(db_session)
        
    def build_context_for_task(self, task: Dict[str, Any]) -> str:
        role = task.get("role")
        
        # Валидация минимальных требований (из существующего кода)
        need_context_error = self._validate_minimum_context_per_role(role, {})
        if need_context_error:
            return json.dumps(need_context_error, ensure_ascii=False)
            
        # Сборка трёхслойного контекста
        base_context = self.base_builder.build_universal_context()
        role_context = self.role_builder.build_role_context(role, task)
        dynamic_context = self.dynamic_builder.build_dynamic_context(task, role)
        
        # Композиция финального контекста
        return self._compose_final_context(base_context, role_context, dynamic_context)
```

## Преимущества новой архитектуры

1. **Адаптивность**: контекст подстраивается под роль и задачу
2. **Релевантность**: примеры кода вместо только правил
3. **Масштабируемость**: каждый слой может развиваться независимо
4. **Эффективность**: оптимальное использование токенов
5. **Интеграция**: использует существующую БД и symbol_index

## Ожидаемые результаты

- **Dev роль**: повышение с 20/100 до 85-95/100 баллов
- **Все роли**: релевантные примеры кода и шаблоны
- **Динамическая аналитика**: автоматический поиск релевантных файлов
- **Unified experience**: все роли получают согласованный контекст

## Следующие шаги

1. ✅ Создать архитектурный план V2
2. 🔄 Реализовать BaseContextBuilder 
3. 🔄 Реализовать RoleContextBuilder
4. 🔄 Реализовать DynamicContextBuilder
5. 🔄 Интегрировать с существующим ContextPackager
6. 🔄 Протестировать на всех ролях
7. 🔄 Развернуть и измерить улучшения