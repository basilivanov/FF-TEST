# GitHub Branch Protection Configuration

Для настройки блокирующего статуса при падении E2E тестов необходимо настроить Branch Protection Rules в GitHub.

## Настройка через GitHub UI

1. Перейдите в Settings → Branches
2. Нажмите "Add rule" для ветки `main`
3. Настройте следующие параметры:

### Branch protection rule для main:

```
Branch name pattern: main

☑️ Require a pull request before merging
   ☑️ Require approvals: 1
   ☑️ Dismiss stale PR approvals when new commits are pushed

☑️ Require status checks to pass before merging
   ☑️ Require branches to be up to date before merging
   
   Required status checks:
   - E2E Regression Tests / feature_e2e
   - E2E Regression Tests / task_e2e
   
☑️ Require linear history
☑️ Include administrators
```

## Настройка через GitHub CLI

Если у вас есть GitHub CLI, можно настроить автоматически:

```bash
# Создание branch protection rule
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["E2E Regression Tests / feature_e2e","E2E Regression Tests / task_e2e"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false
```

## Результат

После настройки:
- Merge в main будет заблокирован, если E2E тесты падают
- Pull Request нельзя будет смержить без прохождения обоих E2E тестов
- Статус тестов будет отображаться в PR как required check

## Проверка работы

1. Создайте тестовый PR
2. Убедитесь, что показываются required checks:
   - "E2E Regression Tests / feature_e2e"
   - "E2E Regression Tests / task_e2e"
3. PR можно мержить только после ✅ обоих тестов