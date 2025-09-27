#!/usr/bin/env python3
from __future__ import annotations

import threading
from typing import Dict, Tuple

_lock = threading.Lock()
_counters: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}
_gauges: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}
_sums: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}
_counts: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], int] = {}


def _key(name: str, labels: Dict[str, str] | None) -> Tuple[str, Tuple[Tuple[str, str], ...]]:
    items = tuple(sorted((labels or {}).items()))
    return (name, items)


def inc(name: str, labels: Dict[str, str] | None = None, value: float = 1.0) -> None:
    with _lock:
        k = _key(name, labels)
        _counters[k] = _counters.get(k, 0.0) + float(value)


def set_gauge(name: str, value: float, labels: Dict[str, str] | None = None) -> None:
    with _lock:
        k = _key(name, labels)
        _gauges[k] = float(value)


def observe(name_prefix: str, value: float, labels: Dict[str, str] | None = None) -> None:
    """Records observation as sum+count pair for simple summaries.

    name_prefix_sum/count metrics will be rendered.
    """
    with _lock:
        k = _key(f"{name_prefix}_sum", labels)
        _sums[k] = _sums.get(k, 0.0) + float(value)
        kc = _key(f"{name_prefix}_count", labels)
        _counts[kc] = _counts.get(kc, 0) + 1


def render_prometheus_text() -> str:
    lines = []
    # Counters
    for (name, labels), value in list(_counters.items()):
        lines.append(f"# TYPE {name} counter")
        if labels:
            lbl = ",".join([f"{k}={quote(v)}" for k, v in labels])
            lines.append(f"{name}{{{lbl}}} {value}")
        else:
            lines.append(f"{name} {value}")
    # Gauges
    for (name, labels), value in list(_gauges.items()):
        lines.append(f"# TYPE {name} gauge")
        if labels:
            lbl = ",".join([f"{k}={quote(v)}" for k, v in labels])
            lines.append(f"{name}{{{lbl}}} {value}")
        else:
            lines.append(f"{name} {value}")
    # Sums + counts (simple summaries)
    for (name, labels), value in list(_sums.items()):
        lines.append(f"# TYPE {name} counter")
        if labels:
            lbl = ",".join([f"{k}={quote(v)}" for k, v in labels])
            lines.append(f"{name}{{{lbl}}} {value}")
        else:
            lines.append(f"{name} {value}")
    for (name, labels), value in list(_counts.items()):
        lines.append(f"# TYPE {name} counter")
        if labels:
            lbl = ",".join([f"{k}={quote(v)}" for k, v in labels])
            lines.append(f"{name}{{{lbl}}} {value}")
        else:
            lines.append(f"{name} {value}")
    return "\n".join(lines) + "\n"


def quote(v: str) -> str:
    # Simple prometheus label quoting
    return '"' + str(v).replace("\\", "\\\\").replace("\"", "\\\"") + '"'


# Convenience for ContextPackager metrics
def record_packager(role: str, source: str, duration_ms: float, size_bytes: int, files: int) -> None:
    labels = {"role": role or "", "source": source or ""}
    inc("context_packager_count_total", labels)
    observe("context_packager_duration_ms", duration_ms, labels)
    observe("context_packager_size_bytes", float(size_bytes), labels)
    observe("context_packager_files", float(files), labels)

