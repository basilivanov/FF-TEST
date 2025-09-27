from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import os
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
import asyncio
import structlog
from app.utils.secret_store import decrypt_value
try:
    from app.db.session import SessionLocal
except Exception:
    SessionLocal = None

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1")

class TelegramMessage(BaseModel):
    chat_id: str
    text: str
    parse_mode: Optional[str] = None

class TelegramTemplateMessage(BaseModel):
    chat_id: str
    template: str
    template_data: Dict[str, Any]
    parse_mode: Optional[str] = None

class TelegramResponse(BaseModel):
    ok: bool
    result: Optional[dict] = None
    error_code: Optional[int] = None
    description: Optional[str] = None

def get_bot_token() -> str:
    """Получить токен бота из ENV или Secret Store (fallback)."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        return token
    # Fallback к Secret Store
    try:
        if SessionLocal is None:
            raise RuntimeError("DB session unavailable")
        db = SessionLocal()
        try:
            row = db.execute(
                "SELECT value_enc FROM secrets WHERE key = :k",
                {"k": "TELEGRAM_BOT_TOKEN"},
            ).fetchone()
            if row and row[0]:
                return decrypt_value(row[0])
        finally:
            db.close()
    except Exception:
        pass
    raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN not configured")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10)
)
async def send_telegram_message_async(message: TelegramMessage, bot_token: str) -> TelegramResponse:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = message.dict(exclude_none=True)
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=3.0, read=10.0)) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return TelegramResponse(**data)
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error occurred while sending Telegram message", 
                        status_code=e.response.status_code, 
                        response_text=e.response.text)
            raise HTTPException(status_code=502, detail=f"Telegram API error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("Request error occurred while sending Telegram message", 
                        error=str(e))
            raise HTTPException(status_code=503, detail=f"Network error: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error occurred while sending Telegram message", 
                        error=str(e))
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10)
)
async def send_telegram_template_message_async(
    message: TelegramTemplateMessage, 
    bot_token: str
) -> TelegramResponse:
    """Send a templated message via Telegram."""
    try:
        # Format the template with provided data
        formatted_text = message.template.format(**message.template_data)
    except KeyError as e:
        logger.error("Missing template parameter", missing_key=str(e))
        raise HTTPException(status_code=400, detail=f"Missing template parameter: {e}")
    except Exception as e:
        logger.error("Failed to format template message", error=str(e))
        raise HTTPException(status_code=400, detail=f"Failed to format template: {str(e)}")
    
    # Create a regular message with the formatted text
    telegram_message = TelegramMessage(
        chat_id=message.chat_id,
        text=formatted_text,
        parse_mode=message.parse_mode
    )
    
    return await send_telegram_message_async(telegram_message, bot_token)

@router.post("/telegram/send-message", response_model=TelegramResponse)
async def send_message(message: TelegramMessage, bot_token: str = Depends(get_bot_token)):
    try:
        response = await send_telegram_message_async(message, bot_token)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send message", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to send message")

@router.post("/telegram/send-template-message", response_model=TelegramResponse)
async def send_template_message(message: TelegramTemplateMessage, bot_token: str = Depends(get_bot_token)):
    """Send a templated message via Telegram."""
    try:
        response = await send_telegram_template_message_async(message, bot_token)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send template message", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to send template message")
