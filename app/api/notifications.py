from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1")


class TelegramMessage(BaseModel):
    chat_id: int
    text: str
    parse_mode: Optional[str] = None


class TelegramResponse(BaseModel):
    ok: bool
    result: Optional[dict] = None
    error_code: Optional[int] = None
    description: Optional[str] = None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=5, max=120),
)
async def send_telegram_message_with_retry(bot_token: str, message: TelegramMessage) -> TelegramResponse:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    timeout = httpx.Timeout(connect=3.0, read=10.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(url, json=message.dict())
            response.raise_for_status()
            data = response.json()
            return TelegramResponse(**data)
        except httpx.RequestError as e:
            await logger.awarning("Failed to send Telegram message", error=str(e))
            raise
        except Exception as e:
            await logger.aerror("Unexpected error when sending Telegram message", error=str(e))
            raise


@router.post("/notifications/telegram")
async def send_telegram_notification(message: TelegramMessage, bot_token: str):
    try:
        result = await send_telegram_message_with_retry(bot_token, message)
        if result.ok:
            await logger.ainfo("Telegram message sent successfully", chat_id=message.chat_id)
            return {"status": "success", "message": "Message sent"}
        else:
            await logger.awarning("Telegram API returned an error", error_code=result.error_code, description=result.description)
            raise HTTPException(status_code=400, detail=result.description)
    except Exception as e:
        await logger.aerror("Failed to send Telegram notification", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to send notification")