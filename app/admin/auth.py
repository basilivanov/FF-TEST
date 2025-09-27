from __future__ import annotations
"""Вспомогательные функции для BasicAuth админских эндпоинтов."""

import os
import secrets
from functools import lru_cache
from typing import Dict

from fastapi import HTTPException, status
from fastapi.security import HTTPBasicCredentials

# Базовые значения по умолчанию: сохраняем существующую пару ops/ops123
# и добавляем admin/password для совместимости с тестовыми сценариями E15.
DEFAULT_CREDENTIALS = (
    ("ops", "ops123"),
    ("admin", "password"),
)


@lru_cache(maxsize=1)
def _load_credentials() -> Dict[str, str]:
    """Собирает пары логин/пароль из окружения и дефолтов."""
    credentials: Dict[str, str] = {}

    # Основной способ конфигурации — ADMIN_BASIC_AUTH_USERS="user1:pass1,user2:pass2"
    users_env = os.getenv("ADMIN_BASIC_AUTH_USERS")
    if users_env:
        for chunk in users_env.split(','):
            chunk = chunk.strip()
            if not chunk or ':' not in chunk:
                continue
            username, password = chunk.split(':', 1)
            username, password = username.strip(), password.strip()
            if username and password:
                credentials[username] = password

    # Совместимость с более старыми переменными окружения
    env_username = os.getenv("ADMIN_USERNAME")
    env_password = os.getenv("ADMIN_PASSWORD")
    if env_username and env_password:
        credentials[env_username] = env_password

    # Если ничего не настроено, используем значения по умолчанию
    if not credentials:
        for username, password in DEFAULT_CREDENTIALS:
            credentials[username] = password

    return credentials


def ensure_admin_credentials(credentials: HTTPBasicCredentials) -> str:
    """Проверяет пару логин/пароль и возвращает имя пользователя."""
    stored_credentials = _load_credentials()

    stored_password = stored_credentials.get(credentials.username)
    if stored_password and secrets.compare_digest(credentials.password, stored_password):
        return credentials.username

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Basic"},
    )


def get_configured_admin_users() -> Dict[str, str]:
    """Возвращает словарь настроенных пользователей (для диагностики/логов)."""
    return _load_credentials().copy()
