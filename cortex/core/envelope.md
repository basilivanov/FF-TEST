# Cortex Core — Router Envelope

Единый формат обёртки промпта для Router.

## Sections
- <role>: Architect|Dev|QA|Scribe|Maintainer
- <context>:
  - <system_knowledge> (core/ + role + scoped docs)
  - <user_intent>
  - <previous_steps>
- <task> (DSL/task packet)
- <rules> (positive/negative)
- <output_format> (ссылка на core/output_formats.md + схемы)
- <thinking> (опц.)
- <code> (финальный результат по контракту роли)

## Errors
- При нехватке контекста агент возвращает: `{ "error": "NeedContext", "missing": [ ... ] }`.

