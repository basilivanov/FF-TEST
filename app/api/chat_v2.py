#!/usr/bin/env python3
"""
Обновленный диалоговый чат-эндпоинт для Maintainer v2.
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
        "database": "Управление базой данных"
    }
    
    name_lower = technical_name.lower()
    for tech_term, business_term in business_translations.items():
        if tech_term in name_lower:
            return technical_name.replace(tech_term.title(), business_term)
    
    return technical_name


class ConversationalChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class ConversationalChatResponse(BaseModel):
    response: str
    history: list[dict]
    correlation_id: str


@router.post("/maintainer/v2", response_model=ConversationalChatResponse)
async def chat_maintainer_v2(
    req: Request,
    payload: ConversationalChatRequest,
    db: Session = Depends(get_db)
) -> ConversationalChatResponse:
    """
    Ведет диалог с пользователем для сбора требований и создания фичи - версия 2.
    """
    correlation_id = generate_correlation_id()
    history = payload.history
    user_message = payload.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Empty message")

    # Добавляем сообщение пользователя в историю
    history.append({"role": "user", "content": user_message})

    # Если это первое сообщение, генерируем новое приветствие
    if len(history) == 1:
        try:
            done_features_result = db.execute(
                text("SELECT title FROM features WHERE status = 'DONE' ORDER BY created_at DESC LIMIT 3")
            )
            done_features = [row[0] for row in done_features_result]
            
            welcome_message = "Добро пожаловать! 👋\n\n"
            welcome_message += "Меня зовут Мейнтейнер, и я ваш помощник по автоматизации бизнес-процессов. "
            welcome_message += "Я могу помочь вам создать новые автоматизированные решения для вашего бизнеса.\n\n"
            
            if done_features:
                welcome_message += "У нас уже реализованы следующие возможности:\n"
                for feature in done_features:
                    # Переводим технические названия в бизнес-термины  
                    business_name = translate_to_business_terms(feature)
                    welcome_message += f"• {business_name}\n"
                welcome_message += "\n"
            
            welcome_message += "Расскажите мне, какую задачу вы хотели бы автоматизировать? "
            welcome_message += "Например:\n"
            welcome_message += "• Получать уведомления о чём-то важном\n"
            welcome_message += "• Собирать данные из различных источников\n"  
            welcome_message += "• Формировать отчёты автоматически\n"
            welcome_message += "• Интегрироваться с внешними сервисами\n\n"
            welcome_message += "Опишите своими словами, что вам нужно сделать?"

            history.append({"role": "assistant", "content": welcome_message})
            return ConversationalChatResponse(
                response=welcome_message,
                history=history,
                correlation_id=correlation_id
            )
        except Exception as e:
            log.error("db_fetch_done_features_failed", error=str(e))
            # Продолжаем без списка фич в случае ошибки
            welcome_message = "Добро пожаловать! 👋 Меня зовут Мейнтейнер, и я помогу вам создать новое автоматизированное решение для вашего бизнеса. Расскажите, что вам нужно?"
            history.append({"role": "assistant", "content": welcome_message})
            return ConversationalChatResponse(
                response=welcome_message,
                history=history,
                correlation_id=correlation_id
            )

    # Формируем бизнес-ориентированный системный промпт
    system_prompt = """
    Вы — Maintainer, бизнес-ассистент для автоматизации процессов. Вы общаетесь с бизнес-аналитиком или менеджером, который НЕ разбирается в технических деталях.

    ВАЖНО: 
    - Говорите простым языком, избегайте технических терминов
    - Используйте бизнес-ориентированные вопросы и формулировки
    - Максимально упрощайте процесс сбора требований
    - Предлагайте готовые решения с разумными дефолтами
    - Фокусируйтесь на бизнес-ценности и результате для пользователя

    Ваша задача:
    1. Понять БИЗНЕС-потребность пользователя (что он хочет автоматизировать)
    2. Уточнить ключевые детали (откуда брать данные, что делать, куда выводить результат)
    3. Предложить приоритет (срочно/важно/можно подождать)
    4. Получить подтверждение
    5. Создать техническое задание

    Стиль общения:
    - Дружелюбный и понятный 
    - Используйте эмодзи для наглядности
    - Задавайте конкретные вопросы с вариантами ответов
    - Переформулируйте технические требования в бизнес-термины

    Ваш ответ ВСЕГДА должен быть в формате JSON:
    {
      "response_for_user": "Дружелюбный ответ пользователю простым языком",
      "action": {
        "type": "CONTINUE_DIALOG | FINALIZE_AND_CREATE_FEATURE",
        "intent_payload": {
          // Заполняется только если type = FINALIZE_AND_CREATE_FEATURE
        }
      }
    }

    Схема intent_payload для финального создания:
    {
      "intent": {
        "title": "Короткое бизнес-название (без технических терминов)",
        "summary": "Подробное описание того, что нужно сделать, в бизнес-терминах с указанием источников данных, действий и результатов",
        "priority": "P1"
      },
      "package_contract": {
        "artifact_manifest": "BUSINESS_AUTOMATION.yaml"
      },
      "risks": ["Список возможных проблем или ограничений"],
      "next_actions": [
        {"action": "Спланировать техническую реализацию", "owner": "Architect"},
        {"action": "Реализовать автоматизацию", "owner": "Dev"}
      ]
    }
    """

    messages_for_llm = [{"role": "system", "content": system_prompt}] + history

    try:
        # Вызов LLM
        llm_response_str = llm_router.completion(
            role="Maintainer",
            messages=messages_for_llm,
            max_tokens=1024,
            temperature=0.3,
        )
        
        response_content = llm_response_str.choices[0].message.content
        
        # Очистка от возможных ```json ... ```
        if response_content.startswith("```json"):
            response_content = response_content[7:-3].strip()

        llm_data = json.loads(response_content)

        # Валидация ответа от LLM
        if not isinstance(llm_data, dict) or "response_for_user" not in llm_data or "action" not in llm_data:
            raise ValueError("Invalid response structure from LLM")

        response_for_user = llm_data["response_for_user"]
        action = llm_data["action"]

        if action.get("type") == "FINALIZE_AND_CREATE_FEATURE":
            intent_payload = action.get("intent_payload")
            if not intent_payload:
                raise ValueError("intent_payload is missing for FINALIZE_AND_CREATE_FEATURE action")

            try:
                # Извлекаем данные из intent_payload
                intent_data = intent_payload.get("intent", {})
                feature_title = intent_data.get("title", "Новая автоматизация")
                
                # Создаем фичу через вызов orchestrator_v2.create_feature
                feature_request = FeatureCreateRequest(
                    title=feature_title,
                    intent=intent_payload
                )
                
                # Создаем mock request для передачи в функцию
                mock_req = Request(scope={"type": "http", "headers": [], "method": "POST", "url": "/mock"})
                
                created_feature = await create_feature(mock_req, feature_request, db)
                
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
                    event="feature_created_via_chat_v2",
                    feature_id=created_feature.id,
                    feature_title=feature_title,
                    correlation_id=correlation_id
                )
                
            except Exception as feature_creation_error:
                log.error(
                    "feature_creation_failed_v2", 
                    error=str(feature_creation_error),
                    correlation_id=correlation_id
                )
                response_for_user += f"\n\n❌ К сожалению, произошла ошибка при регистрации задачи: {str(feature_creation_error)}\n"
                response_for_user += "Пожалуйста, попробуйте еще раз или обратитесь к администратору."

        history.append({"role": "assistant", "content": response_for_user})

        return ConversationalChatResponse(
            response=response_for_user,
            history=history,
            correlation_id=correlation_id
        )

    except Exception as e:
        log.error("maintainer_chat_v2_error", error=str(e))
        # Возвращаем ошибку, но сохраняем историю
        error_response = "К сожалению, произошла ошибка. Попробуйте еще раз."
        history.append({"role": "assistant", "content": error_response})
        return ConversationalChatResponse(
            response=error_response,
            history=history,
            correlation_id=correlation_id
        )