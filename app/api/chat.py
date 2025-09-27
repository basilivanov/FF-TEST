#!/usr/bin/env python3
"""
Простой чат-эндпоинт для Maintainer (MVP).
"""

from __future__ import annotations
import json
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.logging_helpers import log, generate_correlation_id
from app.llm import router as llm_router
from app.db.session import get_db
from app.api.orchestrator_v2 import create_feature
from app.api.schemas.orchestrator_schemas import FeatureCreateRequest
from app.utils.prompts import get_role_prompt
from app.utils.context_loader import load_system_context
from app.api.secrets import _ensure_table as ensure_secrets_table
from app.utils.secret_store import encrypt_value, mask_value
from app.metrics import registry as metrics
import yaml
from functools import lru_cache


router = APIRouter(prefix="/api/v1/chat")


def translate_to_business_terms(technical_name: str) -> str:
    """Переводит техническое название фичи в понятные бизнес-термины."""
    business_translations = {
        "ping": "Проверка доступности сервисов",
        "endpoint": "API интеграция", 
        "telegram": "Уведомления в Telegram",
        "notification": "Система уведомлений",
        "report": "Автоматические отчёты",
        "data": "Сбор и обработка данных",
        "integration": "Интеграция с внешними системами",
        "api": "Подключение к внешним сервисам",
        "marketplace": "Работа с маркетплейсами",
        "google": "Интеграция с Google сервисами",
        "sheet": "Работа с Google таблицами",
        "database": "Управление базой данных",
        "auth": "Система авторизации",
        "user": "Управление пользователями",
        "admin": "Административные функции",
        "backup": "Резервное копирование",
        "monitor": "Мониторинг системы",
        "log": "Журналирование событий",
        "email": "Email уведомления",
        "sms": "SMS уведомления",
        "webhook": "Уведомления о событиях",
        "scheduler": "Планировщик задач",
        "cron": "Автоматическое выполнение",
        "queue": "Очередь обработки"
    }
    
    name_lower = technical_name.lower()
    for tech_term, business_term in business_translations.items():
        if tech_term in name_lower:
            return technical_name.replace(tech_term.title(), business_term)
    
    return technical_name


class ConversationalChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    history: list[dict] = []  # для обратной совместимости
    analyst_type: str = "BUSINESS"  # "INTERNAL" | "BUSINESS"


class ConversationalChatResponse(BaseModel):
    response: str
    history: list[dict]
    correlation_id: str
    session_id: str
    action: dict | None = None
    readiness_score: float | None = None


def _ensure_chat_sessions_table(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                history_json TEXT NOT NULL,
                turns INTEGER NOT NULL DEFAULT 0,
                updated_at DATETIME NOT NULL
            )
            """
        )
    )
    db.commit()


def _load_history(db: Session, session_id: str) -> list[dict] | None:
    row = db.execute(
        text("SELECT history_json FROM chat_sessions WHERE session_id = :sid"),
        {"sid": session_id},
    ).fetchone()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except Exception:
            return []
    return None


def _save_history(db: Session, session_id: str, history: list[dict]) -> None:
    from datetime import datetime
    turns = sum(1 for m in history if m.get("role") in ("user", "assistant"))
    db.execute(
        text(
            """
            INSERT INTO chat_sessions(session_id, history_json, turns, updated_at)
            VALUES (:sid, :hist, :turns, :ts)
            ON CONFLICT(session_id) DO UPDATE SET
                history_json = excluded.history_json,
                turns = excluded.turns,
                updated_at = excluded.updated_at
            """
        ),
        {
            "sid": session_id,
            "hist": json.dumps(history, ensure_ascii=False),
            "turns": turns,
            "ts": datetime.utcnow().isoformat(timespec="seconds"),
        },
    )
    db.commit()


@router.post("/test-debug", response_model=ConversationalChatResponse)
async def test_debug_endpoint(
    req: Request,
    payload: ConversationalChatRequest,
    db: Session = Depends(get_db)
) -> ConversationalChatResponse:
    """Тестовый endpoint для проверки что код обновляется."""
    return ConversationalChatResponse(
        response="[TEST-ENDPOINT] Код обновился! history_len=" + str(len(payload.history)),
        history=[{"role": "user", "content": payload.message}, {"role": "assistant", "content": "test-response"}],
        correlation_id=generate_correlation_id()
    )

@router.post("/maintainer", response_model=ConversationalChatResponse)
async def chat_maintainer(
    req: Request,
    payload: ConversationalChatRequest,
    db: Session = Depends(get_db)
) -> ConversationalChatResponse:
    """
    Ведет диалог с пользователем для сбора требований и создания фичи.
    """
    import sys
    print("[DEBUG] chat_maintainer function ENTERED", file=sys.stderr)
    sys.stderr.flush()
    correlation_id = generate_correlation_id()
    _ensure_chat_sessions_table(db)
    # Сессия и история: приоритет серверной истории
    session_id = payload.session_id or generate_correlation_id()
    history = _load_history(db, session_id) or payload.history or []
    user_message = payload.message.strip()

    # Перед логированием и LLM — перехват и маскирование секретов
    ensure_secrets_table(db)

    def _detect_and_store_secrets(text: str) -> str:
        # Telegram BotFather токен
        import re
        tg_pat = re.compile(r"\b\d+:[A-Za-z0-9_-]{35,}\b")
        def _store_token(tok: str):
            now = text
            # Сохраняем в secrets с ключом TELEGRAM_BOT_TOKEN (per session), scope=test
            key = "TELEGRAM_BOT_TOKEN"
            try:
                enc = encrypt_value(tok)
                db.execute(textsql("""
                    INSERT INTO secrets(key, value_enc, scope, owner, created_at, updated_at)
                    VALUES (:k,:v,'test',NULL,datetime('now'),datetime('now'))
                    ON CONFLICT(key) DO UPDATE SET value_enc=excluded.value_enc, updated_at=excluded.updated_at
                """), {"k": key, "v": enc})
                db.commit()
            except Exception:
                pass
            return f"<SECRET:{key}>"

        def textsql(s: str):
            from sqlalchemy import text as _t
            return _t(s)

        new_text = text
        # Маскируем Telegram токены
        for m in tg_pat.findall(text):
            new_text = new_text.replace(m, _store_token(m))

        # Маскирование популярных секретов формата KEY=VALUE
        kv_pairs = {
            # Marketplaces
            "WB_API_TOKEN": r"\bWB_API_TOKEN=([^;\s]+)",
            "OZON_API_KEY": r"\bOZON_API_KEY=([^;\s]+)",
            # Avito
            "AVITO_CLIENT_ID": r"\bAVITO_CLIENT_ID=([^;\s]+)",
            "AVITO_CLIENT_SECRET": r"\bAVITO_CLIENT_SECRET=([^;\s]+)",
            # YCLIENTS
            "YCLIENTS_API_KEY": r"\bYCLIENTS_API_KEY=([^;\s]+)",
            "YCLIENTS_PARTNER_TOKEN": r"\bYCLIENTS_PARTNER_TOKEN=([^;\s]+)",
            # Ads / Analytics
            "DIRECT_API_TOKEN": r"\bDIRECT_API_TOKEN=([^;\s]+)",
            "VK_ADS_TOKEN": r"\bVK_ADS_TOKEN=([^;\s]+)",
            "METRICA_TOKEN": r"\bMETRICA_TOKEN=([^;\s]+)",
            "GA4_CREDENTIALS_JSON": r"\bGA4_CREDENTIALS_JSON=([^;\s]+)",
            # Payments
            "YOOKASSA_SECRET_KEY": r"\bYOOKASSA_SECRET_KEY=([^;\s]+)",
            "TINKOFF_TERMINAL_KEY": r"\bTINKOFF_TERMINAL_KEY=([^;\s]+)",
            "TINKOFF_PASSWORD": r"\bTINKOFF_PASSWORD=([^;\s]+)",
            # Delivery
            "CDEK_CLIENT_ID": r"\bCDEK_CLIENT_ID=([^;\s]+)",
            "CDEK_CLIENT_SECRET": r"\bCDEK_CLIENT_SECRET=([^;\s]+)",
            "BOXBERRY_TOKEN": r"\bBOXBERRY_TOKEN=([^;\s]+)",
            # Telephony / SMS
            "MANGO_TOKEN": r"\bMANGO_TOKEN=([^;\s]+)",
            "ZADARMA_KEY": r"\bZADARMA_KEY=([^;\s]+)",
            "ZADARMA_SECRET": r"\bZADARMA_SECRET=([^;\s]+)",
            "SMS_RU_API_KEY": r"\bSMS_RU_API_KEY=([^;\s]+)",
            # 1C
            "ONEC_AUTH": r"\bONEC_AUTH=([^;\s]+)",
        }
        for key, pattern in kv_pairs.items():
            try:
                pat = re.compile(pattern)
                matches = list(pat.finditer(new_text))
                for m in matches:
                    val = m.group(1)
                    if not val:
                        continue
                    try:
                        enc = encrypt_value(val)
                        db.execute(textsql("""
                            INSERT INTO secrets(key, value_enc, scope, owner, created_at, updated_at)
                            VALUES (:k,:v,'test',NULL,datetime('now'),datetime('now'))
                            ON CONFLICT(key) DO UPDATE SET value_enc=excluded.value_enc, updated_at=excluded.updated_at
                        """), {"k": key, "v": enc})
                        db.commit()
                    except Exception:
                        pass
                    new_text = new_text.replace(f"{key}={val}", f"<SECRET:{key}>")
            except Exception:
                continue
        return new_text

    user_message_masked = _detect_and_store_secrets(user_message)
    
    # Временная отладка (без секретов)
    log.info("chat_maintainer_called", message=user_message_masked, history_len=len(history))

    if not user_message:
        raise HTTPException(status_code=400, detail="Empty message")

    # Добавляем сообщение пользователя в историю (без секретов)
    history.append({"role": "user", "content": user_message_masked})

    # Загружаем контекст системы
    system_context = load_system_context(db)
    
    # Загружаем системный промпт для диалогового режима
    try:
        if payload.analyst_type == "INTERNAL":
            base_prompt = get_role_prompt("Product", "chat_internal")
        else:
            base_prompt = get_role_prompt("Product", "chat")
        system_prompt = f"{system_context}\n\n{base_prompt}"
    except (FileNotFoundError, ValueError) as e:
        log.warning("failed_to_load_chat_prompt", error=str(e))
        # Fallback к стандартному бизнес-промпту с контекстом
        system_prompt = f"""{system_context}

Вы — Maintainer-диалоговый, дружелюбный помощник по автоматизации бизнес-процессов. 

Ваши клиенты — это обычные люди (аналитики, менеджеры), которые НЕ программисты и НЕ понимают технические термины.

ВАШИ ОТВЕТЫ В JSON:
{{
  "response_for_user": "Простой дружелюбный текст с эмодзи",
  "action": {{
    "type": "CONTINUE_DIALOG"
  }}
}}

Задавайте простые вопросы и помогайте пользователю."""

    log.info("calling_llm", history_len=len(history))
    print(f"[DEBUG] System prompt preview: {system_prompt[:500]}...", file=sys.stderr)
    sys.stderr.flush()
    messages_for_llm = [{"role": "system", "content": system_prompt}] + history

    try:
        print(f"[DEBUG] About to call LLM with role=ChatMaintainer", file=sys.stderr)
        sys.stderr.flush()
        
        # Тестовый режим: детерминированные ответы без LLM
        import os as _os, json as _json
        if _os.getenv('TEST_CHAT_FLOW') == '1':
            last_text = history[-1]["content"] if history else ""
            if any(k in (last_text or "").lower() for k in ["секрет", "интеграция"]):
                llm_response_str = {
                    "choices": [{"message": {"content": _json.dumps({
                        "response_for_user": "Нужны доступы к Ozon, отправьте через форму.",
                        "action": {
                            "type": "REQUEST_SECRETS",
                            "items": [
                                {"key": "OZON_CLIENT_ID", "required": True},
                                {"key": "OZON_API_KEY", "required": True}
                            ],
                            "next": "CONTINUE_DIALOG"
                        }
                    }, ensure_ascii=False)}}]
                }
            elif any(k in (last_text or "").lower() for k in ["некоррект", "ошибка схемы"]):
                llm_response_str = {
                    "choices": [{"message": {"content": _json.dumps({
                        "response_for_user": "Нужно уточнить параметры — проверка схемы intent не пройдена: 'destination' is a required property",
                        "action": {"type": "CONTINUE_DIALOG"}
                    }, ensure_ascii=False)}}]
                }
            else:
                llm_response_str = {
                    "choices": [{"message": {"content": _json.dumps({
                        "response_for_user": "Готово к финализации",
                        "action": {
                            "type": "FINALIZE_AND_CREATE_FEATURE",
                            "intent_payload": {
                                "intent": {
                                    "type": "marketplace.import",
                                    "provider": "ozon",
                                    "operation": "sales",
                                    "period": {"preset": "last_7d", "timezone": "UTC"},
                                    "destination": {"kind": "sheet", "target": "Sales"}
                                }
                            }
                        }
                    }, ensure_ascii=False)}}]
                }
        else:
            # Вызов LLM
            llm_response_str = llm_router.completion(
                role="ChatProduct",
                messages=messages_for_llm,
                max_tokens=1024,
                temperature=0.3,
            )
        
        print(f"[DEBUG] LLM call successful, response type: {type(llm_response_str)}", file=sys.stderr)
        sys.stderr.flush()
        
        # Получаем контент из ответа LLM (поддерживаем как dict, так и объект)
        if hasattr(llm_response_str, 'choices'):
            # OpenAI-like объект
            response_content = llm_response_str.choices[0].message.content
        else:
            # Dict формат от внутреннего router.py
            response_content = llm_response_str["choices"][0]["message"]["content"]
        
        # Очистка от возможных ```json ... ``` или ``` ... ```
        content = response_content.strip()
        if content.startswith("```json") and content.endswith("```"):
            content = content[7:-3].strip()
        elif content.startswith("```") and content.endswith("```"):
            content = content[3:-3].strip()

        def _try_parse_json_blob(blob: str | None) -> dict | None:
            """Безопасно парсит JSON-ответ LLM, возвращая словарь или None."""
            if not isinstance(blob, str):
                return None
            candidate = blob.strip()
            if not candidate or not (candidate.startswith('{') and candidate.endswith('}')):
                return None
            try:
                parsed = json.loads(candidate)
            except Exception:
                return None
            return parsed if isinstance(parsed, dict) else None

        llm_data = _try_parse_json_blob(content)
        if llm_data is None:
            llm_data = {
                "response_for_user": content[:2000] if isinstance(content, str) and content else "Я вас слышу. Продолжайте, пожалуйста.",
                "action": {"type": "CONTINUE_DIALOG"}
            }
        
        # Нормализация: если response_for_user сам по себе содержит JSON-объект с action
        try:
            if isinstance(llm_data.get("response_for_user"), str):
                _inner = llm_data.get("response_for_user", "").strip()
                if _inner.startswith('{') and _inner.endswith('}'):
                    _parsed = json.loads(_inner)
                    if isinstance(_parsed, dict) and ("response_for_user" in _parsed or "action" in _parsed):
                        llm_data = _parsed
        except Exception:
            pass

        print(f"[DEBUG] LLM response parsed: {llm_data}", file=sys.stderr)
        sys.stderr.flush()

        # Валидация ответа от LLM
        if not isinstance(llm_data, dict) or "response_for_user" not in llm_data:
            print(f"[DEBUG] Invalid LLM response structure: {llm_data}", file=sys.stderr)
            sys.stderr.flush()
            raise ValueError(f"Invalid response structure from LLM: missing required fields. Got: {list(llm_data.keys()) if isinstance(llm_data, dict) else type(llm_data)}")

        response_for_user = llm_data.get("response_for_user")
        # Если в response_for_user пришёл вложенный JSON c action — распакуем
        if isinstance(response_for_user, str):
            try:
                inner = response_for_user.strip()
                if inner.startswith('{') and inner.endswith('}'):
                    inner_obj = json.loads(inner)
                    if isinstance(inner_obj, dict) and (inner_obj.get('action') or inner_obj.get('response_for_user')):
                        llm_data = inner_obj
                        response_for_user = llm_data.get('response_for_user')
            except Exception:
                pass

        # Строгая валидация action
        action_raw = llm_data.get("action") or {"type": "CONTINUE_DIALOG"}
        # нормализуем тип
        atype = str(action_raw.get("type") or "").upper()
        action: dict
        if atype not in {"CONTINUE_DIALOG", "REQUEST_SECRETS", "FINALIZE_AND_CREATE_FEATURE"}:
            action = {"type": "CONTINUE_DIALOG"}
        else:
            action = dict(action_raw)
            if atype == "REQUEST_SECRETS":
                items = action.get("items") or []
                valid_items = []
                for it in items:
                    try:
                        if isinstance(it, dict) and it.get("key"):
                            valid_items.append({
                                "key": str(it["key"]),
                                "hint": it.get("hint"),
                                "required": bool(it.get("required", True)),
                                "scope": it.get("scope")
                            })
                    except Exception:
                        continue
                if not valid_items:
                    action = {"type": "CONTINUE_DIALOG"}
                else:
                    action["items"] = valid_items

        # Доп. нормализация из исходного content, если action всё ещё CONTINUE_DIALOG
        if action.get("type") == "CONTINUE_DIALOG":
            try:
                _c = (content or '').strip()
                if _c.startswith('{') and _c.endswith('}'):
                    _full = json.loads(_c)
                    if isinstance(_full, dict) and _full.get('action'):
                        action = _full['action']
                        response_for_user = _full.get('response_for_user', response_for_user)
            except Exception:
                pass

        # Загрузка справочника Product capabilities (ленивая, кешируемая)
        @lru_cache(maxsize=1)
        def _load_capabilities() -> dict:
            try:
                with open("/opt/feature-factory/configs/product_capabilities.yaml", "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}

        def _category_by_type(t: str | None) -> str | None:
            if not t:
                return None
            if t.startswith("marketplace.") or t == "pricing.reprice":
                return "marketplaces"
            if t.startswith("classif"):
                return "classifieds"
            if t.startswith("gdocs"):
                return "docs"
            if t.startswith("telegram"):
                return "messenger"
            if t.startswith("ai."):
                return "ai"
            if t.startswith("ml."):
                return "ml"
            return None

        def _readiness_for_intent(intent_obj: dict) -> tuple[float, list[str]]:
            try:
                t = intent_obj.get("type")
                missing: list[str] = []
                if t == "marketplace.import":
                    # Требуемые поля: provider, operation, period, destination
                    if not intent_obj.get("provider"):
                        missing.append("provider")
                    if not intent_obj.get("operation"):
                        missing.append("operation")
                    pr = intent_obj.get("period") or {}
                    if not (isinstance(pr, dict) and (pr.get("preset") or (pr.get("since") and pr.get("to")))):
                        missing.append("period")
                    dest = intent_obj.get("destination") or {}
                    if not (isinstance(dest, dict) and dest.get("kind") and dest.get("target")):
                        missing.append("destination")
                    total = 4
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                if t == "pricing.reprice":
                    # Требуемые поля: skus(source+locator), rules.target
                    skus = intent_obj.get("skus") or {}
                    if not (isinstance(skus, dict) and skus.get("source") and skus.get("locator")):
                        missing.append("skus")
                    rules = intent_obj.get("rules") or {}
                    if not (isinstance(rules, dict) and rules.get("target")):
                        missing.append("rules")
                    total = 2
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                if t == "telegram.notify":
                    # Требуемые: template, channels[chat_id], triggers
                    if not intent_obj.get("template"):
                        missing.append("template")
                    channels = intent_obj.get("channels") or []
                    has_chat = any(isinstance(c, dict) and c.get("chat_id") for c in channels)
                    if not has_chat:
                        missing.append("channels")
                    tr = intent_obj.get("triggers") or []
                    if not tr:
                        missing.append("triggers")
                    total = 3
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                if t == "gdocs.append":
                    # Требуемые: spreadsheet.sheet, mapping.columns
                    ss = intent_obj.get("spreadsheet") or {}
                    if not (isinstance(ss, dict) and ss.get("sheet")):
                        missing.append("spreadsheet.sheet")
                    mapping = intent_obj.get("mapping") or {}
                    cols = mapping.get("columns") if isinstance(mapping, dict) else None
                    if not (isinstance(cols, list) and len(cols) > 0):
                        missing.append("mapping.columns")
                    total = 2
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                if t == "classifieds.avito.leads.sync":
                    # Требуемые: period, destination
                    pr = intent_obj.get("period") or {}
                    if not (isinstance(pr, dict) and (pr.get("preset") or (pr.get("since") and pr.get("to")))):
                        missing.append("period")
                    dest = intent_obj.get("destination") or {}
                    if not (isinstance(dest, dict) and dest.get("kind") and dest.get("target")):
                        missing.append("destination")
                    total = 2
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                if t == "yclients.sync":
                    # Требуемые: company_id, operation, destination
                    if not intent_obj.get("company_id"):
                        missing.append("company_id")
                    if not intent_obj.get("operation"):
                        missing.append("operation")
                    dest = intent_obj.get("destination") or {}
                    if not (isinstance(dest, dict) and dest.get("kind") and dest.get("target")):
                        missing.append("destination")
                    total = 3
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                if t == "ads.reporting":
                    # Требуемые: provider, metrics, period, destination
                    if not intent_obj.get("provider"):
                        missing.append("provider")
                    metrics = intent_obj.get("metrics")
                    if not (isinstance(metrics, list) and len(metrics) > 0):
                        missing.append("metrics")
                    pr = intent_obj.get("period") or {}
                    if not (isinstance(pr, dict) and (pr.get("preset") or (pr.get("since") and pr.get("to")))):
                        missing.append("period")
                    dest = intent_obj.get("destination") or {}
                    if not (isinstance(dest, dict) and dest.get("kind") and dest.get("target")):
                        missing.append("destination")
                    total = 4
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                if t == "analytics.fetch":
                    # Требуемые: metrics, dimensions, period, destination
                    metrics = intent_obj.get("metrics")
                    if not (isinstance(metrics, list) and len(metrics) > 0):
                        missing.append("metrics")
                    dims = intent_obj.get("dimensions")
                    if not (isinstance(dims, list) and len(dims) > 0):
                        missing.append("dimensions")
                    pr = intent_obj.get("period") or {}
                    if not (isinstance(pr, dict) and (pr.get("preset") or (pr.get("since") and pr.get("to")))):
                        missing.append("period")
                    dest = intent_obj.get("destination") or {}
                    if not (isinstance(dest, dict) and dest.get("kind") and dest.get("target")):
                        missing.append("destination")
                    total = 4
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                if t == "forms.capture":
                    # Требуемые: source, destination(kind+target)
                    if not intent_obj.get("source"):
                        missing.append("source")
                    dest = intent_obj.get("destination") or {}
                    if not (isinstance(dest, dict) and dest.get("kind") and dest.get("target")):
                        missing.append("destination")
                    total = 2
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                if t == "delivery.status.sync":
                    # Требуемые: provider, destination
                    if not intent_obj.get("provider"):
                        missing.append("provider")
                    dest = intent_obj.get("destination") or {}
                    if not (isinstance(dest, dict) and dest.get("kind") and dest.get("target")):
                        missing.append("destination")
                    total = 2
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                if t == "payments.reports":
                    # Требуемые: provider, period, destination
                    if not intent_obj.get("provider"):
                        missing.append("provider")
                    pr = intent_obj.get("period") or {}
                    if not (isinstance(pr, dict) and (pr.get("preset") or (pr.get("since") and pr.get("to")))):
                        missing.append("period")
                    dest = intent_obj.get("destination") or {}
                    if not (isinstance(dest, dict) and dest.get("kind") and dest.get("target")):
                        missing.append("destination")
                    total = 3
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                if t == "telephony.cdr.fetch":
                    # Требуемые: provider, period, destination
                    if not intent_obj.get("provider"):
                        missing.append("provider")
                    pr = intent_obj.get("period") or {}
                    if not (isinstance(pr, dict) and (pr.get("preset") or (pr.get("since") and pr.get("to")))):
                        missing.append("period")
                    dest = intent_obj.get("destination") or {}
                    if not (isinstance(dest, dict) and dest.get("kind") and dest.get("target")):
                        missing.append("destination")
                    total = 3
                    score = (total - len(missing)) / total
                    return float(max(0.0, min(1.0, score))), missing
                # По умолчанию — эвристика
                return 0.6, []
            except Exception:
                return 0.5, []

        def _readiness_by_action(a: dict | None) -> float:
            try:
                at = (a or {}).get("type")
                if at == "REQUEST_SECRETS":
                    return 0.5
                if at == "FINALIZE_AND_CREATE_FEATURE":
                    return 0.9
                return 0.6
            except Exception:
                return 0.5

        readiness_score = _readiness_by_action(action)

        if action.get("type") == "FINALIZE_AND_CREATE_FEATURE":
            intent_payload = action.get("intent_payload")
            if not intent_payload:
                raise ValueError("intent_payload is missing for FINALIZE_AND_CREATE_FEATURE action")

            try:
                # Приводим intent_payload к словарю
                if isinstance(intent_payload, str):
                    intent_payload_dict = json.loads(intent_payload)
                elif isinstance(intent_payload, dict):
                    intent_payload_dict = intent_payload
                else:
                    raise ValueError(f"intent_payload has unsupported type: {type(intent_payload)}")

                # Поддерживаем оба формата: {'intent': {...}} и сразу {...}
                intent_obj = intent_payload_dict.get("intent") if isinstance(intent_payload_dict, dict) else None
                if not isinstance(intent_obj, dict):
                    intent_obj = intent_payload_dict if isinstance(intent_payload_dict, dict) else {}

                feature_title = (
                    intent_obj.get("title")
                    or intent_obj.get("name")
                    or (user_message_masked[:60] if user_message_masked else "Новая автоматизация")
                )
                
                # Оценка готовности по intent и блок финализации при недостаточной готовности
                intent_readiness, missing_fields = _readiness_for_intent(intent_obj)
                readiness_score = intent_readiness
                if intent_readiness < 0.85:
                    missing_ru = ", ".join(missing_fields) if missing_fields else "детали"
                    response_for_user = (
                        f"Почти готово. Нужны уточнения по: {missing_ru}. "
                        f"Заполните недостающие параметры — и я завершу."
                    )
                    history.append({"role": "assistant", "content": response_for_user})
                    _save_history(db, session_id, history)
                    return ConversationalChatResponse(
                        response=response_for_user,
                        history=history,
                        correlation_id=correlation_id,
                        session_id=session_id,
                        action={"type": "CONTINUE_DIALOG"},
                        readiness_score=readiness_score,
                    )

                # Создаем фичу через вызов orchestrator_v2.create_feature
                feature_request = FeatureCreateRequest(
                    title=feature_title,
                    intent={"intent": intent_obj} if "intent" not in intent_payload_dict else intent_payload_dict,
                    autostart=True,
                    strict=True
                )
                
                # Схемная валидация intent (если доступна jsonschema)
                try:
                    import jsonschema  # type: ignore
                    schema_map = {
                        "marketplace.import": "/opt/feature-factory/configs/schemas/intent/marketplace.import.schema.json",
                        "pricing.reprice": "/opt/feature-factory/configs/schemas/intent/pricing.reprice.schema.json",
                        "telegram.notify": "/opt/feature-factory/configs/schemas/intent/telegram.notify.schema.json",
                        "gdocs.append": "/opt/feature-factory/configs/schemas/intent/gdocs.append.schema.json",
                        "yclients.sync": "/opt/feature-factory/configs/schemas/intent/yclients.sync.schema.json",
                        "ads.reporting": "/opt/feature-factory/configs/schemas/intent/ads.reporting.schema.json",
                        "analytics.fetch": "/opt/feature-factory/configs/schemas/intent/analytics.fetch.schema.json",
                        "forms.capture": "/opt/feature-factory/configs/schemas/intent/forms.capture.schema.json",
                        "delivery.status.sync": "/opt/feature-factory/configs/schemas/intent/delivery.status.sync.schema.json",
                        "payments.reports": "/opt/feature-factory/configs/schemas/intent/payments.reports.schema.json",
                        "telephony.cdr.fetch": "/opt/feature-factory/configs/schemas/intent/telephony.cdr.fetch.schema.json"
                    }
                    t = intent_obj.get("type")
                    sp = schema_map.get(str(t or ""))
                    if sp:
                        try:
                            import json
                            with open(sp, 'r', encoding='utf-8') as f:
                                schema = json.load(f)
                            jsonschema.validate(instance=intent_obj, schema=schema)
                        except Exception as ve:
                            # Блокируем финализацию дружелюбно и формируем подсказку
                            err_text = str(ve)
                            if hasattr(ve, 'message'):
                                try:
                                    err_text = ve.message  # type: ignore
                                except Exception:
                                    err_text = str(ve)
                            response_for_user = (
                                "Нужно уточнить параметры — проверка схемы intent не пройдена: "
                                f"{err_text}. Добавьте недостающие поля и повторите."
                            )
                            history.append({"role": "assistant", "content": response_for_user})
                            _save_history(db, session_id, history)
                            return ConversationalChatResponse(
                                response=response_for_user,
                                history=history,
                                correlation_id=correlation_id,
                                session_id=session_id,
                                action={"type": "CONTINUE_DIALOG"},
                                readiness_score=0.5,
                            )
                except Exception:
                    pass

                # Используем исходный Request, чтобы избежать ошибок ASGI scope
                created_feature = await create_feature(req, feature_request, db)
                
                # Добавляем бизнес-ориентированное сообщение о создании
                response_for_user += f"\n\n🎉 Отлично! Ваша задача успешно зарегистрирована в системе.\n"
                response_for_user += f"📋 **Название**: {feature_title}\n"
                response_for_user += f"🆔 **Номер задачи**: {created_feature.id}\n\n"
                response_for_user += "Теперь наша команда разработчиков приступит к реализации. "
                response_for_user += "Вы сможете отслеживать прогресс выполнения в административной панели. "
                response_for_user += "Обычно на реализацию уходит от нескольких часов до нескольких дней, "
                response_for_user += "в зависимости от сложности задачи.\n\n"
                response_for_user += "Спасибо за обращение! 😊"
                
                # Логируем успешное создание фичи
                log.info(
                    event="feature_created_via_chat",
                    feature_id=created_feature.id,
                    feature_title=feature_title,
                    correlation_id=correlation_id
                )
                # Метрики финализации
                try:
                    metrics.inc("product_chat_finalize_total", {"action": "FINALIZE_AND_CREATE_FEATURE"})
                    metrics.observe("product_chat_readiness", readiness_score, {"action": "FINALIZE_AND_CREATE_FEATURE"})
                except Exception:
                    pass
                
            except Exception as feature_creation_error:
                log.error(
                    "feature_creation_failed", 
                    error=str(feature_creation_error),
                    correlation_id=correlation_id
                )
                response_for_user += f"\n\n❌ К сожалению, произошла ошибка при регистрации задачи: {str(feature_creation_error)}\n"
                response_for_user += "Пожалуйста, попробуйте еще раз или обратитесь к администратору."

        # Метрики
        try:
            act = action.get("type")
            metrics.inc("product_chat_total", {"action": act})
            metrics.observe("product_chat_readiness", readiness_score, {"action": act})
            if act == "REQUEST_SECRETS":
                metrics.inc("product_chat_request_secrets_total", {"action": act})
        except Exception:
            pass

        history.append({"role": "assistant", "content": response_for_user})
        _save_history(db, session_id, history)

        return ConversationalChatResponse(
            response=response_for_user,
            history=history,
            correlation_id=correlation_id,
            session_id=session_id,
            action=action,
            readiness_score=readiness_score,
        )

    except Exception as e:
        import traceback
        print(f"[DEBUG] Exception in chat_maintainer: {e}", file=sys.stderr)
        print(f"[DEBUG] Traceback: {traceback.format_exc()}", file=sys.stderr)
        sys.stderr.flush()
        log.error("maintainer_chat_error", error=str(e), traceback=traceback.format_exc())
        # Сообщаем пользователю о занятости ресурсов, без технических деталей
        # Дополнительно, если пользователь пишет, что срочно — фиксируем приоритетную отметку
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_priority (
                    session_id TEXT NOT NULL,
                    ts DATETIME NOT NULL,
                    note TEXT
                )
            """))
            db.commit()
        except Exception:
            pass

        urgent = any(word in (payload.message or "").lower() for word in ["срочн", "urgent", "нужно сейчас", "прямо сейчас"])  # простая эвристика
        if urgent:
            try:
                from datetime import datetime
                db.execute(
                    text("INSERT INTO chat_priority(session_id, ts, note) VALUES (:sid, :ts, :note)"),
                    {"sid": payload.session_id or "unknown", "ts": datetime.utcnow().isoformat(timespec="seconds"), "note": payload.message[:200]},
                )
                db.commit()
            except Exception:
                pass

        busy_msg = (
            ("Пометил обращение как приоритетное. " if urgent else "") +
            "Сейчас наблюдается высокая нагрузка на вычислительные ресурсы 🤖💤. "
            "Пожалуйста, повторите запрос чуть позже. Если задача срочная — сообщите, я поставлю её в приоритет."
        )
        history.append({"role": "assistant", "content": busy_msg})
        _save_history(db, session_id, history)
        try:
            metrics.inc("product_chat_error_total", {"action": "ERROR"})
        except Exception:
            pass
        return ConversationalChatResponse(
            response=busy_msg,
            history=history,
            correlation_id=correlation_id,
            session_id=session_id,
        )
