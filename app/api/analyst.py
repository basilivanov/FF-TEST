#!/usr/bin/env python3
"""
API для аналитиков - создание интентов через InternalAnalyst или BusinessAnalyst.
"""

import time
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel, model_validator

from app.logging_helpers import log, get_env, generate_correlation_id
from app.db.session import get_db
from app.llm.router import completion, RETRYABLE_ERROR
from app.utils.prompts import load_prompt_content
from app.utils.feature_templates import find_template_for_query, get_discovery_questions

# Создаем роутер 
router = APIRouter(prefix="/api/v1/analyst")

class AnalystCreateIntentRequest(BaseModel):
    """Схема запроса для создания интента через аналитика."""
    text: str
    type: str  # "INTERNAL" | "BUSINESS"
    
    @model_validator(mode='after')
    def validate_request(self):
        if not self.text or not self.text.strip():
            raise ValueError("text is required and cannot be empty")
        if self.type not in ['INTERNAL', 'BUSINESS']:
            raise ValueError("type must be either 'INTERNAL' or 'BUSINESS'")
        self.text = self.text.strip()
        return self

class AnalystCreateIntentResponse(BaseModel):
    """Схема ответа от аналитика."""
    feature_id: int
    status: str
    type: str
    title: str
    intent: Dict[str, Any]
    interpretation: str

def get_correlation_id(request: Request) -> str:
    """Получает correlation_id из заголовков запроса."""
    return request.headers.get("x-correlation-id", generate_correlation_id())

@router.post("/create-intent", response_model=AnalystCreateIntentResponse)
async def create_intent(
    request: Request,
    data: AnalystCreateIntentRequest,
    db: Session = Depends(get_db)
):
    """
    Создать intent через аналитика (внутреннего или бизнес).
    
    Args:
        request: HTTP запрос
        data: Данные запроса в формате {"text": "...", "type": "INTERNAL|BUSINESS"}
        db: Сессия БД
        
    Returns:
        Dict: Созданная фича с интентом
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    env = get_env()
    
    try:
        # Валидируем входные данные - data уже является AnalystCreateIntentRequest
        req = data
        
        # Логируем начало вызова
        log.info(
            event="analyst_api_call_start",
            env=env,
            component="api",
            agent_role=f"{req.type.lower().capitalize()}Analyst",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_path": str(request.url.path),
                "analyst_type": req.type,
                "text_length": len(req.text)
            }
        )
        
        # Определяем роль аналитика
        analyst_role = "InternalAnalyst" if req.type == "INTERNAL" else "BusinessAnalyst"
        
        # Загружаем промпт  
        try:
            prompt_filename = "internal_analyst.md" if req.type == "INTERNAL" else "business_analyst.md"
            prompt_content = load_prompt_content(prompt_filename)
        except Exception as e:
            log.error(
                event="prompt_load_failed",
                env=env,
                component="api", 
                agent_role=analyst_role,
                correlation_id=correlation_id,
                error=str(e)
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to load analyst prompt"
            )
        
        # Для BusinessAnalyst используем двухрежимную логику
        user_message = req.text
        if req.type == "BUSINESS":
            try:
                # Ищем подходящий шаблон
                template, extracted_data = find_template_for_query(req.text)
                
                if template:
                    # Режим 1: Найден шаблон
                    log.info(
                        event="template_found",
                        env=env,
                        component="api",
                        agent_role=analyst_role,
                        correlation_id=correlation_id,
                        kv={
                            "template_name": template.name,
                            "template_category": template.category,
                            "extracted_data": extracted_data
                        }
                    )
                    
                    # Проверяем недостающие обязательные поля
                    missing_slots = template.get_missing_slots(extracted_data)
                    
                    if missing_slots:
                        # Генерируем вопросы для недостающих полей
                        questions = template.generate_questions(missing_slots)
                        questions_text = "\n".join([f"• {q}" for q in questions])
                        
                        user_message = f"""ШАБЛОН НАЙДЕН: {template.name}
                        
Пользователь запросил: {req.text}

ИЗВЛЕЧЕННЫЕ ДАННЫЕ: {json.dumps(extracted_data, ensure_ascii=False, indent=2)}

НЕДОСТАЮЩИЕ ОБЯЗАТЕЛЬНЫЕ ПОЛЯ: {missing_slots}

ВОПРОСЫ ДЛЯ УТОЧНЕНИЯ:
{questions_text}

ИНСТРУКЦИЯ: Используй Режим 1 (шаблонный). Задай эти вопросы пользователю в дружелюбном формате, объясни что нашел подходящий шаблон "{template.name}" и нужно уточнить детали."""
                    else:
                        # Все данные есть, можно создавать интент
                        user_message = f"""ШАБЛОН НАЙДЕН: {template.name}

Пользователь запросил: {req.text}

ИЗВЛЕЧЕННЫЕ ДАННЫЕ: {json.dumps(extracted_data, ensure_ascii=False, indent=2)}

ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ: {json.dumps(template.technical_spec, ensure_ascii=False, indent=2)}

ИНСТРУКЦИЯ: Используй Режим 1 (шаблонный). Создай готовый интент на основе шаблона и данных."""
                else:
                    # Режим 2: Протокол Обнаружения
                    log.info(
                        event="template_not_found_discovery_mode",
                        env=env,
                        component="api",
                        agent_role=analyst_role,
                        correlation_id=correlation_id,
                        kv={"extracted_data": extracted_data}
                    )
                    
                    discovery_questions = get_discovery_questions()
                    questions_text = "\n".join(discovery_questions)
                    
                    user_message = f"""ШАБЛОН НЕ НАЙДЕН - активирую Протокол Обнаружения

Пользователь запросил: {req.text}

БАЗОВЫЕ ДАННЫЕ: {json.dumps(extracted_data, ensure_ascii=False, indent=2)}

ВОПРОСЫ ПРОТОКОЛА ОБНАРУЖЕНИЯ:
{questions_text}

ИНСТРУКЦИЯ: Используй Режим 2 (Протокол Обнаружения). Задай эти вопросы в дружелюбном формате, объясни что это новый тип интеграции и нужно собрать детали."""
                    
            except Exception as e:
                log.warning(
                    event="template_processing_failed",
                    env=env,
                    component="api",
                    agent_role=analyst_role,
                    correlation_id=correlation_id,
                    error=str(e)
                )
                # Fallback к стандартной обработке
                user_message = req.text
        
        # Готовим сообщения для LLM
        messages = [
            {"role": "system", "content": prompt_content},
            {"role": "user", "content": user_message}
        ]
        
        # Вызываем LLM через роутер
        try:
            llm_response = completion(
                role=analyst_role,
                messages=messages,
                max_tokens=2000,
                temperature=0.1,
                timeout_s=45
            )
            
            if llm_response.get("error"):
                log.error(
                    event="llm_completion_failed",
                    env=env,
                    component="api",
                    agent_role=analyst_role,
                    correlation_id=correlation_id,
                    error=llm_response["error"]
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM completion failed: {llm_response['error']}"
                )
            
            # Парсим ответ LLM
            try:
                # Извлекаем content из структуры choices или напрямую
                content = llm_response.get("content") or llm_response.get("choices", [{}])[0].get("message", {}).get("content", "")
                intent_data = json.loads(content)
            except json.JSONDecodeError as e:
                log.error(
                    event="intent_parse_failed",
                    env=env,
                    component="api",
                    agent_role=analyst_role,
                    correlation_id=correlation_id,
                    error=str(e),
                    content=content
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to parse LLM response as JSON"
                )
            
        except Exception as e:
            log.error(
                event="llm_call_failed",
                env=env,
                component="api",
                agent_role=analyst_role,
                correlation_id=correlation_id,
                error=str(e)
            )
            raise HTTPException(
                status_code=500,
                detail=f"LLM call failed: {str(e)}"
            )
        
        # Создаем фичу в БД
        try:
            intent_json = json.dumps(intent_data.get("intent", intent_data), ensure_ascii=False)
            title = intent_data.get("intent", {}).get("title", req.text[:100])
            
            create_feature_query = text("""
                INSERT INTO features (title, intent_json, status, created_by, env, type, created_at)
                VALUES (:title, :intent_json, 'NEW', :created_by, :env, :type, :created_at)
                RETURNING id
            """)
            
            result = db.execute(create_feature_query, {
                "title": title,
                "intent_json": intent_json,
                "created_by": "analyst_api",
                "env": env,
                "type": req.type,
                "created_at": datetime.utcnow()
            })
            
            feature_id = result.fetchone()[0]
            db.commit()
            
            # Логируем успешное создание
            log.info(
                event="feature_created_by_analyst",
                env=env,
                component="api",
                agent_role=analyst_role,
                correlation_id=correlation_id,
                kv={
                    "feature_id": feature_id,
                    "feature_type": req.type,
                    "title": title,
                    "duration_ms": (time.time() - start_time) * 1000
                }
            )
            
            return {
                "feature_id": feature_id,
                "status": "NEW",
                "type": req.type,
                "title": title,
                "intent": intent_data.get("intent", intent_data),
                "interpretation": intent_data.get("interpretation", "")
            }
            
        except Exception as e:
            db.rollback()
            log.error(
                event="feature_creation_failed",
                env=env,
                component="api",
                agent_role=analyst_role,
                correlation_id=correlation_id,
                error=str(e)
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create feature: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log.error(
            event="analyst_api_unexpected_error",
            env=env,
            component="api",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )