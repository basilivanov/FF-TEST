#!/usr/bin/env python3
"""
LLM status endpoints: OAuth/auth readiness and CLI probes based on declarative config.
"""

from __future__ import annotations
from fastapi import APIRouter, Query
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
import yaml
from app.llm.router import completion

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


@router.get("/roles-check")
def roles_check(
    roles: str | None = Query(None, description="Comma-separated role names to check; defaults to all in llm_routing.yaml"),
    timeout_s: int = Query(10, ge=1, le=120),
    max_tokens: int = Query(64, ge=1, le=4096),
) -> Dict[str, Any]:
    """Checks that each configured role can respond to a small prompt.

    Returns per-role status with provider/model info when available.
    """
    # Load roles from routing config
    routing = {}
    try:
        with open("/opt/feature-factory/configs/llm_routing.yaml", "r") as f:
            routing = yaml.safe_load(f) or {}
    except Exception:
        routing = {}
    configured_roles = sorted((routing.get("roles") or {}).keys())
    target_roles = [r.strip() for r in roles.split(",")] if roles else configured_roles

    results: List[Dict[str, Any]] = []
    for role in target_roles:
        start = time.time()
        try:
            out = completion(
                role=role,
                messages=[
                    {"role": "system", "content": f"You are {role}."},
                    {"role": "user", "content": "Return a short acknowledgement."},
                ],
                max_tokens=max_tokens,
                temperature=0,
                timeout_s=timeout_s,
            )
            # Try to normalize
            text = out.get("text") or (out.get("choices", [{}])[0].get("message", {}).get("content"))
            latency_ms = int((time.time() - start) * 1000)
            results.append({
                "role": role,
                "ok": bool(text),
                "latency_ms": latency_ms,
                "model": out.get("model") or "",
                "provider": out.get("provider") or routing.get("roles", {}).get(role, {}).get("providers", [None])[0],
                "text_len": len(str(text or "")),
            })
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            results.append({
                "role": role,
                "ok": False,
                "latency_ms": latency_ms,
                "error": str(e),
            })

    overall_ok = all(r.get("ok") for r in results) if results else False
    return {"status": "ok" if overall_ok else "partial", "results": results, "ts": int(time.time())}
