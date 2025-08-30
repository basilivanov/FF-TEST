#!/usr/bin/env python3
"""
LLM status endpoints: OAuth/auth readiness and CLI probes based on declarative config.
"""

from __future__ import annotations
from fastapi import APIRouter
from typing import Any, Dict, List
import os
import time
from app.llm.router import (
    _load_cli_decl_config,
    _alias_to_decl,
    PROVIDER_ADAPTERS,
    FF_UNIVERSAL_WRAPPER,
)
from app.llm.transports.cli import run_cli
from app.utils.secret_store import decrypt_value
try:
    from app.db.session import SessionLocal
except Exception:
    SessionLocal = None

router = APIRouter(prefix="/api/v1/llm")


def _get_secret(key: str) -> str | None:
    if not key or SessionLocal is None:
        return None
    db = SessionLocal()
    try:
        row = db.execute("SELECT value_enc FROM secrets WHERE key = :k", {"k": key}).fetchone()
        if not row:
            return None
        return decrypt_value(row[0])
    except Exception:
        return None
    finally:
        db.close()


@router.get("/status")
def llm_status() -> Dict[str, Any]:
    decl = _load_cli_decl_config() or {}
    providers = (decl.get("providers") or {}).keys()
    statuses: List[Dict[str, Any]] = []
    for base_provider in providers:
        prov = decl.get("providers", {}).get(base_provider) or {}
        auth = prov.get("auth") or {}
        probe = prov.get("probe") or []
        binary_path = prov.get("binary_path")
        env_cfg = prov.get("env") or {}
        status: Dict[str, Any] = {
            "provider": base_provider,
            "binary_path": binary_path,
            "probe": probe,
            "auth": {
                "refresh_secret_key": auth.get("refresh_secret_key"),
                "has_refresh_token": False,
                "has_client": bool(auth.get("client_id") and auth.get("client_secret")),
                "token_endpoint": bool(auth.get("token_endpoint")),
                "local_config_file": auth.get("local_config_file"),
            },
            "cli_probe": {"ok": None, "stderr": None, "returncode": None},
        }

        # Secrets presence
        rt = _get_secret(auth.get("refresh_secret_key")) if auth.get("refresh_secret_key") else None
        status["auth"]["has_refresh_token"] = bool(rt)

        # CLI probe: wrapper + binary + probe args
        if binary_path and isinstance(probe, list) and probe:
            try:
                cmd = [FF_UNIVERSAL_WRAPPER, binary_path] + probe
                # assemble env: only non-empty values
                env = {k: v for k, v in env_cfg.items() if v}
                rc, stdout, stderr = run_cli(cmd, env, timeout_s=10)
                status["cli_probe"] = {"ok": rc == 0, "returncode": rc, "stderr": (stderr or "").strip()[:300]}
            except Exception as e:
                status["cli_probe"] = {"ok": False, "error": str(e)}

        # Access token refresh (dry run)
        try:
            adapter_class = PROVIDER_ADAPTERS.get(base_provider)
            if adapter_class and auth:
                adapter = adapter_class(base_provider)
                auth_cfg = dict(auth)
                auth_cfg["refresh_token"] = rt
                at = None
                if hasattr(adapter, "get_fresh_access_token"):
                    at = adapter.get_fresh_access_token(auth_cfg)
                status["auth"]["can_refresh_now"] = bool(at)
            else:
                status["auth"]["can_refresh_now"] = False
        except Exception as e:
            status["auth"]["can_refresh_now"] = False
            status["auth"]["refresh_error"] = str(e)

        # Local config file exists?
        lcf = auth.get("local_config_file")
        if lcf:
            status["auth"]["local_config_exists"] = os.path.exists(lcf)
        else:
            status["auth"]["local_config_exists"] = False

        statuses.append(status)

    return {"status": "ok", "providers": statuses, "ts": int(time.time())}

