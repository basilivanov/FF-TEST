import os
import yaml
from typing import List, Dict, Any, TypedDict

try:
    from app.logging_helpers import log
except ImportError:
    import logging
    log = logging.getLogger(__name__)

# This is a forward declaration. The actual GraphState will be imported from the graph definition.
class GraphState(TypedDict, total=False):
    tool_errors: List[Dict[str, Any]]
    watchdog_failures: List[Dict[str, Any]]
    escalation_context: str
    watchdog_decision: str
    run_id: str
    task_id: str
    correlation_id: str

CONFIG_PATH = "/opt/feature-factory/configs/watchdog_policy.yaml"

def _load_policy() -> Dict[str, Any]:
    """Loads the watchdog policy from the YAML file."""
    try:
        if not os.path.exists(CONFIG_PATH):
            log.error(event="watchdog_policy_not_found", path=CONFIG_PATH)
            return {}
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        log.error(event="watchdog_policy_load_failed", error=str(e))
        return {}

def watchdog_check_node(state: GraphState) -> Dict[str, Any]:
    """
    Analyzes the state for consecutive failures and decides whether to escalate.
    This node is part of the graph and receives the current state.
    Based on the analysis, it returns a dictionary with updates to the state.
    """
    policy = _load_policy()
    watchdog_policy = policy.get("watchdog", {})

    if not watchdog_policy.get("enabled", False):
        return {"watchdog_decision": "CONTINUE"}

    new_errors = state.get("tool_errors", [])
    # Ensure watchdog_failures is a list before concatenation
    all_failures = state.get("watchdog_failures", []) + new_errors

    updated_state = {"watchdog_failures": all_failures}

    trigger_policy = next((t for t in watchdog_policy.get("triggers", []) if t.get("type") == "consecutive_tool_failures"), None)

    if not trigger_policy or not new_errors:
        updated_state["watchdog_decision"] = "CONTINUE"
        return updated_state

    threshold = trigger_policy.get("threshold", 3)

    if len(all_failures) < threshold:
        updated_state["watchdog_decision"] = "CONTINUE"
        return updated_state

    last_n_failures = all_failures[-threshold:]

    # To be considered identical, errors must originate from the same tool (or any tool if not specified)
    # and have the same error type.
    first_error_in_sequence = last_n_failures[0]
    
    # The error message itself is used for creating the context, but not for the identity check.
    # The "identity" is based on a more abstract error_type.
    is_consecutive_identical = all(
        err.get("tool_name") == first_error_in_sequence.get("tool_name") and
        err.get("error_type") == first_error_in_sequence.get("error_type")
        for err in last_n_failures
    )

    if is_consecutive_identical:
        log.warning(
            event="watchdog_triggered",
            run_id=state.get("run_id"),
            task_id=state.get("task_id"),
            correlation_id=state.get("correlation_id"),
            kv={
                "threshold": threshold,
                "failures": [{"tool": err.get("tool_name"), "type": err.get("error_type")} for err in last_n_failures],
            }
        )

        escalation_context_str = "Контекст предыдущих ошибок:\n"
        for i, err in enumerate(last_n_failures, 1):
            escalation_context_str += f"{i}. Инструмент: {err.get('tool_name', 'N/A')}, Ошибка: {err.get('error_message', 'N/A')}\n"

        updated_state["escalation_context"] = escalation_context_str
        updated_state["watchdog_decision"] = "ESCALATE_L1"

        log.info(
            event="task_escalated",
            run_id=state.get("run_id"),
            task_id=state.get("task_id"),
            correlation_id=state.get("correlation_id"),
            kv={"level": 1, "action": "retry_with_error_context"}
        )
    else:
        updated_state["watchdog_decision"] = "CONTINUE"

    return updated_state