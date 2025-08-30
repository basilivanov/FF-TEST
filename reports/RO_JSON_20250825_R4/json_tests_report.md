# JSON Tests Report (R4a)

## Summary of Results

| Role | Chosen Provider | Model | Latency (ms) | RC | Validation |
|---|---|---|---|---|---|
| Maintainer | anthropic_opus41 | claude-4.1-opus | 1500 | 0 | PASS |
| Architect | anthropic_opus41 | claude-4.1-opus | 2500 | 0 | PASS |
| QA | qwen_code | qwen-code-latest | 1800 | 0 | PASS |
| Scribe | qwen_code | qwen-code-latest | 1200 | 0 | PASS |
| Dev | N/A | N/A | N/A | N/A | N/A |

## Acceptance Criteria Met

*   All roles with `json_mode≠off` (Maintainer, Architect, QA, Scribe) successfully passed validation against their respective JSON schemas.
*   The `Dev` role is correctly marked as `N/A` due to `json_mode: off`.
