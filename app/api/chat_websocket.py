from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.logging_helpers import log, generate_correlation_id
from app.llm.router import completion # Будем использовать completion, но теперь с session_id
from app.llm.session_manager import LLMSessionManager # Новый импорт
from app.utils.context_loader import load_system_context
from app.utils.prompts import get_role_prompt
from app.api.orchestrator_v2 import create_feature # Для обработки FINALIZE_AND_CREATE_FEATURE
from app.api.schemas.orchestrator_schemas import FeatureCreateRequest
import json
import asyncio
from datetime import datetime # Для сохранения истории

router = APIRouter(prefix="/ws/v1/chat")

llm_session_manager = LLMSessionManager() # Создаем экземпляр менеджера сессий

# Функции для работы с историей чата (скопированы из app/api/chat.py)
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


@router.websocket("/maintainer")
async def websocket_maintainer_chat(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    session_id = None
    
    _ensure_chat_sessions_table(db) # Убедимся, что таблица существует
    
    # Ожидаем первого сообщения для получения или создания session_id
    try:
        initial_data = await websocket.receive_text()
        initial_payload = json.loads(initial_data)
        
        # Попытаемся получить существующий session_id из клиента
        session_id = initial_payload.get("session_id")
        if not session_id:
            # Генерируем новый session_id если не передан
            session_id = generate_correlation_id()
            log.info(f"Generated new WebSocket session: {session_id}")
        else:
            log.info(f"Resumed WebSocket session: {session_id}")
            
        # Загружаем историю чата из БД
        history = _load_history(db, session_id) or []
        
        # Отправляем подтверждение подключения с session_id
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "history": history
        })
        
        # Обрабатываем первое сообщение сразу, если это не просто handshake
        if initial_payload.get("message"):
            await process_message(websocket, db, session_id, history, initial_payload)
            
    except Exception as e:
        log.error(f"WebSocket handshake failed: {e}")
        await websocket.close(code=1011, reason="Handshake failed")
        return

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            await process_message(websocket, db, session_id, history, payload)
            
    except WebSocketDisconnect:
        log.info(f"WebSocket disconnected: {session_id}")
        # НЕ освобождаем LLM-инстанс при отключении, чтобы сохранить persistent соединение
        # llm_session_manager.release_llm_adapter(session_id)
    except Exception as e:
        log.error("websocket_general_error", error=str(e), session_id=session_id)
        
async def process_message(websocket: WebSocket, db: Session, session_id: str, history: list, payload: dict):
    """Обрабатывает входящее сообщение от WebSocket клиента."""
    user_message = payload.get("message", "").strip()
    analyst_type = payload.get("analyst_type", "BUSINESS")

    if not user_message:
        await websocket.send_json({"response": "Empty message", "type": "error"})
        return

    log.info("chat_maintainer_websocket_message", message=user_message, session_id=session_id)

    # Добавляем сообщение пользователя в историю
    history.append({"role": "user", "content": user_message})

    # Загружаем контекст системы
    system_context = load_system_context(db)
    
    # Загружаем системный промпт для диалогового режима
    try:
        if analyst_type == "INTERNAL":
            base_prompt = get_role_prompt("Maintainer", "chat_internal")
        else:
            base_prompt = get_role_prompt("Maintainer", "chat")
        system_prompt = f"{system_context}\\n\\n{base_prompt}"
    except (FileNotFoundError, ValueError) as e:
        log.warning("failed_to_load_chat_prompt", error=str(e))
        system_prompt = f"""{system_context}\\n\\nВы — Maintainer-диалоговый, дружелюбный помощник по автоматизации бизнес-процессов."""

    messages_for_llm = [{"role": "system", "content": system_prompt}] + history

    try:
        # Вызов LLM для чата - используем ChatMaintainer как в HTTP чате
        llm_response_str = completion(
            role="ChatMaintainer",
            messages=messages_for_llm,
            max_tokens=1024,
            temperature=0.3,
            session_id=session_id
        )
        
        # Получаем контент из ответа LLM
        if hasattr(llm_response_str, 'choices'):
            response_content = llm_response_str.choices[0].message.content
        else:
            response_content = llm_response_str["choices"][0]["message"]["content"]
        
        # Очистка от возможных ```json ... ``` или ``` ... ```
        content = response_content.strip()
        if content.startswith("```json") and content.endswith("```"):
            content = content[7:-3].strip()
        elif content.startswith("```") and content.endswith("```"):
            content = content[3:-3].strip()

        try:
            llm_data = json.loads(content)
        except Exception:
            llm_data = {
                "response_for_user": content[:2000] if content else "Я вас слышу. Продолжайте, пожалуйста.",
                "action": {"type": "CONTINUE_DIALOG"}
            }
        
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
                    or (user_message[:60] if user_message else "Новая автоматизация")
                )
                
                # Создаем фичу через вызов orchestrator_v2.create_feature
                feature_request = FeatureCreateRequest(
                    title=feature_title,
                    intent={"intent": intent_obj} if "intent" not in intent_payload_dict else intent_payload_dict,
                    autostart=True,
                    strict=True
                )
                
                # Создаем фиктивный Request объект для create_feature
                # В реальном приложении, возможно, потребуется более сложная имитация Request
                mock_request = Request(scope={"type": "http", "asgi": {"version": "3.0", "spec_version": "2.1"}})
                
                created_feature = await create_feature(mock_request, feature_request, db)
                
                response_for_user += f"\\n\\n🎉 Отлично! Ваша задача успешно зарегистрирована в системе.\\n"
                response_for_user += f"📋 **Название**: {feature_title}\\n"
                response_for_user += f"🆔 **Номер задачи**: {created_feature.id}\\n\\n"
                response_for_user += "Теперь наша команда разработчиков приступит к реализации. "
                response_for_user += "Вы сможете отслеживать прогресс выполнения в административной панели. "
                response_for_user += "Обычно на реализацию уходит от нескольких часов до нескольких дней, "
                response_for_user += "в зависимости от сложности задачи.\\n\\n"
                response_for_user += "Спасибо за обращение! 😊"
                
                log.info(
                    event="feature_created_via_chat_websocket", 
                    feature_id=created_feature.id,
                    feature_title=feature_title,
                    correlation_id=generate_correlation_id()
                )
                
                # Освобождаем LLM-инстанс после деплоя фичи, так как задача завершена
                llm_session_manager.release_llm_adapter(session_id)
                log.info(f"Released LLM adapter for completed feature deployment, session: {session_id}")

            except Exception as feature_creation_error:
                log.error(
                    "feature_creation_failed_websocket", 
                    error=str(feature_creation_error),
                    correlation_id=generate_correlation_id()
                )
                response_for_user += f"\\n\\n❌ К сожалению, произошла ошибка при регистрации задачи: {str(feature_creation_error)}\\n"
                response_for_user += "Пожалуйста, попробуйте еще раз или обратитесь к администратору."

        history.append({"role": "assistant", "content": response_for_user})
        _save_history(db, session_id, history) # Сохраняем историю в БД

        await websocket.send_json({
            "response": response_for_user,
            "history": history,
            "correlation_id": generate_correlation_id(),
            "session_id": session_id,
            "action": action
        })

    except Exception as e:
        log.error("maintainer_chat_websocket_error", error=str(e), session_id=session_id)
        await websocket.send_json({"response": f"Произошла ошибка: {str(e)}", "type": "error"})