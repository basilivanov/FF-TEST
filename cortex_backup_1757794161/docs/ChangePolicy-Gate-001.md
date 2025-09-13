# Gate Policy — причины REJECT

## Таблица REJECT-кодов (10 примеров)

1. `REJ_NO_MANIFEST` — отсутствует `artifact_manifest`.
2. `REJ_BAD_MANIFEST_SCHEMA` — не проходит схему.
3. `REJ_FORBIDDEN_PATH` — путь вне `tmp/{run_id}/`.
4. `REJ_NO_PACKAGE_CONTRACT` — нет контракта (Architect).
5. `REJ_BAD_DAG` — некорректный `plan.dsl`.
6. `REJ_SECRET_FOUND` — секрет/ключ в тексте файла.
7. `REJ_BROKEN_LINKS` — битые ссылки в доках.
8. `REJ_NO_DOC_UPDATED` — нет события `doc_updated`.
9. `REJ_NO_TESTS` — у QA нет фактических проверок.
10. `REJ_POLICY_VIOLATION` — нарушение Permissions/Context.

Соответствие HTTP: 400/409/422 — в зависимости от причины (см. внутренние маппинги).