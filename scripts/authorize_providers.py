#!/usr/bin/env python3
"""
Одноразовая авторизация провайдеров LLM для получения Refresh Token и сохранения в Secret Store.

Поддерживает два режима:
1) Guided: печать OAuth-URL и ввод кода/refresh_token вручную
2) Direct: непосредственный ввод refresh_token оператором

Секреты сохраняются в таблицу `secrets` через app.db.session с ключами:
 - CLAUDE_REFRESH_TOKEN
 - GEMINI_REFRESH_TOKEN
 - QWEN_REFRESH_TOKEN
 - (Codex не требует refresh flow)

Для Google (Gemini) поддержан обмен code->refresh_token при наличии client_id/client_secret/redirect_uri.
Для прочих провайдеров скрипт предложит ввести refresh_token вручную.
"""

from __future__ import annotations
import argparse
import sys
import os
from pathlib import Path
import httpx
from datetime import datetime

# --- Bootstrap sys.path and env (.env) so script runs from anywhere ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def _load_dotenv(dotenv_path: Path) -> None:
    try:
        if dotenv_path.exists():
            for line in dotenv_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    if k and v and k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

_load_dotenv(PROJECT_ROOT / ".env")

# Fallback DATABASE_URL to known dev DB if still not set
os.environ.setdefault("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")

from app.db.session import SessionLocal
from app.utils.secret_store import encrypt_value, mask_value
import yaml
from urllib.parse import urlencode
from sqlalchemy import text


def _upsert_secret(key: str, value: str) -> None:
    db = SessionLocal()
    try:
        enc = encrypt_value(value)
        now = datetime.utcnow().isoformat(timespec="seconds")
        db.execute(
            text("""
            INSERT INTO secrets(key, value_enc, scope, owner, created_at, updated_at)
            VALUES (:k, :v, :s, :o, :ts, :ts)
            ON CONFLICT(key) DO UPDATE SET
              value_enc = excluded.value_enc,
              updated_at = excluded.updated_at
            """),
            {"k": key, "v": enc, "s": "prod", "o": "system", "ts": now},
        )
        db.commit()
        print(f"Saved {key}: {mask_value(value)}")
    finally:
        db.close()


def authorize_gemini_via_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> str:
    token_endpoint = "https://oauth2.googleapis.com/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(token_endpoint, data=data)
        resp.raise_for_status()
        js = resp.json()
        rt = js.get("refresh_token")
        if not rt:
            raise RuntimeError("No refresh_token in response")
        return rt


def _load_decl_cfg() -> dict:
    path = PROJECT_ROOT / "configs/llm_cli_config.yaml"
    if not path.exists():
        raise RuntimeError(f"Config not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _secret_key_from_placeholder(val: str | None) -> str | None:
    if not val or not isinstance(val, str):
        return None
    # Expect format <SECRET:KEY>
    if val.startswith("<SECRET:") and val.endswith(">"):
        return val[len("<SECRET:"):-1]
    return None


def _auth_config_for_provider(provider: str) -> tuple[dict, dict]:
    cfg = _load_decl_cfg()
    prov = (cfg.get("providers") or {}).get(provider)
    if not prov:
        # try alias mapping
        alias = (cfg.get("aliases") or {}).get(provider)
        if alias and isinstance(alias, dict):
            pname = alias.get("provider")
            prov = (cfg.get("providers") or {}).get(pname)
    if not prov:
        raise RuntimeError(f"Provider not found in decl config: {provider}")
    return cfg, prov.get("auth") or {}


def main() -> int:
    p = argparse.ArgumentParser(description="Authorize providers and store refresh tokens")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gemini", help="Authorize Gemini")
    g.add_argument("--client-id", required=False, help="OAuth Client ID (will be stored as GEMINI_OAUTH_CLIENT_ID)")
    g.add_argument("--client-secret", required=False, help="OAuth Client Secret (will be stored as GEMINI_OAUTH_CLIENT_SECRET)")
    g.add_argument("--redirect-uri", required=False, default="https://codeassist.google.com/authcode")
    g.add_argument("--code", required=False, help="Authorization code for exchange")
    g.add_argument("--refresh-token", required=False, help="Paste existing refresh token (stored as GEMINI_REFRESH_TOKEN)")

    c = sub.add_parser("claude", help="Store Claude OAuth settings")
    c.add_argument("--refresh-token", required=False, help="Refresh token (stored as CLAUDE_REFRESH_TOKEN)")
    c.add_argument("--client-id", required=False, help="OAuth Client ID (stored as CLAUDE_OAUTH_CLIENT_ID)")
    c.add_argument("--client-secret", required=False, help="OAuth Client Secret (stored as CLAUDE_OAUTH_CLIENT_SECRET)")
    c.add_argument("--token-endpoint", required=False, help="OAuth token endpoint (stored as CLAUDE_OAUTH_TOKEN_ENDPOINT)")

    q = sub.add_parser("qwen", help="Store Qwen refresh token")
    q.add_argument("--refresh-token", required=True)

    # Unified OAuth flow
    u = sub.add_parser("oauth", help="Unified OAuth flow using llm_cli_config.yaml")
    u.add_argument("--provider", required=True, help="Provider key, e.g., gemini, claude, qwen")
    u.add_argument("--client-id", required=False)
    u.add_argument("--client-secret", required=False)
    u.add_argument("--redirect-uri", required=False, default="https://localhost/callback")
    u.add_argument("--code", required=False)
    u.add_argument("--refresh-token", required=False)

    args = p.parse_args()

    if args.cmd == "gemini":
        # Always store provided client credentials if present
        if args.client_id:
            _upsert_secret("GEMINI_OAUTH_CLIENT_ID", args.client_id)
        if args.client_secret:
            _upsert_secret("GEMINI_OAUTH_CLIENT_SECRET", args.client_secret)
        if args.refresh_token:
            _upsert_secret("GEMINI_REFRESH_TOKEN", args.refresh_token)
            return 0
        if not (args.client_id and args.client_secret and args.code):
            print("Provide --client-id, --client-secret and --code or use --refresh-token", file=sys.stderr)
            return 2
        rt = authorize_gemini_via_code(args.client_id, args.client_secret, args.code, args.redirect_uri)
        _upsert_secret("GEMINI_REFRESH_TOKEN", rt)
        return 0

    if args.cmd == "claude":
        if args.client_id:
            _upsert_secret("CLAUDE_OAUTH_CLIENT_ID", args.client_id)
        if args.client_secret:
            _upsert_secret("CLAUDE_OAUTH_CLIENT_SECRET", args.client_secret)
        if args.token_endpoint:
            _upsert_secret("CLAUDE_OAUTH_TOKEN_ENDPOINT", args.token_endpoint)
        if args.refresh_token:
            _upsert_secret("CLAUDE_REFRESH_TOKEN", args.refresh_token)
        if not (args.client_id or args.client_secret or args.token_endpoint or args.refresh_token):
            print("Provide at least one of --refresh-token/--client-id/--client-secret/--token-endpoint", file=sys.stderr)
            return 2
        return 0

    if args.cmd == "qwen":
        _upsert_secret("QWEN_REFRESH_TOKEN", args.refresh_token)
        return 0

    if args.cmd == "oauth":
        provider = args.provider.strip()
        cfg, auth = _auth_config_for_provider(provider)
        # Persist client_id/client_secret into their secret keys if placeholders used
        cid_ph = _secret_key_from_placeholder(auth.get("client_id"))
        csec_ph = _secret_key_from_placeholder(auth.get("client_secret"))
        if args.client_id and cid_ph:
            _upsert_secret(cid_ph, args.client_id)
        if args.client_secret and csec_ph:
            _upsert_secret(csec_ph, args.client_secret)

        # Refresh token fast-path
        if args.refresh_token:
            rk = auth.get("refresh_secret_key") or f"{provider.upper()}_REFRESH_TOKEN"
            _upsert_secret(rk, args.refresh_token)
            return 0

        # Exchange code if provided
        token_endpoint = auth.get("token_endpoint")
        if args.code:
            client_id = args.client_id or (args.client_id or "")
            client_secret = args.client_secret or (args.client_secret or "")
            if provider == "gemini":
                rt = authorize_gemini_via_code(client_id, client_secret, args.code, args.redirect_uri)
            else:
                # Generic OAuth2 code exchange
                if not token_endpoint:
                    print("token_endpoint missing in config; cannot exchange code", file=sys.stderr)
                    return 2
                data = {
                    "grant_type": "authorization_code",
                    "code": args.code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": args.redirect_uri,
                }
                with httpx.Client(timeout=30) as client:
                    resp = client.post(token_endpoint, data=data)
                    resp.raise_for_status()
                    js = resp.json()
                    rt = js.get("refresh_token")
                    if not rt:
                        raise RuntimeError("No refresh_token in response")
            rk = auth.get("refresh_secret_key") or f"{provider.upper()}_REFRESH_TOKEN"
            _upsert_secret(rk, rt)
            return 0

        # Construct authorization URL for manual flow
        authz = auth.get("authorization_endpoint")
        if not authz:
            print("authorization_endpoint missing; provide --refresh-token or --code", file=sys.stderr)
            return 2
        scope = auth.get("scope") or auth.get("scopes") or ""
        client_id = args.client_id or ""
        params = {
            "client_id": client_id,
            "redirect_uri": args.redirect_uri,
            "response_type": "code",
            "scope": scope,
        }
        # For Google add offline access hints
        if "accounts.google.com" in authz:
            params.update({"access_type": "offline", "prompt": "consent"})
        url = f"{authz}?{urlencode(params)}"
        print("Open this URL in a browser, authorize and pass --code:")
        print(url)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
