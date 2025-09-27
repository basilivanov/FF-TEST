# Рекомендации по реструктуризации документации Cortex

## Анализ текущего состояния

### Текущая структура `/opt/feature-factory/cortex/docs/`

**Количество файлов:** 69 markdown файлов + 5 дополнительных файлов  
**Общий объем:** ~74 документа

### Анализ по категориям

#### ✅ **Хорошо структурированные области:**
1. **API Documentation** - качественный, подробный API.md
2. **UI/Frontend** - полный набор из 10 документов (Components, Development, Testing, Deployment)
3. **CI/CD** - хорошее покрытие процессов сборки и деплоя
4. **Security** - базовая документация по безопасности
5. **Architecture** - общий обзор архитектуры MVP

#### ⚠️ **Проблемные области:**
1. **Отсутствие доменной структуры** - документы смешаны без разделения по бизнес-областям
2. **Плоская структура** - все в одной папке, сложно навигировать
3. **Специфичность Feature Factory** - документация заточена под один проект
4. **Устаревшие документы** - папка `_bundle/` с устаревшими файлами
5. **Отсутствие ML/AI документации** - нет структуры для AI/ML проектов
6. **Нет ETL документации** - минимальные упоминания data pipeline
7. **Отсутствие Enterprise интеграций** - нет CRM/ERP документации
8. **Нет Marketplace документации** - отсутствует e-commerce структура

#### ❌ **Критические недостатки:**
1. **Отсутствие системы тегирования** - нет метаданных для быстрого поиска
2. **Дублирование контента** - некоторая информация повторяется
3. **Несистематичность нумерации** - хаотичные номера версий (001, 000, 002)
4. **Отсутствие индексации по доменам** - невозможно быстро найти релевантную документацию

## Новая универсальная структура

### Предлагаемая структура `/opt/feature-factory/cortex/`

```
cortex/
├── README.md                           # Обзор всей системы документации
├── index/                              # Индексы и навигация
│   ├── domain-index.md                 # Индекс по доменам
│   ├── tag-index.md                    # Индекс по тегам
│   ├── quick-start-index.md            # Быстрый старт по доменам
│   └── doc-registry.json               # Расширенный реестр документов
│
├── domains/                            # Документация по бизнес-доменам
│   ├── marketplace/                    # Маркетплейсы и E-commerce
│   │   ├── api-integrations/           # API интеграции (платежи, доставка)
│   │   ├── catalog-management/         # Управление каталогом продуктов
│   │   ├── order-processing/           # Обработка заказов
│   │   ├── notifications/              # Уведомления покупателей/продавцов
│   │   └── analytics/                  # Аналитика продаж
│   │
│   ├── ml-ai/                          # Machine Learning и AI
│   │   ├── model-training/             # Обучение моделей
│   │   ├── data-pipelines/             # Пайплайны данных для ML
│   │   ├── vector-databases/           # Векторные БД и embeddings
│   │   ├── image-processing/           # Обработка изображений
│   │   ├── text-processing/            # NLP и обработка текста
│   │   └── inference/                  # Инференс и деплой моделей
│   │
│   ├── etl/                            # Extract, Transform, Load
│   │   ├── data-sources/               # Коннекторы к источникам данных
│   │   ├── transformations/            # Правила трансформации
│   │   ├── data-warehouses/            # Хранилища данных
│   │   ├── streaming/                  # Потоковая обработка
│   │   └── monitoring/                 # Мониторинг ETL процессов
│   │
│   ├── enterprise/                     # Enterprise интеграции
│   │   ├── crm-integrations/           # CRM системы
│   │   ├── erp-integrations/           # ERP системы
│   │   ├── reporting/                  # Отчетность и BI
│   │   ├── workflows/                  # Бизнес-процессы
│   │   └── sso-auth/                   # Single Sign-On
│   │
│   ├── web-mobile/                     # Web и Mobile приложения
│   │   ├── frontend/                   # Frontend фреймворки
│   │   ├── mobile-apps/                # Native и hybrid приложения
│   │   ├── pwa/                        # Progressive Web Apps
│   │   ├── micro-frontends/            # Микрофронтенды
│   │   └── ui-components/              # Переиспользуемые компоненты
│   │
│   └── devops-infrastructure/          # DevOps и Infrastructure
│       ├── containerization/           # Docker, Kubernetes
│       ├── ci-cd/                      # Continuous Integration/Deployment
│       ├── monitoring/                 # Мониторинг и алерты
│       ├── security/                   # Безопасность инфраструктуры
│       └── cloud-platforms/            # AWS, GCP, Azure
│
├── foundation/                         # Базовые компоненты (переработанные)
│   ├── architecture/                   # Архитектурные принципы
│   ├── api/                            # API стандарты и документация
│   ├── database/                       # Схемы БД и миграции
│   ├── security/                       # Политики безопасности
│   ├── logging/                        # Стандарты логирования
│   └── testing/                        # Тестирование и QA
│
├── operations/                         # Операционные процессы
│   ├── deployment/                     # Процедуры деплоя
│   ├── monitoring/                     # Операционный мониторинг
│   ├── backup-recovery/                # Резервное копирование
│   ├── incident-response/              # Процедуры при инцидентах
│   └── maintenance/                    # Регулярное обслуживание
│
├── governance/                         # Управление и контроль
│   ├── policies/                       # Политики и стандарты
│   ├── procedures/                     # Процедуры и регламенты
│   ├── compliance/                     # Соответствие требованиям
│   └── change-management/              # Управление изменениями
│
├── templates/                          # Шаблоны документов
│   ├── domain-specific/                # Шаблоны для доменов
│   ├── architecture-docs/              # Шаблоны архитектурных документов
│   ├── api-specs/                      # Шаблоны API спецификаций
│   └── runbooks/                       # Шаблоны эксплуатационных руководств
│
└── archive/                            # Архив устаревших документов
    ├── deprecated/                     # Устаревшие документы
    ├── legacy-systems/                 # Документация устаревших систем
    └── migration-logs/                 # Логи миграции документации
```

## Рекомендации по действиям

### 1. Документы к удалению

**Полностью удалить:**
- `/cortex/docs/_bundle/` - устаревшие бандлы
- Дублирующиеся ADR с одинаковым содержанием
- Файлы с именами-заглушками (stub.md)

### 2. Документы к объединению

**Объединить в единые документы:**
- `UI-*.md` (10 файлов) → `domains/web-mobile/frontend/complete-guide.md`
- `API-*.md` → `foundation/api/complete-api-guide.md`
- `Commands-*.md` → `foundation/architecture/cli-interface.md`
- Различные QA чеклисты → `foundation/testing/qa-procedures.md`

### 3. Документы к переписыванию

**Требуют полного переписывания:**
- `Architecture.md` - слишком специфичен для Feature Factory
- `Security-Guide.md` - добавить Enterprise security practices
- `Monitoring-and-Logging-Guide.md` - расширить для разных доменов

### 4. Новые документы для доменов

#### Marketplace/E-commerce
- `domains/marketplace/payment-integrations.md` - интеграции с платежными системами
- `domains/marketplace/product-catalog-api.md` - API управления каталогом
- `domains/marketplace/order-fulfillment.md` - процессы выполнения заказов
- `domains/marketplace/customer-notifications.md` - система уведомлений
- `domains/marketplace/inventory-management.md` - управление запасами

#### ML/AI
- `domains/ml-ai/model-lifecycle.md` - жизненный цикл ML моделей
- `domains/ml-ai/feature-engineering.md` - инжиниринг признаков
- `domains/ml-ai/vector-search.md` - поиск по векторным embeddings
- `domains/ml-ai/computer-vision.md` - обработка изображений
- `domains/ml-ai/nlp-pipelines.md` - пайплайны обработки текста
- `domains/ml-ai/model-serving.md` - сервинг моделей в продакшене

#### ETL/Data Processing
- `domains/etl/data-connectors.md` - коннекторы к различным источникам
- `domains/etl/transformation-rules.md` - правила трансформации данных
- `domains/etl/data-quality.md` - контроль качества данных
- `domains/etl/streaming-processing.md` - потоковая обработка
- `domains/etl/data-lineage.md` - отслеживание происхождения данных

#### Enterprise Integration
- `domains/enterprise/crm-connectors.md` - интеграции с CRM (Salesforce, HubSpot)
- `domains/enterprise/erp-integrations.md` - интеграции с ERP (SAP, Oracle)
- `domains/enterprise/business-intelligence.md` - BI и аналитика
- `domains/enterprise/workflow-automation.md` - автоматизация бизнес-процессов
- `domains/enterprise/compliance-reporting.md` - отчетность по соответствию

#### Web/Mobile
- `domains/web-mobile/react-patterns.md` - паттерны разработки на React
- `domains/web-mobile/mobile-development.md` - разработка мобильных приложений
- `domains/web-mobile/pwa-implementation.md` - реализация PWA
- `domains/web-mobile/performance-optimization.md` - оптимизация производительности
- `domains/web-mobile/accessibility.md` - обеспечение доступности

#### DevOps/Infrastructure
- `domains/devops-infrastructure/kubernetes-deployment.md` - деплой в Kubernetes
- `domains/devops-infrastructure/docker-best-practices.md` - лучшие практики Docker
- `domains/devops-infrastructure/monitoring-stack.md` - стек мониторинга
- `domains/devops-infrastructure/security-scanning.md` - сканирование безопасности
- `domains/devops-infrastructure/cloud-migration.md` - миграция в облако

### 5. Система тегирования

#### Основные теги

**По доменам:**
- `#marketplace` - маркетплейсы и e-commerce
- `#ml-ai` - машинное обучение и ИИ
- `#etl` - обработка и трансформация данных
- `#enterprise` - корпоративные интеграции
- `#web-mobile` - веб и мобильные приложения
- `#devops` - DevOps и инфраструктура

**По типу контента:**
- `#api` - API документация
- `#tutorial` - пошаговые руководства
- `#reference` - справочная информация
- `#architecture` - архитектурные решения
- `#security` - вопросы безопасности
- `#monitoring` - мониторинг и алерты

**По уровню сложности:**
- `#beginner` - для начинающих
- `#intermediate` - средний уровень
- `#advanced` - продвинутый уровень
- `#expert` - экспертный уровень

**По статусу:**
- `#stable` - стабильная документация
- `#draft` - черновик
- `#deprecated` - устаревшая
- `#experimental` - экспериментальная

#### Пример тегирования в заголовке документа

```markdown
---
title: "Payment Gateway Integration"
domain: marketplace
tags: [marketplace, api, payment, integration, tutorial]
level: intermediate
status: stable
last_updated: "2025-09-18"
maintainer: "platform-team"
related_docs: ["order-processing.md", "customer-notifications.md"]
---
```

### 6. Расширенный doc-registry.json

```json
{
  "version": "2.0.0",
  "last_updated": "2025-09-18T00:00:00Z",
  "domains": {
    "marketplace": {
      "description": "E-commerce and marketplace solutions",
      "lead_maintainer": "marketplace-team",
      "docs_count": 15
    },
    "ml-ai": {
      "description": "Machine Learning and AI systems", 
      "lead_maintainer": "ml-team",
      "docs_count": 12
    },
    "etl": {
      "description": "Data processing and ETL pipelines",
      "lead_maintainer": "data-team", 
      "docs_count": 10
    },
    "enterprise": {
      "description": "Enterprise integrations and systems",
      "lead_maintainer": "enterprise-team",
      "docs_count": 8
    },
    "web-mobile": {
      "description": "Web and mobile applications",
      "lead_maintainer": "frontend-team",
      "docs_count": 18
    },
    "devops-infrastructure": {
      "description": "DevOps and infrastructure management",
      "lead_maintainer": "platform-team",
      "docs_count": 14
    }
  },
  "docs": [
    {
      "path": "domains/marketplace/payment-integrations.md",
      "title": "Payment Gateway Integration",
      "domain": "marketplace",
      "tags": ["marketplace", "api", "payment", "integration"],
      "level": "intermediate",
      "status": "stable",
      "version": "2.1.0",
      "content_hash": "a1b2c3d4e5f",
      "last_updated": "2025-09-18T00:00:00Z",
      "maintainer": "marketplace-team",
      "related_docs": ["order-processing.md", "customer-notifications.md"]
    }
  ]
}
```

## План миграции

### Этап 1: Подготовка (1-2 недели)
1. Создать новую структуру папок
2. Разработать шаблоны документов для каждого домена
3. Обновить doc-registry.json с новой схемой
4. Создать скрипты автоматической миграции

### Этап 2: Миграция основных документов (2-3 недели)
1. Перенести и адаптировать существующие документы
2. Объединить дублирующиеся документы
3. Переписать Architecture.md для универсальности
4. Создать индексные файлы

### Этап 3: Создание доменной документации (3-4 недели)
1. Создать базовую документацию для каждого домена
2. Добавить специфичные для доменов руководства
3. Создать cross-domain интеграционные гайды
4. Добавить примеры и use cases

### Этап 4: Тестирование и валидация (1 неделя)
1. Проверить все ссылки и референсы
2. Валидировать полноту документации
3. Получить обратную связь от команд
4. Финальные корректировки

### Этап 5: Запуск и поддержка
1. Обновить все системы, ссылающиеся на старую структуру
2. Обучить команды новой структуре
3. Настроить автоматические проверки качества документации
4. Установить процессы регулярного обновления

## Инструменты для поддержки

### Скрипт валидации документации
```bash
#!/bin/bash
# scripts/validate-docs.sh
# Проверяет соответствие документов новой структуре

# Проверка тегов в заголовках
# Проверка ссылок между документами  
# Валидация doc-registry.json
# Проверка актуальности дат обновления
```

### Автогенерация индексов
```python
# scripts/generate-indices.py
# Автоматически генерирует индексные файлы на основе метаданных документов
```

### Система уведомлений об обновлениях
```yaml
# .github/workflows/docs-notification.yml
# GitHub Action для уведомления команд об изменениях в их доменной документации
```

## Заключение

Предлагаемая реструктуризация превратит cortex/ из специализированной документации Feature Factory в универсальную систему, способную поддерживать различные бизнес-домены. Новая структура обеспечит:

1. **Масштабируемость** - легкое добавление новых доменов
2. **Навигацию** - быстрый поиск релевантной документации
3. **Консистентность** - единые стандарты оформления
4. **Актуальность** - автоматизированная поддержка актуальности
5. **Интеграцию** - связи между доменами и cross-cutting concerns

Эта система станет надежной основой для документирования любых проектов в экосистеме, от простых веб-приложений до комплексных Enterprise решений.