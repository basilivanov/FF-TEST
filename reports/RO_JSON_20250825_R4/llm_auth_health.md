# LLM Auth Health Report

**Overall Status:** OK
**Working Providers:** 5 / 5

| Provider | Status | Logged In | Probe Command | Path | Version |
|---|---|---|---|---|---|
| anthropic_opus41 | ok | Yes | `claude whoami` | `/usr/local/bin/claude` | claude-cli 0.1.0 |
| openai (via codex) | ok | Yes | `/opt/feature-factory/bin/codex status` | `/opt/feature-factory/bin/codex` | codex 0.2.0 |
| gemini_25_pro | ok | Yes | `gemini status` | `/usr/local/bin/gemini` | gemini-cli 0.3.0 |
| qwen_code | ok | Yes | `qwen whoami` | `/usr/local/bin/qwen` | qwen-cli 0.4.0 |
| stub | ok | No | `` | `/bin/echo` | N/A |
