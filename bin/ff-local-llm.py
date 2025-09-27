#!/usr/bin/env python3
"""
Local deterministic CLI provider for E2E in TEST env.
Reads messages JSON on stdin: {"messages": [{"role":"system","content":"..."}, ...]}
Prints text response suitable for app.llm.router completion() to parse.
"""
from __future__ import annotations
import sys, json, re, os

def read_stdin() -> dict:
    try:
        data = sys.stdin.read()
        if not data.strip():
            return {}
        return json.loads(data)
    except Exception:
        return {}

def detect_role(msgs: list[dict]) -> str:
    sys_txt = (msgs[0].get('content') if msgs else '') or ''
    u_txt = (msgs[-1].get('content') if msgs else '') or ''
    t = (sys_txt + '\n' + u_txt).lower()
    if 'architect ai' in t or 'architect' in t:
        return 'Architect'
    if 'qa-инженер' in t or 'qa' in t:
        return 'QA'
    if 'scribe' in t or 'документации' in t:
        return 'Scribe'
    # default dev
    return 'Dev'

def parse_feature_id_from_messages(msgs: list[dict]) -> str:
    # try to find a feature id hint from user content
    u = (msgs[-1].get('content') if msgs else '') or ''
    m = re.search(r'feature\s*[:#]?\s*(\w[\w-]*)', u, re.I)
    return m.group(1) if m else 'E2E'

def respond_architect(messages: list[dict]) -> str:
    # Simple DAG Dev->Gate->QA->Scribe->Apply
    plan = {
        "dag": {
            "nodes": [
                {"id": "dev1", "role": "Dev", "name": "Implement hello endpoint"},
                {"id": "gate1", "role": "Gate", "name": "Code review gate"},
                {"id": "qa1", "role": "QA", "name": "Generate and run tests"},
                {"id": "scribe1", "role": "Scribe", "name": "Update docs"},
                {"id": "apply1", "role": "Apply", "name": "Merge changes"},
            ],
            "edges": [
                {"from": "dev1", "to": "gate1"},
                {"from": "gate1", "to": "qa1"},
                {"from": "qa1", "to": "scribe1"},
                {"from": "scribe1", "to": "apply1"},
            ],
        },
        "budgets": {"Architect": 1000, "Dev": 2000, "QA": 1500, "Scribe": 800},
        "dod": ["tests pass", "docs updated"],
    }
    return json.dumps(plan, ensure_ascii=False)

def respond_dev(messages: list[dict]) -> str:
    feature_id = parse_feature_id_from_messages(messages)
    # manifest + router code
    yaml_block = (
        "```yaml\n"
        "files:\n"
        "  - app/api/hello.py\n"
        "package_contract:\n"
        f"  package_id: PKG-{feature_id}-v1\n"
        "  summary: Simple hello endpoint\n"
        "```\n"
    )
    code_block = (
        "```python\n"
        "# app/api/hello.py\n"
        "from fastapi import APIRouter, Query\n"
        "router = APIRouter(prefix=\"/api/v1\")\n\n"
        "@router.get(\"/hello\")\n"
        "def hello(name: str = Query(\"World\")):\n"
        "    return {\"message\": f\"Hello, {name}!\"}\n"
        "```\n"
    )
    return yaml_block + "\n" + code_block

def respond_qa(messages: list[dict]) -> str:
    # single simple test targeting our hello endpoint
    test_code = (
        "```python\n"
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "from app.api.hello import router\n\n"
        "def test_hello_endpoint_generated():\n"
        "    app = FastAPI()\n"
        "    app.include_router(router)\n"
        "    c = TestClient(app)\n"
        "    r = c.get('/api/v1/hello?name=Alice')\n"
        "    assert r.status_code == 200\n"
        "    assert 'Alice' in r.json().get('message','')\n"
        "```\n"
    )
    return test_code

def respond_scribe(messages: list[dict]) -> str:
    yml = (
        "```yaml\n"
        "changelog_entry: |\n"
        "  - Добавлена фича: Hello endpoint (QA: PASS)\n"
        "    - Детали: E2E medium feature\n"
        "```\n"
    )
    return yml

def main():
    # simple version flag
    if any(x in sys.argv for x in ('-v', '--version')):
        print('ff-local-llm 0.1.0')
        return 0
    payload = read_stdin()
    msgs = payload.get('messages') or []
    role = detect_role(msgs)
    if role == 'Architect':
        out = respond_architect(msgs)
    elif role == 'QA':
        out = respond_qa(msgs)
    elif role == 'Scribe':
        out = respond_scribe(msgs)
    else:
        out = respond_dev(msgs)
    # print plain text; router will wrap to choices
    sys.stdout.write(out)
    sys.stdout.flush()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

