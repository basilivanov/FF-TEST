#!/usr/bin/env python3
"""
Centralized logging configuration for Feature Factory.

Goals:
- Single JSON log format across the app
- Module-level log level control with runtime overrides
- Secret redaction in logs

Design notes:
- structlog + stdlib logger factory, so stdlib levels are respected
- Redaction processor masks common secret keys
- Helper functions to apply module levels from env and at runtime
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, Optional, Tuple

import structlog


# -----------------------
# Utilities
# -----------------------

_LEVEL_MAP = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def parse_level(name: str, default: int = logging.INFO) -> int:
    if not name:
        return default
    return _LEVEL_MAP.get(str(name).strip().upper(), default)


def parse_module_levels(spec: str) -> Dict[str, int]:
    """Parse spec like "api=DEBUG,orchestrator=INFO,db=WARN" into dict of logger names.
    Accepted logger names should match module prefixes, e.g. "app.api".
    Short names like "api" will be expanded to "app.api" automatically.
    """
    if not spec:
        return {}
    out: Dict[str, int] = {}
    for token in spec.split(','):
        token = token.strip()
        if not token:
            continue
        if '=' not in token:
            continue
        name, lvl = token.split('=', 1)
        name = name.strip()
        if not name:
            continue
        # Expand shortcuts
        if not name.startswith('app.'):
            name = f'app.{name}'
        out[name] = parse_level(lvl, logging.INFO)
    return out


# -----------------------
# Redaction Processor
# -----------------------

_SECRET_KEYS = re.compile(r"(token|secret|authorization|password|client_secret)", re.IGNORECASE)


def redact_secrets_processor(_, __, event_dict: dict) -> dict:
    def _redact(v: object) -> object:
        try:
            s = str(v)
            if len(s) <= 4:
                return "***"
            return s[:4] + "***"
        except Exception:
            return "***"

    # redact direct keys
    for k in list(event_dict.keys()):
        if _SECRET_KEYS.search(k):
            event_dict[k] = _redact(event_dict[k])

    # redact nested kv dict if present
    kv = event_dict.get("kv")
    if isinstance(kv, dict):
        for k in list(kv.keys()):
            if _SECRET_KEYS.search(k):
                kv[k] = _redact(kv[k])
        event_dict["kv"] = kv
    return event_dict


# -----------------------
# Base Configuration
# -----------------------

def _configure_stdlib(root_level: int, module_levels: Dict[str, int]) -> None:
    logging.basicConfig(level=root_level)
    # Apply module levels
    for mod, lvl in module_levels.items():
        logging.getLogger(mod).setLevel(lvl)


def configure_from_env() -> Tuple[int, Dict[str, int]]:
    root_level = parse_level(os.getenv("LOG_LEVEL", "INFO"), logging.INFO)
    module_levels = parse_module_levels(os.getenv("LOG_LEVEL_APP", ""))

    _configure_stdlib(root_level, module_levels)

    # structlog → stdlib
    # Sampling/throttle configuration from ENV
    debug_sample_n = int(os.getenv("LOG_DEBUG_SAMPLE_N", "1") or "1")
    warn_throttle_sec = float(os.getenv("LOG_WARN_THROTTLE_WINDOW_SEC", "0") or "0")

    # State for sampling/throttling
    _sample_counters = {}
    _warn_last_emit: Dict[str, float] = {}

    def sampling_processor(logger, method_name: str, event_dict: dict) -> Optional[dict]:
        # Only sample DEBUG when requested
        if debug_sample_n <= 1:
            return event_dict
        if method_name and method_name.lower() == "debug":
            # Key by event name to keep distribution fair
            key = event_dict.get("event") or "debug"
            cnt = _sample_counters.get(key, 0) + 1
            _sample_counters[key] = cnt
            if cnt % debug_sample_n != 0:
                # drop event
                return None
        return event_dict

    def warn_throttle_processor(logger, method_name: str, event_dict: dict) -> Optional[dict]:
        if warn_throttle_sec <= 0:
            return event_dict
        if method_name and method_name.lower() in ("warning", "warn"):
            key = (event_dict.get("event") or "warning") + "|" + (event_dict.get("component") or "")
            now = datetime.now(timezone.utc).timestamp()
            last = _warn_last_emit.get(key, 0.0)
            if (now - last) < warn_throttle_sec:
                return None
            _warn_last_emit[key] = now
        return event_dict

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            sampling_processor,
            warn_throttle_processor,
            redact_secrets_processor,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return root_level, module_levels


# Configure on import for application startup
ROOT_LEVEL, MODULE_LEVELS = configure_from_env()

# Public logger accessor used by application modules
log = structlog.get_logger()


# -----------------------
# Runtime Overrides
# -----------------------

def apply_runtime_levels(global_level: Optional[str] = None, modules: Optional[Dict[str, str]] = None) -> None:
    """Apply runtime levels immediately to stdlib loggers.
    - global_level: string level name (optional)
    - modules: dict of {module: level_name}
    """
    if global_level:
        gl = parse_level(global_level)
        logging.getLogger().setLevel(gl)
    if modules:
        for name, lvlname in modules.items():
            mod = name if name.startswith('app.') else f'app.{name}'
            logging.getLogger(mod).setLevel(parse_level(lvlname))
