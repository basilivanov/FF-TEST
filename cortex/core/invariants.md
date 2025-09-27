# Cortex Core — Invariants (V2)

## Purpose
Единый, компактный слой инвариантов для всех ролей и узлов. Загружается первым в ContextPackager и имеет высший приоритет.

## Invariants
- SSOT: конфигурации/контракты/документация живут в `cortex/*`; рантайм‑данные — вне SSOT.
- Контракты строго соблюдаются: `artifact_manifest`, `package_contract`, `qa_report` валидируются по схемам.
- Gate: ответы агентов проверяются по ролям и prompt‑hash.
- LLM Router: CLI‑first, fallback по цепочке, бюджеты/таймауты enforce.
- Секреты: только ключи/маски; значений в контексте нет.
- Context Pack: DRY, ≤ ~10KB; роли получают ровно свой слой + scoped docs.

## Ops
- DB: Alembic‑only for schema, WAL per ENV, единый `DATABASE_URL`.
- GitOps: новые работы — всегда через ветку/PR; `main` защищена.
- UI: обращается только к `/api/v1/*` и `/.well-known/ff-context.json`.

