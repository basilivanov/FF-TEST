# Политика маршрутизации и бюджетов

* **Маршрут ролей:**
    * Maintainer: [qwen, gemini, stub]
    * Architect: [anthropic_opus41, openai_gpt5_via_codex, gemini_25_pro, qwen_code, stub]
    * Dev: [qwen_code, gemini_25_flash, openai_gpt5_mini, stub]
    * QA: [qwen_code, openai_gpt5_mini, gemini_25_flash, stub]
    * Scribe: [qwen_code, openai_gpt5_mini, stub]
* **Температуры:** Dev/QA/Scribe=0; Architect/Maintainer=0.2.
* Таймауты LLM/HTTP и ретраи — как в Policy-LLM.
* WAIT_BUDGET: при превышении дневного лимита — перевод в `WAIT_BUDGET`; для срочных — дубль task с `provider_override`.

## Метрики / SLO

| Метрика               | Цель  |
| --------------------- | ----- |
| p95 LLM latency       | ≤ 4s  |
| Fallback rate         | < 10% |
| REJECT share (неделя) | < 5%  |
| QA PASS rate          | ≥ 90% |
| E2E success per day   | ≥ 95% |