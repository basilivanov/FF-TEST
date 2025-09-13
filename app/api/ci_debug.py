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
    return {
        "GIT_INTEGRATION_ENABLED": os.getenv("GIT_INTEGRATION_ENABLED"),
        "SCM_PUSH_ENABLED": os.getenv("SCM_PUSH_ENABLED"),
        "SCM_PROVIDER": os.getenv("SCM_PROVIDER"),
        "GITHUB_OWNER": os.getenv("GITHUB_OWNER"),
        "GITHUB_REPO": os.getenv("GITHUB_REPO"),
        "GIT_BASE_BRANCH": os.getenv("GIT_BASE_BRANCH"),
        "GITHUB_TOKEN_present": present("GITHUB_TOKEN"),
    }

