#!/usr/bin/env python3
"""
Узел SpecSynth: синтезирует формальную спецификацию/оракулы из intent фичи
и сохраняет артефакт architect_spec.json в каталоге артефактов ран-а.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict

import structlog
from sqlalchemy import text

from app.graph.types import RunCtx
from app.db.session import get_db
from app.logging_helpers import get_env

logger = structlog.get_logger()


def _ensure_artifacts_dir(state: Dict[str, Any]) -> str:
    run_ctx = state.get("run_ctx")
    run_id = run_ctx.run_id if run_ctx else uuid.uuid4().hex
    artifacts_dir = state.get("artifacts_dir") or f"/opt/feature-factory/tmp/{run_id}"
    os.makedirs(artifacts_dir, exist_ok=True)
    return artifacts_dir


async def spec_synth_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Строит формальную спецификацию (DSL оракулов) по intent из таблицы features.
    """
    try:
        run_ctx: RunCtx | None = state.get("run_ctx")
        if not run_ctx:
            raise ValueError("Run context not found in state")

        feature_id = run_ctx.feature_id
        correlation_id = run_ctx.correlation_id

        artifacts_dir = _ensure_artifacts_dir(state)

        # 1) Достаём intent_json из БД
        db_gen = get_db()
        db = next(db_gen)
        intent: Dict[str, Any] = {}
        try:
            row = db.execute(
                text("SELECT intent_json FROM features WHERE id = :id"),
                {"id": feature_id},
            ).fetchone()
            if row and row[0]:
                try:
                    intent = json.loads(row[0])
                except Exception:
                    intent = {}
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

        # 2) Формируем минимально полезную спецификацию-оракулы
        title = intent.get("title") or f"feature-{feature_id}"
        spec: Dict[str, Any] = {
            "feature_id": feature_id,
            "title": title,
            "acceptance_tests": {
                # API-тесты будут прогоняться на изолированных роутерах, созданных Dev узлом
                # (динамические тесты в TestSynth читают artifact_manifest.yaml и импортируют routers)
                "api": intent.get("acceptance", {}).get("api", []),
                "invariants": [
                    "no_secrets_in_repo",
                    "idempotent_apply",
                ],
            },
            "feature_flags": intent.get("feature_flags", []),
            "migrations": intent.get("migrations", []),
            "perf_budget": intent.get("perf_budget", {"p95_ms": 500, "rps": 5}),
            "security_policies": intent.get("security", ["basic_auth_for_admin", "no_tokens_in_logs"]),
            "budgets": intent.get("budgets", {}),
            "dod": intent.get("dod", ["tests pass", "docs updated"]),
        }

        # 3) Сохраняем в artifacts_dir/architect_spec.json
        spec_path = os.path.join(artifacts_dir, "architect_spec.json")
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)

        logger.info(
            "spec_synth_completed",
            component="graph",
            agent_role="SpecSynth",
            env=get_env(),
            run_id=run_ctx.run_id,
            feature_id=feature_id,
            correlation_id=correlation_id,
            spec_path=spec_path,
        )

        st = dict(state)
        st.update({
            "status": "spec_synth_completed",
            "architect_spec": spec,
            "artifacts_dir": artifacts_dir,
        })
        return st

    except Exception as e:
        logger.error(
            "spec_synth_failed",
            component="graph",
            agent_role="SpecSynth",
            err_type=type(e).__name__,
            error=str(e),
            run_id=state.get("run_ctx").run_id if state.get("run_ctx") else "unknown",
        )
        return {"status": "spec_failed", "error": str(e)}
