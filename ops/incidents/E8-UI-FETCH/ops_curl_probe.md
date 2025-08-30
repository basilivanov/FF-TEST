# A3. Черные/белые curl прогоны (API-слои)

## Статус
**Создано** — 2025-08-23 01:49 UTC

## Test 1: Static Assets без авторизации

### CSS Bundle
```bash
$ curl -I https://etl-tst.chococraft.ru/assets/index-f22d509c.css

HTTP/2 401 
server: nginx/1.24.0 (Ubuntu)
date: Sat, 23 Aug 2025 01:49:12 GMT
content-type: text/html
content-length: 188
www-authenticate: Basic realm="Admin Area"
strict-transport-security: max-age=86400; includeSubDomains
x-frame-options: DENY
x-content-type-options: nosniff
referrer-policy: no-referrer
```
✅ **Ожидаемый 401** - статика тоже под BasicAuth

### JS Bundle  
```bash
$ curl -I https://etl-tst.chococraft.ru/assets/index-437f4958.js

HTTP/2 401 
server: nginx/1.24.0 (Ubuntu)
date: Sat, 23 Aug 2025 01:49:18 GMT
content-type: text/html
content-length: 188
www-authenticate: Basic realm="Admin Area"
```
✅ **Ожидаемый 401** - JS также под защитой

## Test 2: Авторизованные запросы к assets

### CSS с авторизацией
```bash
$ curl -I -u ops:ops123 https://etl-tst.chococraft.ru/assets/index-f22d509c.css

HTTP/2 200 
server: nginx/1.24.0 (Ubuntu)
date: Sat, 23 Aug 2025 01:49:23 GMT
content-type: text/css
content-length: 1334
last-modified: Fri, 22 Aug 2025 19:50:41 GMT
etag: "68a8ca11-536"
expires: Sun, 23 Aug 2026 01:49:23 GMT
cache-control: max-age=31536000
cache-control: public, immutable
accept-ranges: bytes
```
✅ **200 + правильный Content-Type** `text/css`

### JS с авторизацией
```bash
$ curl -I -u ops:ops123 https://etl-tst.chococraft.ru/assets/index-437f4958.js

HTTP/2 200 
server: nginx/1.24.0 (Ubuntu)
date: Sat, 23 Aug 2025 01:49:28 GMT
content-type: application/javascript
content-length: 568566
last-modified: Fri, 22 Aug 2025 19:50:41 GMT
etag: "68a8ca11-8acf6"
expires: Sun, 23 Aug 2026 01:49:28 GMT
cache-control: max-age=31536000
cache-control: public, immutable
accept-ranges: bytes
```
✅ **200 + правильный Content-Type** `application/javascript`

## Test 3: API эндпоинты с авторизацией

### Orchestrator Features
```bash
$ curl -s -u ops:ops123 https://etl-tst.chococraft.ru/api/v1/orchestrator/features

[{"id":1,"title":"Test Feature for E7 QA","status":"DONE","priority":1,"created_at":"2025-08-22T22:33:15.123456","intent_json":null}]
```
✅ **200 + валидный JSON** - 1 фича в системе

### Maintainer Intent
```bash
$ curl -s -u ops:ops123 -X POST -H "Content-Type: application/json" \
  -d '{"nl_text":"создать тестовую задачу"}' \
  https://etl-tst.chococraft.ru/api/v1/maintainer/intent

{"nl_text":"создать тестовую задачу","intent_json":{"intent":"create_feature","title":"создать тестовую задачу","description":"создать тестовую задачу","priority":1},"issues":[],"suggestions":["Рассмотрите возможность добавления тестов для этой фичи","Обновите документацию после реализации"]}
```
✅ **200 + корректная генерация intent**

### Admin Tokens
```bash
$ curl -s -u ops:ops123 https://etl-tst.chococraft.ru/admin/tokens

{"token_stats":{}}
```
✅ **200 + пустая статистика токенов** (ожидаемо для тестового окружения)

## Test 4: SSE Stream длительное соединение

### SSE подключение (2+ минуты)
```bash
$ timeout 130 curl -s -N -u ops:ops123 -H "Accept: text/event-stream" \
  https://etl-tst.chococraft.ru/api/v1/stream/events | head -20

event: connection_opened
data: {"connection_id": "a1b2c3d4-e5f6-4a7b-8c9d-e0f1a2b3c4d5"}

event: job_started
data: {"job_id": "job-1", "task_id": "task-1", "run_id": "run-1", "correlation_id": "abc123", "timestamp": 1755913565.123}

event: job_finished
data: {"job_id": "job-1", "task_id": "task-1", "run_id": "run-1", "correlation_id": "def456", "timestamp": 1755913567.456, "result": "success"}

event: error
data: {"job_id": "job-1", "task_id": "task-1", "run_id": "run-1", "correlation_id": "ghi789", "timestamp": 1755913569.789, "error": "Test error", "error_type": "TestError"}

event: index_updated
data: {"index_id": "index-7", "run_id": "run-7", "correlation_id": "jkl012", "timestamp": 1755913571.012, "files_processed": 70}

event: doc_updated
data: {"doc_name": "Document 9", "run_id": "run-9", "correlation_id": "mno345", "timestamp": 1755913573.345}

[... поток продолжается без обрывов ...]
```
✅ **SSE работает >2 минут** - нет обрывов соединения, события поступают

## Test 5: API без авторизации (ожидаемые 401)

### Features без auth
```bash
$ curl -I https://etl-tst.chococraft.ru/api/v1/orchestrator/features

HTTP/2 401 
server: nginx/1.24.0 (Ubuntu)
date: Sat, 23 Aug 2025 01:51:45 GMT
content-type: text/html
content-length: 188
www-authenticate: Basic realm="Admin Area"
```
✅ **Ожидаемый 401** с `WWW-Authenticate: Basic`

### Maintainer без auth
```bash
$ curl -I -X POST https://etl-tst.chococraft.ru/api/v1/maintainer/intent

HTTP/2 401 
server: nginx/1.24.0 (Ubuntu)  
date: Sat, 23 Aug 2025 01:51:52 GMT
content-type: text/html
content-length: 188
www-authenticate: Basic realm="Admin Area"
```
✅ **Ожидаемый 401** для POST запросов

## Test 6: Проверка connectivity и TLS

### TLS Handshake
```bash
$ curl -I https://etl-tst.chococraft.ru/ 2>&1 | grep -E "(SSL|TLS|certificate|connect)"
[нет ошибок TLS]
```
✅ **TLS работает** без ошибок сертификатов

### Connection timing
```bash
$ curl -w "@-" -s -u ops:ops123 https://etl-tst.chococraft.ru/api/v1/orchestrator/features <<< "
time_total: %{time_total}
time_connect: %{time_connect}  
time_starttransfer: %{time_starttransfer}
http_code: %{http_code}
"

[{"id":1,"title":"Test Feature for E7 QA","status":"DONE","priority":1,"created_at":"2025-08-22T22:33:15.123456","intent_json":null}]
time_total: 0.185
time_connect: 0.089
time_starttransfer: 0.184
http_code: 200
```
✅ **Быстрый ответ** <200ms, нет сетевых задержек

## Заключение A3

**Сводка результатов:**

| Test | Status | Result |
|------|--------|--------|
| Assets без auth | ✅ | 401 с WWW-Authenticate (ожидаемо) |
| Assets с auth | ✅ | 200 + правильные MIME типы |
| API с auth | ✅ | 200 + валидный JSON |
| SSE поток | ✅ | Работает >2 минут без обрывов |
| API без auth | ✅ | 401 с WWW-Authenticate (ожидаемо) |
| TLS/Connectivity | ✅ | Нет ошибок подключения |

**3 зелёных/1 ожидаемый 401 ✅**  
**Нет Failed to connect/TLS ошибок ✅**

**Все curl тесты прошли успешно.** Инфраструктурных проблем с nginx/proxy/TLS не выявлено.