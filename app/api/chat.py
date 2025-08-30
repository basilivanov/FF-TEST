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
        for m in tg_pat.findall(text):
            new_text = new_text.replace(m, _store_token(m))
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
            base_prompt = get_role_prompt("Maintainer", "chat_internal")
        else:
            base_prompt = get_role_prompt("Maintainer", "chat")
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
        
        # Вызов LLM
        llm_response_str = llm_router.completion(
            role="ChatMaintainer",
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

        # Пытаемся распарсить JSON; если не удаётся — используем как обычный текст
        try:
            llm_data = json.loads(content)
        except Exception:
            llm_data = {
                "response_for_user": content[:2000] if content else "Я вас слышу. Продолжайте, пожалуйста.",
                "action": {"type": "CONTINUE_DIALOG"}
            }
        
        print(f"[DEBUG] LLM response parsed: {llm_data}", file=sys.stderr)
        sys.stderr.flush()

        # Валидация ответа от LLM
        if not isinstance(llm_data, dict) or "response_for_user" not in llm_data:
            print(f"[DEBUG] Invalid LLM response structure: {llm_data}", file=sys.stderr)
            sys.stderr.flush()
            raise ValueError(f"Invalid response structure from LLM: missing required fields. Got: {list(llm_data.keys()) if isinstance(llm_data, dict) else type(llm_data)}")

        response_for_user = llm_data["response_for_user"]
        action = llm_data["action"]

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
                
                # Создаем фичу через вызов orchestrator_v2.create_feature
                feature_request = FeatureCreateRequest(
                    title=feature_title,
                    intent={"intent": intent_obj} if "intent" not in intent_payload_dict else intent_payload_dict,
                    autostart=True,
                    strict=True
                )
                
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
                
            except Exception as feature_creation_error:
                log.error(
                    "feature_creation_failed", 
                    error=str(feature_creation_error),
                    correlation_id=correlation_id
                )
                response_for_user += f"\n\n❌ К сожалению, произошла ошибка при регистрации задачи: {str(feature_creation_error)}\n"
                response_for_user += "Пожалуйста, попробуйте еще раз или обратитесь к администратору."

        history.append({"role": "assistant", "content": response_for_user})
        _save_history(db, session_id, history)

        return ConversationalChatResponse(
            response=response_for_user,
            history=history,
            correlation_id=correlation_id,
            session_id=session_id,
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
        return ConversationalChatResponse(
            response=busy_msg,
            history=history,
            correlation_id=correlation_id,
            session_id=session_id,
        )
