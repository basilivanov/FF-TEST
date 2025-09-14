#!/usr/bin/env python3
"""
DEBUG: CI/Git env probe (TEST only). Возвращает флаги интеграции и признак наличия токена.
"""

import os
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/ci")


@router.get("/debug/git-env")
def git_env_debug():
    def present(k: str) -> bool:
        v = os.getenv(k)
        return bool(v and len(v) > 10)
    pem_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH", "")
    pem_ok = False
    try:
        if pem_path and os.path.exists(pem_path):
            st = os.stat(pem_path)
            pem_ok = (st.st_mode & 0o777) == 0o600
    except Exception:
        pem_ok = False
    return {
        "GIT_INTEGRATION_ENABLED": os.getenv("GIT_INTEGRATION_ENABLED"),
        "SCM_PUSH_ENABLED": os.getenv("SCM_PUSH_ENABLED"),
        "SCM_PROVIDER": os.getenv("SCM_PROVIDER"),
        "GITHUB_OWNER": os.getenv("GITHUB_OWNER"),
        "GITHUB_REPO": os.getenv("GITHUB_REPO"),
        "GIT_BASE_BRANCH": os.getenv("GIT_BASE_BRANCH"),
        "GITHUB_TOKEN_present": present("GITHUB_TOKEN"),
        # GitHub App diagnostics (TEST)
        "GITHUB_APP_ID_present": present("GITHUB_APP_ID"),
        "GITHUB_APP_INSTALLATION_ID_present": present("GITHUB_APP_INSTALLATION_ID"),
        "GITHUB_APP_CLIENT_ID_present": present("GITHUB_APP_CLIENT_ID"),
        "GITHUB_APP_CLIENT_SECRET_present": present("GITHUB_APP_CLIENT_SECRET"),
        "GITHUB_APP_PRIVATE_KEY_PATH": pem_path,
        "GITHUB_APP_PRIVATE_KEY_perms_600": pem_ok,
    }
