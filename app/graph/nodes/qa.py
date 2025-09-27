#!/usr/bin/env python3
"""
Узел QA для графа G1.
"""

import asyncio
import os
from pathlib import Path
import subprocess
import structlog
import json
import re
import uuid
import yaml
from typing import Dict, Any
from app.graph.types import RunCtx
from app.llm.router import completion
from app.logging_helpers import log, get_env

# Настройка логгера
logger = structlog.get_logger()

async def qa_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Узел QA - выполняет статический анализ и тесты.
    """
    logger.debug("Вход в узел QA", state=state)
    try:
        run_ctx = state.get("run_ctx")
        if not run_ctx:
            raise ValueError("Run context not found in state")

        feature_id = run_ctx.feature_id
        correlation_id = run_ctx.correlation_id
        run_id = run_ctx.run_id

        logger.info(
            "qa_node_started",
            component="graph",
            agent_role="QA",
            run_id=run_id,
            feature_id=feature_id,
            correlation_id=correlation_id
        )

        # Получаем данные от узла Dev
        artifacts_dir = state.get("artifacts_dir")
        artifact_manifest = state.get("artifact_manifest")
        package_contract = state.get("package_contract")

        if not artifacts_dir or not artifact_manifest or not package_contract:
            logger.error(
                "qa_node_missing_artifacts_or_manifest",
                component="graph",
                agent_role="QA",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id
            )
            return {
                "status": "qa_failed",
                "result": "Missing artifacts, manifest or package contract from Dev node"
            }

        # 1. Получить код для тестирования
        code_to_test = ""
        for file_name in artifact_manifest.get("files", []):
            file_path = os.path.join(artifacts_dir, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code_to_test += f.read() + "\n\n"
        
        if not code_to_test:
            logger.error(
                "qa_node_no_code_to_test",
                component="graph",
                agent_role="QA",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id
            )
            return {
                "status": "qa_failed",
                "result": "No code found to test"
            }

        # 2. Сгенерировать тесты с помощью LLM
        system_prompt = """Ты QA-инженер. Твоя задача - сгенерировать pytest тесты для предоставленного Python кода.
Тесты должны быть полными, покрывать основные сценарии и граничные случаи.
Верни только Python код тестов в fenced-блоке.
"""
        user_prompt = f"""Сгенерируй pytest тесты для следующего кода:

```python
{code_to_test}
```

Учитывай следующий package_contract:
```json
{json.dumps(package_contract, indent=2)}
```
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            llm_role = "test_QA" if os.getenv("TEST_MODE") == "true" else "QA"
            llm_response = completion(
                role=llm_role,
                messages=messages,
                max_tokens=2000, # Установить адекватное значение
                temperature=0.7,
                timeout_s=120
            )
            test_code_text = llm_response.get("text", "")
            if not test_code_text and 'choices' in llm_response:
                try:
                    test_code_text = llm_response['choices'][0]['message']['content']
                except Exception:
                    test_code_text = ""
            
            # Извлекаем только код из fenced-блока
            match = re.search(r'```python\s*\n(.*?)\n```', test_code_text, re.DOTALL)
            if match:
                test_code_text = match.group(1)
            else:
                logger.warning(
                    "qa_node_llm_no_fenced_code",
                    component="graph",
                    agent_role="QA",
                    run_id=run_id,
                    feature_id=feature_id,
                    correlation_id=correlation_id,
                    llm_response_preview=test_code_text[:200]
                )
                # Если LLM не вернул fenced-блок, используем весь текст как код
                pass # test_code_text уже содержит весь текст

            if not test_code_text.strip():
                logger.error(
                    "qa_node_llm_no_test_code",
                    component="graph",
                    agent_role="QA",
                    run_id=run_id,
                    feature_id=feature_id,
                    correlation_id=correlation_id
                )
                return {
                    "status": "qa_failed",
                    "result": "LLM failed to generate test code"
                }

        except Exception as llm_error:
            logger.error(
                "qa_node_llm_test_generation_failed",
                component="graph",
                agent_role="QA",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id,
                error=str(llm_error)
            )
            return {
                "status": "qa_failed",
                "result": f"LLM failed to generate tests: {str(llm_error)}"
            }

        # 3. Сохранить тесты
        test_file_path = os.path.join(artifacts_dir, "test_generated.py")
        with open(test_file_path, "w", encoding='utf-8') as f:
            f.write(test_code_text)

        # 4. Запустить тесты (pytest)
        qa_report_path = os.path.join(artifacts_dir, "qa_report.json")
        try:
            # Используем pytest из виртуального окружения, если доступен
            pytest_bin = "/opt/feature-factory/.venv/bin/pytest"
            if not (Path(pytest_bin).exists() and os.access(pytest_bin, os.X_OK)):
                pytest_bin = "pytest"

            pytest_command = [
                pytest_bin,
                "--json-report",
                f"--json-report-file={qa_report_path}",
                "-q",
                "."
            ]
            
            # Добавляем путь к тестируемому коду в PYTHONPATH
            env = os.environ.copy()
            project_root = "/opt/feature-factory"
            prev = env.get("PYTHONPATH", "")
            parts = [artifacts_dir, project_root] + ([prev] if prev else [])
            env["PYTHONPATH"] = ":".join([p for p in parts if p])

            result = subprocess.run(
                pytest_command,
                cwd=artifacts_dir, # Запускаем pytest в каталоге с артефактами
                capture_output=True,
                text=True,
                timeout=180, # Увеличиваем таймаут для тестов
                env=env
            )

            # Логируем stdout/stderr pytest
            logger.info(
                "pytest_execution_output",
                run_id=run_id,
                feature_id=feature_id,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode
            )

        except subprocess.CalledProcessError as e:
            logger.error(
                "qa_node_pytest_failed_execution",
                component="graph",
                agent_role="QA",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id,
                error=str(e),
                stdout=e.stdout,
                stderr=e.stderr
            )
            return {
                "status": "qa_failed",
                "result": f"Pytest execution failed: {str(e)}"
            }
        except subprocess.TimeoutExpired as e:
            logger.error(
                "qa_node_pytest_timeout",
                component="graph",
                agent_role="QA",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id,
                error=str(e),
                stdout=e.stdout,
                stderr=e.stderr
            )
            return {
                "status": "qa_failed",
                "result": "Pytest execution timed out"
            }
        except Exception as e:
            logger.error(
                "qa_node_pytest_unexpected_error",
                component="graph",
                agent_role="QA",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id,
                error=str(e)
            )
            # продолжаем формировать отчёт ниже

        # 5. Сформировать отчет QA
        qa_report = {"cases": [], "pass": 0, "fail": []}
        overall_qa_result = "FAIL" # По умолчанию FAIL

        if os.path.exists(qa_report_path):
            try:
                with open(qa_report_path, 'r', encoding='utf-8') as f:
                    pytest_json_report = json.load(f)
                
                # Парсим отчет pytest в qa_report.json
                for test_case in pytest_json_report.get("test_cases", []):
                    case_status = "FAIL"
                    if test_case.get("outcome") == "passed":
                        case_status = "PASS"
                        qa_report["pass"] += 1
                    elif test_case.get("outcome") == "skipped":
                        case_status = "SKIP"
                    else:
                        qa_report["fail"].append(test_case.get("nodeid", "unknown_test"))

                    qa_report["cases"].append({
                        "id": test_case.get("nodeid", str(uuid.uuid4())),
                        "name": test_case.get("name", "unknown_test"),
                        "status": case_status,
                        "notes": test_case.get("call", {}).get("longrepr", "")
                    })
                
                if qa_report["pass"] > 0 and not qa_report["fail"]:
                    overall_qa_result = "PASS"

            except Exception as e:
                logger.error(
                    "qa_node_report_parsing_failed",
                    component="graph",
                    agent_role="QA",
                    run_id=run_id,
                    feature_id=feature_id,
                    correlation_id=correlation_id,
                    error=str(e)
                )
                qa_report["fail"].append("report_parsing_error")
        else:
            logger.warning(
                "qa_node_report_file_not_found",
                component="graph",
                agent_role="QA",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id
            )
            qa_report["fail"].append("no_report_file")

        # Валидация отчёта по JSON‑схеме (если доступна)
        try:
            from app.orchestrator.gates import ManifestValidator
            mv = ManifestValidator()
            _ = mv.validate_qa_report(qa_report)
            if not _:
                overall_qa_result = "FAIL"
        except Exception:
            pass

        logger.info(
            "qa_node_finished",
            component="graph",
            agent_role="QA",
            run_id=run_id,
            feature_id=feature_id,
            correlation_id=correlation_id,
            qa_result=overall_qa_result,
            qa_report=qa_report
        )

        # Если тесты провалены — подготовим запись для Watchdog (tool_errors + escalation_context)
        watchdog_payload = {}
        if overall_qa_result != "PASS":
            failed = qa_report.get("fail", []) or []
            ctx_lines = ["Отчёт о провале тестов (QA):"]
            for name in failed[:10]:
                ctx_lines.append(f"- Тест провален: {name}")
            escalation_context = "\n".join(ctx_lines)
            watchdog_payload = {
                "tool_errors": [{
                    "tool_name": "qa_tests",
                    "error_type": "TestsFailed",
                    "error_message": escalation_context,
                }],
                "escalation_context": escalation_context,
            }

        result_state = {
            "status": "qa_completed",
            "result": "QA testing completed",
            "qa_result": overall_qa_result,
            "qa_report": qa_report,
            "artifacts_dir": artifacts_dir
        }
        result_state.update(watchdog_payload)
        return result_state

    except Exception as e:
        logger.error(
            "qa_node_failed",
            component="graph",
            agent_role="QA",
            err_type=type(e).__name__,
            error=str(e),
            run_id=state.get("run_ctx").run_id if state.get("run_ctx") else "unknown"
        )
        return {
            "status": "qa_failed",
            "result": f"QA node failed: {str(e)}"
        }
