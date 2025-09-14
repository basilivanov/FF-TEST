# Admin Logging — Runtime Overrides

Эндпоинты администрирования логирования (TEST/PROD с осторожностью).

## Контракт событий

- JSON‑лог, поля: `ts, level, env, component, agent_role, correlation_id, event, kv{}`.
- Редакция секретов выполняется автоматически (token/secret/authorization/password/client_secret → ***).

## Уровни и области

- Глобальный уровень: `LOG_LEVEL` (по умолчанию `INFO`).
- Подсистемы: `LOG_LEVEL_APP`, строка вида `api=DEBUG,orchestrator=INFO,db=WARN` (короткие имена разворачиваются в `app.<name>`).
- Runtime‑оверрайды: применяются без рестарта.

## Эндпоинты

- `POST /api/v1/admin/logging/set-level` (Basic `ADMIN_USERNAME/PASSWORD`, по умолчанию ops/ops123)

```json
{
  "global_level": "INFO",               // опц.
  "modules": {"api": "DEBUG"},         // опц. (короткие имена допустимы)
  "ttl_sec": 900                         // по умолчанию 900 сек
}
```

- `GET /api/v1/admin/logging/state` → активные (не истекшие) оверрайды (истекают по TTL).

## Примеры

- Включить DEBUG на API и GitOps на 15 минут:

```bash
curl -u ops:ops123 -X POST \
  http://127.0.0.1:8081/api/v1/admin/logging/set-level \
  -H 'Content-Type: application/json' \
  -d '{"modules":{"api":"DEBUG","services.git_integration":"DEBUG"},"ttl_sec":900}'
```

- Посмотреть состояние:

```bash
curl -u ops:ops123 http://127.0.0.1:8081/api/v1/admin/logging/state
```

## Практики

- TEST: используйте профили DEBUG с TTL и сэмплингом в шумных местах.
- PROD: точечные оверрайды с малым TTL, DB/LLM не ниже WARN.
- Покрывайте критические пути метриками (`logs_total{component,level,event}`) и не полагайтесь только на логи.

## Переменные окружения (тонкая настройка)

- `LOG_LEVEL` — глобальный уровень (`INFO` по умолчанию).
- `LOG_LEVEL_APP` — уровни по подсистемам, например: `api=DEBUG,orchestrator=INFO,db=WARN`.
- `LOG_DEBUG_SAMPLE_N` — сэмплинг DEBUG (1 из N событий, `1` = без сэмплинга).
- `LOG_WARN_THROTTLE_WINDOW_SEC` — окно подавления повторных WARN (секунды, `0` = выкл.).
