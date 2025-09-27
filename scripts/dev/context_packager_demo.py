#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys

REPO_ROOT = "/opt/feature-factory"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.context.packager import ContextPackager


def main() -> None:
    # Тестовая задача (не запускает фичу), имитирует Dev‑узел
    task = {
        "id": "TASK-DEMO-CTX-001",
        "feature_id": "FEAT-DEMO-001",
        "role": "Dev",
        "dsl_json": json.dumps({
            "name": "demo_dynamic_context",
            "description": "Проверка сборки динамического контекста по селекторам: app/api, символ 'ContextPackager'",
            "selectors": [
                {"type": "code", "filters": {"module_path": "app/context"}, "top_k": 5},
                {"type": "code", "filters": {"symbol": "ContextPackager"}, "top_k": 5}
            ]
        }, ensure_ascii=False),
    }
    pkg = ContextPackager()
    md = pkg.build_context_for_task(task)
    print(md)


if __name__ == "__main__":
    main()
