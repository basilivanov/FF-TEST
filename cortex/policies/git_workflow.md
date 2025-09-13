# Git Workflow Политики

## Инварианты Git операций

### Базовая конфигурация
- **Базовая ветка:** `main` (никогда не коммитим напрямую)
- **SSH ключ:** `~/.ssh/id_ed25519_ff` 
- **Origin:** `git@github.com:basilivanov/FF-TEST.git` (обязательно SSH)
- **SSH Config:**
```
Host github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_ff
  IdentitiesOnly yes
```

## Branch стратегия

### Паттерн именования веток
`feature/<id>_<slug>` где:
- `<id>` — уникальный числовой идентификатор
- `<slug>` — краткое описание (kebab-case)

Примеры:
- `feature/12345_user_auth`
- `feature/67890_api_metrics`

### Branch lifecycle
1. Создание ветки из `main`
2. Коммиты с уникальными артефактами (избегаем пустой diff)  
3. Push в origin
4. Создание PR через GitHub API
5. CI проверки (lint, tests, build, smoke)
6. Auto-merge при 4×success

## PR workflow

### Обязательные проверки
- **lint** — проверка стиля кода
- **tests** — прохождение юнит-тестов
- **build** — успешная сборка проекта  
- **smoke** — smoke тесты критических функций

### PR метаданные
API должно заполнять:
- `pr_url` — ссылка на PR
- `git_branch` — имя ветки
- `commit_sha` — SHA коммита
- `merged_sha` — SHA после merge (при успешном merge)

### Auto-merge правила
- Все 4 проверки должны быть зеленые
- Нет конфликтов с базовой веткой
- PR не помечен как Draft
- Соблюдены GitHub branch protection rules

## Commit правила

### Формат сообщений
```
<type>(<scope>): <description>

<body>

<footer>
```

Примеры:
```
feat(api): add health check endpoint
fix(db): resolve connection timeout issue  
docs(readme): update installation instructions
```

### Pre-commit проверки
- Отсутствие секретов в коде
- Валидность JSON/YAML файлов
- Форматирование согласно стандартам проекта
- Размер файлов не превышает лимиты