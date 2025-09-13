# Политика enforce для Router

## Общие положения

Этот документ описывает политику применения маршрутизации LLM по ролям, включая температуру, максимальное количество токенов, fallback-матрицу и обработку ситуаций WAIT_BUDGET.

## Настройки по ролям

### Architect

**Параметры:**
- **Temperature**: 0.2
- **Max Tokens**: 4096
- **Primary Provider**: claude
- **Fallback Chain**: gpt → gemini
- **Timeout**: 30 секунд

**Поведение при ошибках:**
- **Non-zero RC**: Выполняется fallback на следующего провайдера в цепочке
- **Timeout**: Выполняется fallback на следующего провайдера в цепочке
- **JSON Parse Error**: Выполняется fallback на следующего провайдера в цепочке

**Логирование:**
```json
{
  "event": "llm_fallback",
  "from_provider": "claude",
  "to_provider": "gpt",
  "reason": "timeout",
  "role": "Architect",
  "task_id": "task_12345"
}
```

### Dev

**Параметры:**
- **Temperature**: 0
- **Max Tokens**: 4096
- **Primary Provider**: qwen
- **Fallback Chain**: gemini
- **Timeout**: 30 секунд

**Поведение при ошибках:**
- **Non-zero RC**: Выполняется fallback на следующего провайдера в цепочке
- **Timeout**: Выполняется fallback на следующего провайдера в цепочке
- **JSON Parse Error**: Выполняется fallback на следующего провайдера в цепочке

**Логирование:**
```json
{
  "event": "llm_fallback",
  "from_provider": "qwen",
  "to_provider": "gemini",
  "reason": "parse_error",
  "role": "Dev",
  "task_id": "task_12345"
}
```

### QA

**Параметры:**
- **Temperature**: 0
- **Max Tokens**: 4096
- **Primary Provider**: qwen
- **Fallback Chain**: gemini
- **Timeout**: 30 секунд

**Поведение при ошибках:**
- **Non-zero RC**: Выполняется fallback на следующего провайдера в цепочке
- **Timeout**: Выполняется fallback на следующего провайдера в цепочке
- **JSON Parse Error**: Выполняется fallback на следующего провайдера в цепочке

**Логирование:**
```json
{
  "event": "llm_fallback",
  "from_provider": "qwen",
  "to_provider": "gemini",
  "reason": "non_zero_rc",
  "role": "QA",
  "task_id": "task_12345"
}
```

### Scribe

**Параметры:**
- **Temperature**: 0
- **Max Tokens**: 4096
- **Primary Provider**: qwen
- **Fallback Chain**: gemini
- **Timeout**: 30 секунд

**Поведение при ошибках:**
- **Non-zero RC**: Выполняется fallback на следующего провайдера в цепочке
- **Timeout**: Выполняется fallback на следующего провайдера в цепочке
- **JSON Parse Error**: Выполняется fallback на следующего провайдера в цепочке

**Логирование:**
```json
{
  "event": "llm_fallback",
  "from_provider": "qwen",
  "to_provider": "gemini",
  "reason": "timeout",
  "role": "Scribe",
  "task_id": "task_12345"
}
```

### Maintainer

**Параметры:**
- **Temperature**: 0.2
- **Max Tokens**: 4096
- **Primary Provider**: claude
- **Fallback Chain**: gpt → gemini
- **Timeout**: 30 секунд

**Поведение при ошибках:**
- **Non-zero RC**: Выполняется fallback на следующего провайдера в цепочке
- **Timeout**: Выполняется fallback на следующего провайдера в цепочке
- **JSON Parse Error**: Выполняется fallback на следующего провайдера в цепочке

**Логирование:**
```json
{
  "event": "llm_fallback",
  "from_provider": "claude",
  "to_provider": "gpt",
  "reason": "non_zero_rc",
  "role": "Maintainer",
  "task_id": "task_12345"
}
```

## Обработка WAIT_BUDGET

При превышении бюджета токенов для роли:

1. Задача переводится в состояние `WAIT_BUDGET`
2. Генерируется событие:
   ```json
   {
     "event": "llm_budget_exceeded",
     "role": "Dev",
     "daily_limit": 500000,
     "used_tokens": 500050,
     "task_id": "task_12345"
   }
   ```
3. Задача остается в очереди до следующего дня или до ручного перевода
4. При возобновлении задача продолжает выполнение с того же места

## Чек-лист негативов

### Сценарий 1: Timeout
- **Описание**: Превышено время ожидания ответа от провайдера
- **Ожидаемое поведение**: Выполняется fallback на следующего провайдера
- **Логирование**: Событие `llm_fallback` с reason="timeout"

### Сценарий 2: Non-zero RC
- **Описание**: Провайдер вернул ненулевой код возврата
- **Ожидаемое поведение**: Выполняется fallback на следующего провайдера
- **Логирование**: Событие `llm_fallback` с reason="non_zero_rc"

### Сценарий 3: JSON Parse Error
- **Описание**: Ответ провайдера не может быть распарсен как JSON
- **Ожидаемое поведение**: Выполняется fallback на следующего провайдера
- **Логирование**: Событие `llm_fallback` с reason="parse_error"

### Сценарий 4: Budget Exceeded
- **Описание**: Превышен дневной лимит токенов для роли
- **Ожидаемое поведение**: Задача переводится в состояние WAIT_BUDGET
- **Логирование**: Событие `llm_budget_exceeded`

### Сценарий 5: Provider Unavailable
- **Описание**: Провайдер временно недоступен
- **Ожидаемое поведение**: Выполняется fallback на следующего провайдера
- **Логирование**: Событие `llm_fallback` с reason="provider_unavailable"

### Сценарий 6: Rate Limit Exceeded
- **Описание**: Превышен лимит запросов к провайдеру
- **Ожидаемое поведение**: Выполняется fallback на следующего провайдера
- **Логирование**: Событие `llm_fallback` с reason="rate_limit_exceeded"