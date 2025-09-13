# Comprehensive Agent Test Report

## Test Summary
- **Correlation ID**: COMPREHENSIVE_TEST_1757741578
- **Execution Time**: 87.70 seconds
- **Test Date**: 2025-09-13T08:34:26.094037

## Role Testing Results (2/5 passed)
- **Architect**: ✅ (anthropic_opus41, 11433ms)
- **Dev**: ❌ (None, 2020ms)
  - Error: All providers failed for role Dev. Last error: CLI command failed with return code 1: Usage: gemini [options] [command]

Gemini CLI - Launch an interactive CLI, use -p/--prompt for non-interactive mode

Commands:
  gemini      Launch Gemini CLI  [default]
  gemini mcp  Manage MCP servers

Options:
  -m, --model                     Model  [string]
  -p, --prompt                    Prompt. Appended to input on stdin (if any).  [string]
  -i, --prompt-interactive        Execute the provided prompt and continue in interactive mode  [string]
  -s, --sandbox                   Run in sandbox?  [boolean]
      --sandbox-image             Sandbox image URI.  [string]
  -d, --debug                     Run in debug mode?  [boolean] [default: false]
  -a, --all-files                 Include ALL files in context?  [boolean] [default: false]
      --show-memory-usage         Show memory usage in status bar  [boolean] [default: false]
  -y, --yolo                      Automatically accept all actions (aka YOLO mode, see https://www.youtube.com/watch?v=xvFZjo5PgG0 for more details)?  [boolean] [default: false]
      --approval-mode             Set the approval mode: default (prompt for approval), auto_edit (auto-approve edit tools), yolo (auto-approve all tools)  [string] [choices: "default", "auto_edit", "yolo"]
      --telemetry                 Enable telemetry? This flag specifically controls if telemetry is sent. Other --telemetry-* flags set specific values but do not enable telemetry on their own.  [boolean]
      --telemetry-target          Set the telemetry target (local or gcp). Overrides settings files.  [string] [choices: "local", "gcp"]
      --telemetry-otlp-endpoint   Set the OTLP endpoint for telemetry. Overrides environment variables and settings files.  [string]
      --telemetry-otlp-protocol   Set the OTLP protocol for telemetry (grpc or http). Overrides settings files.  [string] [choices: "grpc", "http"]
      --telemetry-log-prompts     Enable or disable logging of user prompts for telemetry. Overrides settings files.  [boolean]
      --telemetry-outfile         Redirect all telemetry output to the specified file.  [string]
  -c, --checkpointing             Enables checkpointing of file edits  [boolean] [default: false]
      --experimental-acp          Starts the agent in ACP mode  [boolean]
      --allowed-mcp-server-names  Allowed MCP server names  [array]
      --allowed-tools             Tools that are allowed to run without confirmation  [array]
  -e, --extensions                A list of extensions to use. If not provided, all extensions are used.  [array]
  -l, --list-extensions           List all available extensions and exit.  [boolean]
      --proxy                     Proxy for gemini client, like schema://user:password@host:port  [string]
      --include-directories       Additional directories to include in the workspace (comma-separated or multiple --include-directories)  [array]
      --screen-reader             Enable screen reader mode for accessibility.  [boolean] [default: false]
  -v, --version                   Show version number  [boolean]
  -h, --help                      Show help  [boolean]

Unknown argument: bash

- **QA**: ❌ (None, 1966ms)
  - Error: CLI command failed with return code 1: Usage: gemini [options] [command]

Gemini CLI - Launch an interactive CLI, use -p/--prompt for non-interactive mode

Commands:
  gemini      Launch Gemini CLI  [default]
  gemini mcp  Manage MCP servers

Options:
  -m, --model                     Model  [string]
  -p, --prompt                    Prompt. Appended to input on stdin (if any).  [string]
  -i, --prompt-interactive        Execute the provided prompt and continue in interactive mode  [string]
  -s, --sandbox                   Run in sandbox?  [boolean]
      --sandbox-image             Sandbox image URI.  [string]
  -d, --debug                     Run in debug mode?  [boolean] [default: false]
  -a, --all-files                 Include ALL files in context?  [boolean] [default: false]
      --show-memory-usage         Show memory usage in status bar  [boolean] [default: false]
  -y, --yolo                      Automatically accept all actions (aka YOLO mode, see https://www.youtube.com/watch?v=xvFZjo5PgG0 for more details)?  [boolean] [default: false]
      --approval-mode             Set the approval mode: default (prompt for approval), auto_edit (auto-approve edit tools), yolo (auto-approve all tools)  [string] [choices: "default", "auto_edit", "yolo"]
      --telemetry                 Enable telemetry? This flag specifically controls if telemetry is sent. Other --telemetry-* flags set specific values but do not enable telemetry on their own.  [boolean]
      --telemetry-target          Set the telemetry target (local or gcp). Overrides settings files.  [string] [choices: "local", "gcp"]
      --telemetry-otlp-endpoint   Set the OTLP endpoint for telemetry. Overrides environment variables and settings files.  [string]
      --telemetry-otlp-protocol   Set the OTLP protocol for telemetry (grpc or http). Overrides settings files.  [string] [choices: "grpc", "http"]
      --telemetry-log-prompts     Enable or disable logging of user prompts for telemetry. Overrides settings files.  [boolean]
      --telemetry-outfile         Redirect all telemetry output to the specified file.  [string]
  -c, --checkpointing             Enables checkpointing of file edits  [boolean] [default: false]
      --experimental-acp          Starts the agent in ACP mode  [boolean]
      --allowed-mcp-server-names  Allowed MCP server names  [array]
      --allowed-tools             Tools that are allowed to run without confirmation  [array]
  -e, --extensions                A list of extensions to use. If not provided, all extensions are used.  [array]
  -l, --list-extensions           List all available extensions and exit.  [boolean]
      --proxy                     Proxy for gemini client, like schema://user:password@host:port  [string]
      --include-directories       Additional directories to include in the workspace (comma-separated or multiple --include-directories)  [array]
      --screen-reader             Enable screen reader mode for accessibility.  [boolean] [default: false]
  -v, --version                   Show version number  [boolean]
  -h, --help                      Show help  [boolean]

Unknown argument: bash

- **Scribe**: ❌ (None, 965ms)
  - Error: All providers failed for role Scribe. Last error: CLI command failed with return code 1: Usage: qwen [options] [command]

Qwen Code - Launch an interactive CLI, use -p/--prompt for non-interactive mode

Commands:
  qwen      Launch Qwen Code  [default]
  qwen mcp  Manage MCP servers

Options:
  -m, --model                     Model  [string]
  -p, --prompt                    Prompt. Appended to input on stdin (if any).  [string]
  -i, --prompt-interactive        Execute the provided prompt and continue in interactive mode  [string]
  -s, --sandbox                   Run in sandbox?  [boolean]
      --sandbox-image             Sandbox image URI.  [string]
  -d, --debug                     Run in debug mode?  [boolean] [default: false]
  -a, --all-files                 Include ALL files in context?  [boolean] [default: false]
      --all_files                 Include ALL files in context?  [deprecated: Use --all-files instead. We will be removing --all_files in the coming weeks.] [boolean] [default: false]
      --show-memory-usage         Show memory usage in status bar  [boolean] [default: false]
      --show_memory_usage         Show memory usage in status bar  [deprecated: Use --show-memory-usage instead. We will be removing --show_memory_usage in the coming weeks.] [boolean] [default: false]
  -y, --yolo                      Automatically accept all actions (aka YOLO mode, see https://www.youtube.com/watch?v=xvFZjo5PgG0 for more details)?  [boolean] [default: false]
      --approval-mode             Set the approval mode: default (prompt for approval), auto_edit (auto-approve edit tools), yolo (auto-approve all tools)  [string] [choices: "default", "auto_edit", "yolo"]
      --telemetry                 Enable telemetry? This flag specifically controls if telemetry is sent. Other --telemetry-* flags set specific values but do not enable telemetry on their own.  [boolean]
      --telemetry-target          Set the telemetry target (local or gcp). Overrides settings files.  [string] [choices: "local", "gcp"]
      --telemetry-otlp-endpoint   Set the OTLP endpoint for telemetry. Overrides environment variables and settings files.  [string]
      --telemetry-otlp-protocol   Set the OTLP protocol for telemetry (grpc or http). Overrides settings files.  [string] [choices: "grpc", "http"]
      --telemetry-log-prompts     Enable or disable logging of user prompts for telemetry. Overrides settings files.  [boolean]
      --telemetry-outfile         Redirect all telemetry output to the specified file.  [string]
  -c, --checkpointing             Enables checkpointing of file edits  [boolean] [default: false]
      --experimental-acp          Starts the agent in ACP mode  [boolean]
      --allowed-mcp-server-names  Allowed MCP server names  [array]
  -e, --extensions                A list of extensions to use. If not provided, all extensions are used.  [array]
  -l, --list-extensions           List all available extensions and exit.  [boolean]
      --proxy                     Proxy for qwen client, like schema://user:password@host:port  [string]
      --include-directories       Additional directories to include in the workspace (comma-separated or multiple --include-directories)  [array]
      --openai-logging            Enable logging of OpenAI API calls for debugging and analysis  [boolean]
      --openai-api-key            OpenAI API key to use for authentication  [string]
      --openai-base-url           OpenAI base URL (for custom endpoints)  [string]
      --tavily-api-key            Tavily API key for web search functionality  [string]
  -v, --version                   Show version number  [boolean]
  -h, --help                      Show help  [boolean]

Unknown arguments: color, quiet, bash, run

- **Maintainer**: ✅ (anthropic_opus41, 9790ms)

## Provider Authorization Results (4/5 passed)
- **anthropic_opus41**: ✅
- **openai_gpt5_via_codex**: ✅
- **gemini_25_pro**: ✅
- **gemini_25_flash**: ✅
- **qwen_code**: ❌
  - Error: All providers failed for role Dev. Last error: CLI command failed with return code 1: Usage: gemini [options] [command]

Gemini CLI - Launch an interactive CLI, use -p/--prompt for non-interactive mode

Commands:
  gemini      Launch Gemini CLI  [default]
  gemini mcp  Manage MCP servers

Options:
  -m, --model                     Model  [string]
  -p, --prompt                    Prompt. Appended to input on stdin (if any).  [string]
  -i, --prompt-interactive        Execute the provided prompt and continue in interactive mode  [string]
  -s, --sandbox                   Run in sandbox?  [boolean]
      --sandbox-image             Sandbox image URI.  [string]
  -d, --debug                     Run in debug mode?  [boolean] [default: false]
  -a, --all-files                 Include ALL files in context?  [boolean] [default: false]
      --show-memory-usage         Show memory usage in status bar  [boolean] [default: false]
  -y, --yolo                      Automatically accept all actions (aka YOLO mode, see https://www.youtube.com/watch?v=xvFZjo5PgG0 for more details)?  [boolean] [default: false]
      --approval-mode             Set the approval mode: default (prompt for approval), auto_edit (auto-approve edit tools), yolo (auto-approve all tools)  [string] [choices: "default", "auto_edit", "yolo"]
      --telemetry                 Enable telemetry? This flag specifically controls if telemetry is sent. Other --telemetry-* flags set specific values but do not enable telemetry on their own.  [boolean]
      --telemetry-target          Set the telemetry target (local or gcp). Overrides settings files.  [string] [choices: "local", "gcp"]
      --telemetry-otlp-endpoint   Set the OTLP endpoint for telemetry. Overrides environment variables and settings files.  [string]
      --telemetry-otlp-protocol   Set the OTLP protocol for telemetry (grpc or http). Overrides settings files.  [string] [choices: "grpc", "http"]
      --telemetry-log-prompts     Enable or disable logging of user prompts for telemetry. Overrides settings files.  [boolean]
      --telemetry-outfile         Redirect all telemetry output to the specified file.  [string]
  -c, --checkpointing             Enables checkpointing of file edits  [boolean] [default: false]
      --experimental-acp          Starts the agent in ACP mode  [boolean]
      --allowed-mcp-server-names  Allowed MCP server names  [array]
      --allowed-tools             Tools that are allowed to run without confirmation  [array]
  -e, --extensions                A list of extensions to use. If not provided, all extensions are used.  [array]
  -l, --list-extensions           List all available extensions and exit.  [boolean]
      --proxy                     Proxy for gemini client, like schema://user:password@host:port  [string]
      --include-directories       Additional directories to include in the workspace (comma-separated or multiple --include-directories)  [array]
      --screen-reader             Enable screen reader mode for accessibility.  [boolean] [default: false]
  -v, --version                   Show version number  [boolean]
  -h, --help                      Show help  [boolean]

Unknown argument: bash


## Full Feature Test
- **Status**: ✅ SUCCESS
- **Feature ID**: 17
- **Final Status**: DONE
- **Execution Time**: 20.02s
- **Feature ID**: 17

## System Health
- **LLM Router**: ✅ Working
- **Provider Auth**: ✅ Working
- **Orchestrator**: ✅ Working

## Recommendations
- Fix failed role configurations
- Check provider authorization credentials

## Artifacts Location
All test artifacts saved to: /opt/feature-factory/artifacts/COMPREHENSIVE_TEST/COMPREHENSIVE_TEST_1757741578

---
**Test completed at 2025-09-13T08:34:26.094096**
