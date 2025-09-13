# CI/CD Guide

## Обзор

Этот документ описывает процессы непрерывной интеграции и доставки (CI/CD) Feature Factory.

## Архитектура CI/CD

### Платформа

CI/CD реализован на GitHub Actions.

### Репозиторий

Репозиторий: `https://github.com/chococraft/feature-factory`

### Ветки

- `main`: основная ветка (продакшен)
- `develop`: ветка разработки
- `feature/*`: ветки фич
- `hotfix/*`: ветки хотфиксов
- `release/*`: ветки релизов

## Процесс CI

### Запуск CI

CI запускается автоматически при:
- Пуш в любую ветку
- Создание pull request
- Ручной запуск

### Этапы CI

#### 1. Установка зависимостей

```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    cd app/ui
    npm install
```

#### 2. Линтинг

##### Python линтинг

```yaml
- name: Lint Python code
  run: |
    flake8 app/
    black --check app/
    isort --check-only app/
```

##### TypeScript линтинг

```yaml
- name: Lint TypeScript code
  run: |
    cd app/ui
    npm run lint
```

#### 3. Тестирование

##### Python тестирование

```yaml
- name: Run Python tests
  run: |
    python -m pytest tests/ --cov=app --cov-report=xml
```

##### TypeScript тестирование

```yaml
- name: Run TypeScript tests
  run: |
    cd app/ui
    npm test -- --coverage --coverageReporters=text-summary --coverageReporters=cobertura
```

#### 4. Сборка

##### Сборка UI

```yaml
- name: Build UI
  run: |
    cd app/ui
    npm run build
```

#### 5. Анализ качества кода

##### SonarQube анализ

```yaml
- name: SonarQube Scan
  uses: sonarsource/sonarqube-scan-action@master
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
    SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

#### 6. Безопасность

##### Сканер уязвимостей

```yaml
- name: Security scan
  run: |
    # Dependabot для Python зависимостей
    # Trivy для Docker образов
    # Bandit для Python кода
```

### Условия прохождения CI

CI считается успешным, если:
- Все этапы выполнены без ошибок
- Покрытие кода тестами ≥ 80%
- Нет критических уязвимостей безопасности
- Нет нарушений стиля кода

## Процесс CD

### Деплой в тестовое окружение

#### Условия

Деплой в тестовое окружение происходит при:
- Успешном прохождении CI в ветке `develop`
- Ручном триггере

#### Процесс

1. Сборка Docker образа
2. Деплой в тестовое окружение
3. Запуск smoke тестов

#### GitHub Actions workflow

```yaml
name: Deploy to Test

on:
  push:
    branches:
      - develop
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: chococraft/feature-factory:test

      - name: Deploy to test
        run: |
          ssh feature-factory@test-server "docker pull chococraft/feature-factory:test && docker-compose down && docker-compose up -d"
```

### Деплой в продакшен

#### Условия

Деплой в продакшен происходит при:
- Создании релиза
- Ручном триггере

#### Процесс

1. Создание релиза
2. Сборка Docker образа
3. Деплой в продакшен окружение
4. Запуск smoke тестов
5. Мониторинг метрик

#### GitHub Actions workflow

```yaml
name: Deploy to Production

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: chococraft/feature-factory:latest,chococraft/feature-factory:${{ github.ref_name }}

      - name: Deploy to production
        run: |
          ssh feature-factory@prod-server "docker pull chococraft/feature-factory:${{ github.ref_name }} && docker-compose down && docker-compose up -d"

      - name: Run smoke tests
        run: |
          # Запуск smoke тестов
```

## Версионирование

### Схема версионирования

Feature Factory использует Semantic Versioning (SemVer):
- MAJOR: несовместимые изменения API
- MINOR: обратно совместимые изменения функциональности
- PATCH: обратно совместимые исправления ошибок

### Создание релизов

Релизы создаются вручную через GitHub Releases:
1. Перейти в раздел Releases
2. Нажать "Draft a new release"
3. Выбрать тег (например, v1.2.3)
4. Указать название релиза
5. Добавить описание изменений
6. Опубликовать релиз

## Branching Strategy

### Git Flow

Feature Factory использует упрощенную версию Git Flow:
- `main`: стабильная версия кода
- `develop`: ветка разработки
- `feature/*`: ветки для разработки фич
- `hotfix/*`: ветки для срочных исправлений
- `release/*`: ветки для подготовки релизов

### Работа с фичами

1. Создать ветку от `develop`: `git checkout -b feature/feature-name develop`
2. Разрабатывать фичу в своей ветке
3. Создать pull request в `develop`
4. Пройти code review
5. Слить ветку в `develop`

### Hotfixes

1. Создать ветку от `main`: `git checkout -b hotfix/hotfix-name main`
2. Внести исправления
3. Создать pull request в `main`
4. Пройти code review
5. Слить ветку в `main` и `develop`

### Releases

1. Создать ветку от `develop`: `git checkout -b release/release-name develop`
2. Подготовить релиз (обновить версию, документацию)
3. Создать pull request в `main`
4. Пройти code review
5. Слить ветку в `main`
6. Создать релиз через GitHub Releases

## Code Review

### Процесс

Code review проводится через GitHub Pull Requests:
1. Создать pull request
2. Назначить reviewers
3. Дождаться комментариев
4. Внести правки при необходимости
5. Получить approve
6. Слить pull request

### Критерии

#### Общие критерии

1. **Стиль кода**: соблюдение стандартов кодирования
2. **Тесты**: наличие и качество тестов
3. **Документация**: обновление документации при необходимости
4. **Безопасность**: отсутствие уязвимостей
5. **Производительность**: эффективность кода
6. **Читаемость**: понятность кода

#### Python критерии

1. **PEP 8**: соблюдение рекомендаций по стилю
2. **Типизация**: использование аннотаций типов
3. **Документация**: docstrings для всех публичных функций и классов
4. **Логирование**: использование стандартного логирования
5. **Обработка ошибок**: корректная обработка исключений

#### TypeScript критерии

1. **TypeScript**: использование строгой типизации
2. **React**: соблюдение лучших практик React
3. **Hooks**: корректное использование hooks
4. **Компоненты**: повторное использование и тестируемость
5. **Стили**: использование Tailwind CSS

## Тестирование

### Уровни тестирования

#### Unit тесты

- Тестирование отдельных функций и компонентов
- Высокое покрытие критических путей (≥ 80%)
- Быстрое выполнение (< 1 сек на тест)

#### Integration тесты

- Тестирование взаимодействия между компонентами
- Тестирование API эндпоинтов
- Тестирование базы данных

#### E2E тесты

- Тестирование полного цикла работы приложения
- Smoke тесты для критических путей
- Тестирование UI

### Инструменты тестирования

#### Python

- **pytest**: фреймворк для тестирования
- **pytest-cov**: измерение покрытия кода
- **httpx**: для тестирования HTTP запросов
- **respx**: для мокирования HTTP запросов

#### TypeScript

- **Jest**: фреймворк для тестирования
- **React Testing Library**: для тестирования React компонентов
- **Mock Service Worker**: для мокирования API запросов

### Покрытие кода

Цель покрытия кода тестами: 80% для критических компонентов.

Критические компоненты:
- API эндпоинты
- Бизнес-логика
- Компоненты UI

### Тестирование производительности

Регулярно проводится тестирование производительности:
- Load testing
- Stress testing
- Spike testing

## Deployment

### Стратегия деплоя

Feature Factory использует Blue-Green deployment:
1. Подготовка нового окружения (Green)
2. Деплой в новое окружение
3. Тестирование нового окружения
4. Переключение трафика на новое окружение
5. Удаление старого окружения (Blue)

### Rollback

При возникновении проблем происходит rollback:
1. Переключение трафика на старое окружение
2. Анализ проблемы
3. Исправление проблемы
4. Повторный деплой

### Canary deployment

Для крупных изменений может использоваться Canary deployment:
1. Деплой на небольшую часть инфраструктуры
2. Мониторинг метрик
3. Постепенное увеличение доли трафика
4. Полный деплой при отсутствии проблем

## Monitoring

### Метрики

#### Application Metrics

- Время отклика API
- Количество запросов
- Количество ошибок
- Использование ресурсов (CPU, память, диск)

#### Business Metrics

- Количество созданных фич
- Скорость обработки задач
- Время выполнения графов
- Количество обработанных записей

#### Infrastructure Metrics

- Доступность сервисов
- Загрузка серверов
- Использование дискового пространства
- Сетевой трафик

### Алерты

#### Critical Alerts

- Сервис недоступен
- Высокий уровень ошибок
- Превышение лимитов токенов
- Низкое дисковое пространство

#### Warning Alerts

- Высокое время отклика
- Низкий уровень успеха задач
- Приближение к лимитам токенов
- Высокая загрузка CPU

### Dashboards

#### System Dashboard

- Состояние API
- Состояние базы данных
- Состояние индекса
- Количество активных задач
- Количество ошибок

#### Business Dashboard

- Количество созданных фич
- Скорость обработки задач
- Время выполнения графов
- Количество обработанных записей

#### LLM Dashboard

- Использование токенов по ролям
- Использование токенов по моделям
- Время отклика LLM
- Количество вызовов
- Количество cache hit/miss

#### Financial Dashboard

- Стоимость использования LLM
- Бюджеты по ролям
- Прогноз расходов

## Security

### Security Scanning

#### Dependency Scanning

- Dependabot для проверки зависимостей
- Trivy для проверки Docker образов
- Bandit для проверки Python кода

#### Container Scanning

- Clair для сканирования Docker образов
- Anchore для анализа образов

#### Infrastructure Scanning

- Terraform security scanning
- Kubernetes security scanning

### Secrets Management

#### Secret Detection

- Git-secrets для предотвращения коммита секретов
- TruffleHog для поиска секретов в репозитории

#### Secret Rotation

- Автоматическая ротация секретов
- Уведомления о истечении срока действия секретов

## Documentation

### Обновление документации

Документация обновляется автоматически при изменении кода:
- API документация генерируется из кода
- Документация по компонентам обновляется при изменении компонентов
- Руководства обновляются при изменении процессов

### Versioning Documentation

Документация версионируется вместе с кодом:
- Каждая версия документации соответствует версии кода
- Документация доступна по тегам релизов

## Best Practices

### CI

1. **Быстрые сборки**: оптимизируйте время сборки
2. **Параллельное выполнение**: используйте параллельное выполнение задач
3. **Кэширование**: кэшируйте зависимости для ускорения сборок
4. **Изоляция**: изолируйте среды сборки
5. **Уведомления**: настраивайте уведомления о статусе сборок

### CD

1. **Автоматизация**: максимально автоматизируйте процесс деплоя
2. **Canary deployments**: используйте канареечные деплои для крупных изменений
3. **Rollback**: обеспечьте возможность быстрого отката
4. **Мониторинг**: мониторьте приложение после деплоя
5. **Security**: обеспечьте безопасность процесса деплоя

### Testing

1. **Покрытие кода**: стремитесь к высокому покрытию кода тестами
2. **Разнообразие тестов**: используйте разные типы тестов
3. **Тестовые данные**: используйте реалистичные тестовые данные
4. **Тестирование производительности**: регулярно тестируйте производительность
5. **Тестирование безопасности**: регулярно тестируйте безопасность

### Code Review

1. **Своевременность**: проводите code review быстро
2. **Конструктивность**: давайте конструктивные комментарии
3. **Соблюдение стандартов**: следуйте принятым стандартам кодирования
4. **Обучение**: используйте code review как возможность обучения
5. **Фокус**: фокусируйтесь на критических аспектах кода

## Troubleshooting

### Common Issues

#### CI Failures

1. **Dependency issues**: проверьте зависимости и их версии
2. **Linting errors**: исправьте нарушения стиля кода
3. **Test failures**: исправьте падающие тесты
4. **Security vulnerabilities**: устраните уязвимости

#### CD Failures

1. **Deployment failures**: проверьте конфигурацию деплоя
2. **Rollback issues**: проверьте возможность отката
3. **Monitoring failures**: проверьте настройки мониторинга
4. **Security breaches**: проверьте настройки безопасности

### Debugging

#### CI Debugging

1. **Логи сборок**: анализируйте логи сборок
2. **Локальное воспроизведение**: воспроизводите проблемы локально
3. **Изоляция проблем**: изолируйте проблемные компоненты
4. **Тестирование гипотез**: тестируйте гипотезы о причинах проблем

#### CD Debugging

1. **Логи деплоя**: анализируйте логи деплоя
2. **Мониторинг метрик**: анализируйте метрики после деплоя
3. **Логи приложения**: анализируйте логи приложения
4. **Тестирование функциональности**: тестируйте функциональность после деплоя

## Contacts

По вопросам CI/CD обращайтесь к команде DevOps по адресу devops@chococraft.ru.