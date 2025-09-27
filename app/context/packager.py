#!/usr/bin/env python3
"""
ContextPackager — модуль формирования "контекстного пакета" для задач.

Основные этапы:
1) Анализ dsl_json задачи и извлечение ключевых слов (пути файлов, символы).
2) Формирование Selector DSL запросов (docs/Selectors-DSL-001.md).
3) Запрос к индексу кода (symbol_index, call_graph_edges) в БД INDEX.
4) Извлечение содержимого файлов и сборка Markdown.

Модуль устойчив к отсутствию индекса: в этом случае использует эвристики по именам файлов
и читает их напрямую из репозитория.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

try:
    from sqlalchemy import create_engine, text  # type: ignore
except Exception:  # pragma: no cover - soft dependency
    create_engine = None  # type: ignore
    def text(x: str) -> str:  # type: ignore
        return x
try:
    import structlog  # type: ignore
except Exception:  # pragma: no cover
    class _DummyLogger:
        def info(self, *args, **kwargs):
            pass
        def warning(self, *args, **kwargs):
            pass
        def error(self, *args, **kwargs):
            pass
    class structlog:  # type: ignore
        @staticmethod
        def get_logger():
            return _DummyLogger()


REPO_ROOT = "/opt/feature-factory"
DEFAULT_INDEX_DB = "sqlite:////opt/feature-factory/data/index.db"


@dataclass
class Selector:
    type: str  # "code" | "docs" | ...
    filters: Dict[str, Any]
    top_k: int = 5


class ContextPackager:
    def __init__(self, index_db_url: Optional[str] = None):
        self.index_db_url = index_db_url or os.getenv("INDEX_DATABASE_URL", DEFAULT_INDEX_DB)
        self._index_engine = None
        self._connect_index_engine()
        self._selector_source = "none"
        self.logger = structlog.get_logger()

    def _connect_index_engine(self) -> None:
        """Ленивая и устойчивная инициализация подключения к индексу.

        Приоритет: INDEX_DATABASE_URL → fallback на DATABASE_URL, если там есть таблицы индекса.
        """
        if create_engine is None:
            self._index_engine = None
            return
        # 1) Пытаемся INDEX_DATABASE_URL
        try:
            eng = create_engine(self.index_db_url)
            with eng.connect() as conn:
                try:
                    conn.execute(text("SELECT 1 FROM sqlite_master WHERE type='table' AND name='symbol_index'"))
                    self._index_engine = eng
                    return
                except Exception:
                    pass
        except Exception:
            pass

        # 2) Fallback: DATABASE_URL
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                self._index_engine = None
                return
            eng = create_engine(db_url)
            with eng.connect() as conn:
                res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('symbol_index','call_graph_edges')"))
                rows = res.fetchall()
                if rows:
                    self._index_engine = eng
                else:
                    self._index_engine = None
        except Exception:
            self._index_engine = None

    def _load_playbook(self) -> str:
        try:
            with open("/opt/feature-factory/cortex/playbook/main.md", "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _load_doctrine(self) -> str:
        """Загружает общие правила и анти-паттерны из доктрины."""
        try:
            with open("/opt/feature-factory/cortex/doctrine/common_rules.md", "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _load_security_credentials(self, task_description: str) -> str:
        """Загружает карту секретов, если в задаче упоминаются ключевые слова безопасности."""
        security_keywords = {"доступ", "пароль", "ключ", "api", "логин", "секрет", "auth", "login", "password", "key", "secret", "access"}
        
        # Проверяем наличие ключевых слов в описании задачи
        desc_lower = task_description.lower()
        if not any(keyword in desc_lower for keyword in security_keywords):
            return ""
            
        try:
            with open("/opt/feature-factory/cortex/security/credentials.md", "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _load_cortex_context(self, role: Optional[str]) -> str:
        """Загружает контекст Cortex V2 (core → role → patterns) с fallback на старые пути."""
        if not role:
            return ""

        context_parts = []
        # Cortex V2 — core
        core_modules_v2 = [
            "/opt/feature-factory/cortex/core/invariants.md",
            "/opt/feature-factory/cortex/core/principles.md",
            "/opt/feature-factory/cortex/core/output_formats.md",
            "/opt/feature-factory/cortex/core/envelope.md",
            "/opt/feature-factory/cortex/core/self_documenting.md",
        ]
        for module_path in core_modules_v2:
            try:
                with open(module_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        module_name = module_path.split("/")[-1].replace(".md", "").replace("_", " ").title()
                        context_parts.append(f"## {module_name}\n\n{content}")
            except Exception:
                pass

        # Cortex V2 — роль
        role_lc = (role or "").strip()
        try:
            role_path = f"/opt/feature-factory/cortex/roles/{role_lc.lower()}.md"
            if os.path.exists(role_path):
                with open(role_path, "r", encoding="utf-8") as f:
                    context_parts.append(f"## Role — {role}\n\n" + f.read())
        except Exception:
            pass

        # Cortex V2 — patterns (например, фронтенд для Dev)
        if role == "Dev":
            try:
                with open("/opt/feature-factory/cortex/patterns/frontend_tech_stack.md", "r", encoding="utf-8") as f:
                    context_parts.append("## Frontend Patterns\n\n" + f.read())
            except Exception:
                pass

        # Старые пути (fallback)
        if not context_parts:
            core_modules = [
                "/opt/feature-factory/app/agents/prompts/core/role_definitions.md",
                "/opt/feature-factory/app/agents/prompts/core/tech_stack.md",
                "/opt/feature-factory/app/agents/prompts/core/anti_patterns.md",
                "/opt/feature-factory/app/agents/prompts/core/output_formats.md",
            ]
            if role == "Dev":
                core_modules.append("/opt/feature-factory/app/agents/prompts/core/frontend_tech_stack.md")
            for module_path in core_modules:
                try:
                    with open(module_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if content.strip():
                            module_name = module_path.split("/")[-1].replace(".md", "").replace("_", " ").title()
                            context_parts.append(f"## {module_name}\n\n{content}")
                except Exception:
                    pass
        
        # Fallback к старой системе, если новые модули не найдены
        if not context_parts:
            cortex_paths = []
            if role == "Dev":
                cortex_paths.extend([
                    "/opt/feature-factory/cortex/db/rules.md",
                    "/opt/feature-factory/cortex/logging_rules.md",
                ])
            elif role == "Ops":
                cortex_paths.append("/opt/feature-factory/cortex/ops_tools.md")

            for path in cortex_paths:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if content.strip():
                            context_parts.append(content)
                except Exception:
                    pass
        
        return "\n\n".join(context_parts) if context_parts else ""

    def _find_api_specs(self, keywords: Set[str]) -> List[Dict[str, Any]]:
        specs = []
        if not any(k in keywords for k in ["curl", "POST", "GET", "эндпоинт", "endpoint"]):
            return specs

        try:
            with open("/opt/feature-factory/cortex/api/openapi.spec.json", "r") as f:
                openapi_spec = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return specs

        paths = openapi_spec.get("paths", {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                # Check if any keyword matches the path or summary
                if any(k in path or k in operation.get("summary", "") for k in keywords):
                    specs.append({
                        "path": path,
                        "method": method,
                        "spec": operation,
                    })
        return specs

    # === Публичный API ===
    def build_context_for_task(self, task: Dict[str, Any]) -> str:
        """Строит Markdown-контекст по задаче.

        task ожидается в формате { id, feature_id, role, dsl_json(str|dict), ... }
        """
        playbook_content = self._load_playbook()
        role = task.get("role")
        cortex_content = self._load_cortex_context(role)
        
        # ВСЕГДА добавляем доктрину (правила и анти-паттерны)
        doctrine_content = self._load_doctrine()

        dsl = self._parse_dsl(task.get("dsl_json"))
        keywords = self._extract_keywords(dsl)
        
        # Получаем описание задачи для проверки ключевых слов безопасности
        task_description = ""
        try:
            task_description = str(dsl.get("description", "") or dsl.get("prompt", "") or dsl.get("name", "") or "")
        except Exception:
            task_description = ""
        
        # УСЛОВНО добавляем карту секретов
        security_content = self._load_security_credentials(task_description)

        api_specs = self._find_api_specs(keywords)

        selectors = self._build_selectors(task, dsl, keywords)
        file_paths: List[str] = self._execute_selectors(selectors)

        # Расширяем набор файлов через граф вызовов (pyan3), если что-то нашли
        call_edges: List[Tuple[str, str, str, str]] = []  # (caller_sym, callee_sym, caller_path, callee_path)
        if file_paths:
            more_paths, edges = self._expand_via_callgraph(file_paths, keywords)
            call_edges = edges
            file_paths.extend(more_paths)

        # При отсутствии индекса/результатов — пробуем эвристику по именам файлов
        if not file_paths:
            file_paths = self._heuristic_paths_from_keywords(keywords)

        # Fallback-эвристика по описанию: явные пути в description
        if not file_paths:
            desc = ""
            try:
                desc = str(dsl.get("description", "") or "")
            except Exception:
                desc = ""
            explicit_paths = self._paths_from_description(desc)
            confirmed: List[str] = []
            for p in explicit_paths:
                # проверяем существование
                abs_p = p if os.path.isabs(p) else os.path.join(REPO_ROOT, p)
                if os.path.exists(abs_p):
                    # нормализуем относительный путь
                    rel = p
                    if os.path.isabs(p) and p.startswith(REPO_ROOT):
                        rel = os.path.relpath(p, REPO_ROOT)
                    confirmed.append(rel)
            if confirmed:
                # логируем активацию фолбэка
                try:
                    self.logger.info(
                        "context_packager_fallback_activated",
                        component="dcms",
                        matched_files=confirmed,
                    )
                except Exception:
                    pass
                file_paths = confirmed

        # Дедублим и ограничиваем
        uniq_paths = self._unique_keep_order(file_paths)
        if len(uniq_paths) > 12:
            uniq_paths = uniq_paths[:12]

        file_entries = self._read_files(uniq_paths)

        t0 = time.time()
        md = self._compose_markdown(task, dsl, selectors, file_entries, call_edges, api_specs)
        
        # Prepend all context content in order of priority
        context_parts = []
        
        # 1. Доктрина - ВСЕГДА первая (самая важная)
        if doctrine_content:
            context_parts.append("# ДОКТРИНА И ПРАВИЛА РАБОТЫ\n\n" + doctrine_content)
            
        # 2. Карта секретов - если актуально
        if security_content:
            context_parts.append("# КАРТА ДОСТУПА К СЕКРЕТАМ\n\n" + security_content)
            
        # 3. Роле-специфичные правила из кортекса
        if cortex_content:
            context_parts.append("# РОЛЕ-СПЕЦИФИЧНЫЕ ПРАВИЛА\n\n" + cortex_content)
            
        # 4. Playbook
        if playbook_content:
            context_parts.append("# PLAYBOOK\n\n" + playbook_content)
        
        # 5. Основной контент
        context_parts.append(md)
        
        result = "\n\n".join(context_parts)
        try:
            self.logger.info(
                "context_packager_end",
                role=role,
                selector_source=getattr(self, "_selector_source", "unknown"),
                files=len(uniq_paths),
                size_bytes=len(result.encode("utf-8"))
            )
        except Exception:
            pass
        # Metrics
        try:
            from app.metrics.registry import record_packager
            duration_ms = (time.time() - t0) * 1000.0
            record_packager(role or "", getattr(self, "_selector_source", "unknown"), float(duration_ms), len(result.encode("utf-8")), len(uniq_paths))
        except Exception:
            pass
        return result

    def _compose_markdown(
        self,
        task: Dict[str, Any],
        dsl: Dict[str, Any],
        selectors: List[Selector],
        file_entries: List[Tuple[str, str]],
        call_edges: List[Tuple[str, str, str, str]],
        api_specs: List[Dict[str, Any]],
    ) -> str:
        header = f"# Context Package\n\n"
        meta = {
            "task_id": task.get("id"),
            "feature_id": task.get("feature_id"),
            "role": task.get("role"),
        }
        parts: List[str] = [header]
        parts.append("## Meta\n")
        parts.append("```json\n" + json.dumps(meta, ensure_ascii=False, indent=2) + "\n```\n\n")

        parts.append("## Task DSL\n")
        try:
            parts.append("```json\n" + json.dumps(dsl, ensure_ascii=False, indent=2) + "\n```\n\n")
        except Exception:
            parts.append("```\n<dsl unavailable>\n```\n\n")

        if selectors:
            parts.append("## Selectors\n")
            try:
                sel_json = [s.__dict__ for s in selectors]
                parts.append("```json\n" + json.dumps(sel_json, ensure_ascii=False, indent=2) + "\n```\n\n")
            except Exception:
                pass

        # Раздел с графом вызовов (если найден)
        if call_edges:
            parts.append("## Call Graph (pyan3)\n")
            # Ограничим вывод до 30 рёбер
            for i, (cs, es, cp, ep) in enumerate(call_edges[:30]):
                line = f"- {cs or 'caller'} ({cp or '?'}) -> {es or 'callee'} ({ep or '?'})\n"
                parts.append(line)
            parts.append("\n")

        if api_specs:
            parts.append("## API Specifications\n")
            for spec in api_specs:
                parts.append(f"### {spec['method'].upper()} {spec['path']}\n")
                parts.append("```json\n")
                parts.append(json.dumps(spec['spec'], ensure_ascii=False, indent=2))
                parts.append("\n```\n\n")

        if file_entries:
            parts.append("## Code & Docs\n")
            for path, content in file_entries:
                parts.append(f"### {path}\n")
                parts.append("```\n")
                parts.append(content)
                parts.append("\n``" + "`\n\n")
        else:
            parts.append("_Не найдено релевантных файлов._\n")

        return "".join(parts)

    def _unique_keep_order(self, items: Iterable[str]) -> List[str]:
        seen: Set[str] = set()
        out: List[str] = []
        for x in items:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out




    # === Внутренние утилиты ===
    def _parse_dsl(self, dsl_json: Any) -> Dict[str, Any]:
        if isinstance(dsl_json, dict):
            return dsl_json
        if isinstance(dsl_json, str) and dsl_json.strip():
            try:
                return json.loads(dsl_json)
            except Exception:
                return {"raw": dsl_json}
        return {}

    def _extract_keywords(self, dsl: Dict[str, Any]) -> Set[str]:
        keys: Set[str] = set()
        # Смотрим поля DSL
        for k in ("name", "prompt", "desc", "description"):
            v = dsl.get(k)
            if isinstance(v, str):
                keys |= self._keywords_from_text(v)
        # Весь DSL тоже в поиск
        try:
            keys |= self._keywords_from_text(json.dumps(dsl, ensure_ascii=False))
        except Exception:
            pass
        return keys

    def _keywords_from_text(self, text: str) -> Set[str]:
        found: Set[str] = set()
        # Имена файлов c расширениями
        for m in re.findall(r"[A-Za-z0-9_./-]+\.(?:py|tsx|ts|js|md|sql|sh|yaml|yml|ini|toml|json)\b", text, flags=re.IGNORECASE):
            found.add(m)
        # Примитивно вытащим потенциальные symbol/func имена
        for m in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]{2,})\b", text):
            if len(m) > 3:
                found.add(m)
        return found

    def _build_selectors(self, task: Dict[str, Any], dsl: Dict[str, Any], keywords: Set[str]) -> List[Selector]:
        sels: List[Selector] = []
        # 1) Если нашлись пути вида app/... — запрос по module_path
        module_like = [k for k in keywords if "/" in k and (k.endswith(".py") or k.endswith(".tsx") or k.endswith(".ts") or k.endswith(".js"))]
        for mp in module_like[:6]:
            sels.append(Selector(type="code", filters={"module_path": mp}, top_k=5))
            # Добавим эвристические запросы по графу вызовов
            sels.append(Selector(type="code", filters={"calls_to": mp}, top_k=5))
            sels.append(Selector(type="code", filters={"calls_from": mp}, top_k=5))
        # 2) Символы
        symbol_like = [k for k in keywords if re.match(r"^[A-Za-z_][A-Za-z0-9_]+$", k or "")]
        for sym in symbol_like[:6]:
            sels.append(Selector(type="code", filters={"symbol": sym}, top_k=5))
            # И по символам — попробуем связи графа вызовов
            sels.append(Selector(type="code", filters={"calls_to": sym}, top_k=5))
            sels.append(Selector(type="code", filters={"calls_from": sym}, top_k=5))
        return sels

    def _paths_from_description(self, desc: str) -> List[str]:
        """Извлекает явные пути к файлам из текста описания задачи.

        Примеры совпадений:
        - app/graph/nodes/dev_code.py
        - configs/telegram.yaml
        - app/api/init.ts
        """
        if not desc:
            return []
        # Ищем подстроки, похожие на пути c допустимыми расширениями; игнорируем завершающие знаки препинания
        matches = re.findall(r"([A-Za-z0-9_./-]+\.(?:py|tsx|ts|js|md|sql|sh|yaml|yml|ini|toml|json))\b", desc, flags=re.IGNORECASE)
        # Нормализуем: удаляем повторяющиеся и ведущие './'
        seen: Set[str] = set()
        out: List[str] = []
        for m in matches:
            m2 = m.lstrip("./")
            if m2 not in seen:
                seen.add(m2)
                out.append(m2)
        return out

    def _execute_selectors(self, selectors: List[Selector]) -> List[str]:
        paths: List[str] = []
        if not selectors:
            return paths
        if not self._index_engine:
            # Fallback: попробуем ctags, затем ripgrep
            ct_paths = self._execute_selectors_via_ctags(selectors)
            if ct_paths:
                self._selector_source = "ctags"
                return ct_paths
            rg_paths = self._execute_selectors_via_rg(selectors)
            if rg_paths:
                self._selector_source = "ripgrep"
            else:
                self._selector_source = "none"
            return rg_paths
        try:
            with self._index_engine.connect() as conn:
                for sel in selectors:
                    if sel.type != "code":
                        continue
                    f = sel.filters or {}
                    top_k = min(int(sel.top_k or 5), 8)
                    if f.get("module_path"):
                        q = text(
                            """
                            SELECT DISTINCT file_path
                            FROM symbol_index
                            WHERE file_path LIKE :p
                            LIMIT :k
                            """
                        )
                        p = f"%{f.get('module_path')}%"
                        rows = conn.execute(q, {"p": p, "k": top_k}).fetchall()
                        for r in rows:
                            paths.append(r[0])
                    if f.get("symbol"):
                        q = text(
                            """
                            SELECT DISTINCT file_path
                            FROM symbol_index
                            WHERE symbol_name LIKE :s
                            LIMIT :k
                            """
                        )
                        s = f"%{f.get('symbol')}%"
                        rows = conn.execute(q, {"s": s, "k": top_k}).fetchall()
                        for r in rows:
                            paths.append(r[0])
                    if f.get("calls_to"):
                        # По целевому символу найдём файлы, где он вызывается
                        q = text(
                            """
                            SELECT DISTINCT file_path
                            FROM call_graph_edges
                            WHERE target_symbol LIKE :p
                            LIMIT :k
                            """
                        )
                        p = f"%{f.get('calls_to')}%"
                        rows = conn.execute(q, {"p": p, "k": top_k}).fetchall()
                        for r in rows:
                            paths.append(r[0])
                    if f.get("calls_from"):
                        q = text(
                            """
                            SELECT DISTINCT file_path
                            FROM call_graph_edges
                            WHERE source_symbol LIKE :p
                            LIMIT :k
                            """
                        )
                        p = f"%{f.get('calls_from')}%"
                        rows = conn.execute(q, {"p": p, "k": top_k}).fetchall()
                        for r in rows:
                            paths.append(r[0])
            # зафиксируем источник
            self._selector_source = "index_db"
        except Exception:
            # Индекс/схема может отличаться — не падаем
            self._selector_source = "index_db_error"
            return []
        return paths

    def _execute_selectors_via_ctags(self, selectors: List[Selector]) -> List[str]:
        """Попытка получить пути через universal-ctags (в stdout), если бинарь доступен.

        Генерируем тэги на лету (без файлов) и фильтруем по имени символа/пути.
        """
        if not selectors:
            return []
        if not shutil.which("ctags"):
            return []
        try:
            cmd = [
                "ctags", "-R", "-f", "-", "--fields=+n", "--sort=no",
                "--languages=Python,TypeScript,TSX,JavaScript",
                REPO_ROOT,
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True, text=True)
            lines = proc.stdout.splitlines()
        except Exception:
            return []

        sym_filters: List[str] = []
        path_filters: List[str] = []
        for sel in selectors:
            f = sel.filters or {}
            if f.get("symbol"):
                sym_filters.append(str(f["symbol"]))
            if f.get("module_path"):
                path_filters.append(str(f["module_path"]))
        sym_filters = [s for s in sym_filters if s]
        path_filters = [p for p in path_filters if p]

        matched_paths: List[str] = []
        seen: Set[str] = set()
        for ln in lines:
            # Формат: <tagName> <TAB> <file> <TAB> ...
            try:
                parts = ln.split("\t")
                if len(parts) < 2:
                    continue
                tag, file_path = parts[0], parts[1]
                rel = os.path.relpath(file_path, REPO_ROOT) if os.path.isabs(file_path) else os.path.relpath(os.path.join(REPO_ROOT, file_path), REPO_ROOT)
                cond_sym = (not sym_filters) or any(tag.find(sf) != -1 for sf in sym_filters)
                cond_path = (not path_filters) or any(rel.find(pf) != -1 for pf in path_filters)
                if cond_sym or cond_path:
                    if rel not in seen:
                        seen.add(rel)
                        matched_paths.append(rel)
                if len(matched_paths) > 24:
                    break
            except Exception:
                continue
        return matched_paths

    def _execute_selectors_via_rg(self, selectors: List[Selector]) -> List[str]:
        """Fallback на ripgrep по имени символа/пути, если нет ctags/индекса."""
        if not selectors:
            return []
        if not shutil.which("rg"):
            return []
        sym_filters: List[str] = []
        path_filters: List[str] = []
        for sel in selectors:
            f = sel.filters or {}
            if f.get("symbol"):
                sym_filters.append(str(f["symbol"]))
            if f.get("module_path"):
                path_filters.append(str(f["module_path"]))
        candidates: List[str] = []
        try:
            # Ограничим поиск: попробуем выбрать корень по первому module_path
            search_root = REPO_ROOT
            for pf in path_filters:
                pf_clean = pf.strip().lstrip("/")
                if pf_clean:
                    cand = os.path.join(REPO_ROOT, pf_clean.split("/")[0])
                    if os.path.isdir(cand):
                        search_root = cand
                        break
            # Собираем дополнительные исключения
            rg_args = [
                "-g", "!node_modules",
                "-g", "!**/node_modules*",
                "-g", "!.venv",
                "-g", "!**/.venv*",
                "-g", "!__pycache__",
                "-g", "!**/.cache*",
                "-g", "*.py",
                "-g", "*.ts",
                "-g", "*.tsx",
                "-g", "*.js",
                "-g", "*.md",
                "-m", "200",
            ]
            for sym in sym_filters[:5]:
                cmd = [
                    "rg", "-n", "-S", sym, search_root,
                ]
                cmd.extend(rg_args)
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                for ln in proc.stdout.splitlines():
                    # Формат: path:line:match
                    p = ln.split(":", 1)[0]
                    if p.startswith(REPO_ROOT + os.sep):
                        rel = os.path.relpath(p, REPO_ROOT)
                    else:
                        rel = p
                    if path_filters and not any(rel.find(pf) != -1 for pf in path_filters):
                        continue
                    candidates.append(rel)
        except Exception:
            return []
        # Дедуп и ограничение
        out = self._unique_keep_order(candidates)
        return out[:12]

    def _expand_via_callgraph(self, seed_paths: List[str], keywords: Set[str]) -> Tuple[List[str], List[Tuple[str, str, str, str]]]:
        """Расширяет список файлов, используя call_graph_edges от pyan3.

        Возвращает (additional_paths, edges) где edges = [(caller_sym, callee_sym, caller_path, callee_path)].
        """
        add_paths: List[str] = []
        edges: List[Tuple[str, str, str, str]] = []
        if not self._index_engine:
            return add_paths, edges
        if not seed_paths and not keywords:
            return add_paths, edges
        try:
            with self._index_engine.connect() as conn:
                # Ищем связи по путям
                if seed_paths:
                    for p in seed_paths[:10]:
                        q = text(
                            """
                            SELECT source_symbol, target_symbol, file_path, line_number
                            FROM call_graph_edges
                            WHERE file_path LIKE :p
                            LIMIT 50
                            """
                        )
                        rows = conn.execute(q, {"p": f"%{p}%"}).fetchall()
                        for cs, es, fp, ln in rows:
                            edges.append((cs or "", es or "", fp or "", ""))
                            if fp:
                                add_paths.append(fp)
                # Ищем связи по символам (если есть ключевые слова на символы)
                sym_kw = [k for k in keywords if re.match(r"^[A-Za-z_][A-Za-z0-9_]+$", k or "")]
                for sym in sym_kw[:10]:
                    q = text(
                        """
                        SELECT source_symbol, target_symbol, file_path, line_number
                        FROM call_graph_edges
                        WHERE source_symbol LIKE :s OR target_symbol LIKE :s
                        LIMIT 50
                        """
                    )
                    rows = conn.execute(q, {"s": f"%{sym}%"}).fetchall()
                    for cs, es, fp, ln in rows:
                        edges.append((cs or "", es or "", fp or "", ""))
                        if fp:
                            add_paths.append(fp)
        except Exception:
            return [], []
        return add_paths, edges

    def _heuristic_paths_from_keywords(self, keywords: Set[str]) -> List[str]:
        paths: List[str] = []
        for k in keywords:
            if k.endswith((".py", ".tsx", ".ts", ".js", ".md", ".sql", ".sh")):
                if os.path.isabs(k):
                    paths.append(k)
                else:
                    # Пытаемся привязать к корню репо
                    candidate = os.path.join(REPO_ROOT, k)
                    if os.path.exists(candidate):
                        paths.append(k)  # сохраняем относительный к корню
        return paths

    def _read_files(self, paths: Iterable[str]) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        for p in paths:
            # Нормализуем путь
            abs_p = p if os.path.isabs(p) else os.path.join(REPO_ROOT, p)
            try:
                with open(abs_p, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    if len(content) > 100_000:
                        content = content[:100_000] + "\n...\n"
                    out.append((p, content))
            except Exception:
                # Пробуем без REPO_ROOT
                try:
                    with open(p, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                        if len(content) > 100_000:
                            content = content[:100_000] + "\n...\n"
                        out.append((p, content))
                except Exception:
                    continue
        return out

    def _unique_keep_order(self, items: Iterable[str]) -> List[str]:
        seen: Set[str] = set()
        out: List[str] = []
        for x in items:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out
