# A2. Проверка прокси-маршрутов и BasicAuth

## Статус  
**Создано** — 2025-08-23 01:47 UTC

## Анализ nginx конфигурации

### Единый origin
✅ **Проверено:** UI и API работают с одного домена `etl-tst.chococraft.ru`
- Нет кросс-доменных запросов
- Все ресурсы доступны по HTTPS

### BasicAuth Scope Analysis

| Location | Auth Required | Auth File | Challenge Scope |
|----------|---------------|-----------|-----------------|
| `/` (root) | ✅ Yes | `/etc/nginx/.htpasswd` | "Admin Area" |
| `/api/` | ✅ Yes | `/etc/nginx/.htpasswd` | "Admin Area" |
| `/admin` | ✅ Yes | `/etc/nginx/.htpasswd` | "Admin Area" |
| `/assets/*` | ✅ Yes (inherited from root) | `/etc/nginx/.htpasswd` | "Admin Area" |

✅ **Статус:** Единый BasicAuth challenge для всех ресурсов - нет конфликтов авторизации

### Proxy Configuration

| Location | Upstream | Headers Forwarded | Buffering |
|----------|----------|-------------------|-----------|
| `/api/` | `http://127.0.0.1:8081` | ✅ X-Request-ID, X-Forwarded-Proto, Authorization | ✅ OFF (для SSE) |  
| `/admin` | `http://127.0.0.1:8081/admin` | ✅ X-Request-ID, X-Forwarded-Proto, Authorization | Default |

### Специфичные настройки для SSE

```nginx
location /api/ {
    # Для SSE соединений
    proxy_buffering off;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```
✅ **SSE оптимизация:** Отключена буферизация, увеличены таймауты

### Static Files Caching

| File Pattern | Cache Control | Expires |
|--------------|---------------|---------|
| `*.js, *.css, *.png, etc.` | `public, immutable` | `1 year` |
| `/index.html` | `no-store, no-cache, must-revalidate` | No cache |

✅ **Кеширование:** Настроено корректно для SPA

## Проверка фактической работы

### Test 1: Root без авторизации
```bash
$ curl -I https://etl-tst.chococraft.ru/ 2>/dev/null | grep -E "HTTP|WWW-Authenticate"
HTTP/2 401 
WWW-Authenticate: Basic realm="Admin Area"
```
✅ **Ожидаемый 401** с правильным realm

### Test 2: API без авторизации  
```bash
$ curl -I https://etl-tst.chococraft.ru/api/v1/orchestrator/features 2>/dev/null | grep -E "HTTP|WWW-Authenticate"
HTTP/2 401 
WWW-Authenticate: Basic realm="Admin Area"
```
✅ **Ожидаемый 401** с тем же realm (нет двойного challenge)

### Test 3: Авторизованные запросы
```bash
$ curl -u ops:ops123 -I https://etl-tst.chococraft.ru/ 2>/dev/null | head -1
HTTP/2 200

$ curl -u ops:ops123 -I https://etl-tst.chococraft.ru/api/v1/orchestrator/features 2>/dev/null | head -1  
HTTP/2 200
```
✅ **Авторизация проходит** для всех protected location

## Backend connectivity

### FastAPI доступность
```bash  
$ curl -s http://127.0.0.1:8081/api/v1/health | head -20
{"status":"ok"}
```
✅ **Backend отвечает** на прямые запросы

### Headers forwarding test
```bash
$ curl -u ops:ops123 -H "X-Request-ID: test-123" https://etl-tst.chococraft.ru/api/v1/orchestrator/features -I 2>/dev/null | grep -i correlation
x-correlation-id: test-123
```
✅ **Заголовки прокидываются** корректно

## Заключение A2

**Proxy конфигурация корректна:**

✅ **Единый origin и auth:** Нет CORS проблем, один BasicAuth challenge  
✅ **Правильные upstream:** API идет на порт 8081  
✅ **SSE оптимизация:** Отключена буферизация для `/api/`  
✅ **Headers forwarding:** X-Request-ID и Authorization проксируются  
✅ **Static files:** Кеширование настроено правильно для SPA  

**Нет признаков проблем на proxy уровне.** Если есть "Failed to fetch data" в UI, причина в логике приложения или специфичных эндпоинтах.