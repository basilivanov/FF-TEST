# Cortex Core — Self-Documenting System

## Автодокументация
- Оркестратор логирует `llm_call_start/end`, `artifact_applied/rejected`, `doc_updated`.
- Scribe получает `artifact_manifest` и формирует дельту в CHANGELOG + обновляет `doc_registry`.
- Prompt drift: валидируется по `configs/prompts.lock.json`, генерируется `prompt_drift_detected`.

## Питание контекста
- ContextPackager собирает слои: core → role → scoped docs → динамика задачи.
- При наличии индекса: `symbol_index`/`call_graph_edges`; иначе — ctags/rg‑fallback.
- Ограничение: ≤ ~10KB, приоритеты — core/invariants > roles > patterns > scoped docs.

