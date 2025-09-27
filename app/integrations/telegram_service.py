"""Telegram notification service with template support."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending notifications via Telegram using templates."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """Initialize the Telegram service.
        
        Args:
            bot_token: Telegram bot token. If not provided, will be read from TELEGRAM_BOT_TOKEN env var.
            chat_id: Target chat ID. If not provided, will be read from TELEGRAM_CHAT_ID env var.
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token:
            raise ValueError("Telegram bot token is required")
            
        if not self.chat_id:
            raise ValueError("Telegram chat ID is required")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def send_message(self, text: str) -> Dict[str, Any]:
        """Send a message via Telegram.
        
        Args:
            text: Message text to send
            
        Returns:
            Response from Telegram API
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        if not text:
            raise ValueError("Message text cannot be empty")
            
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        timeout = httpx.Timeout(connect=3.0, read=10.0)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info("Successfully sent Telegram message", extra={
                    "message_id": result.get("result", {}).get("message_id")
                })
                return result
        except httpx.HTTPError as e:
            logger.error("Failed to send Telegram message", extra={
                "error": str(e),
                "status_code": e.response.status_code if e.response else None
            })
            raise

    async def send_template_message(self, template: str, **kwargs) -> Dict[str, Any]:
        """Send a message using a template.
        
        Args:
            template: Template string with placeholders
            **kwargs: Values to substitute in the template
            
        Returns:
            Response from Telegram API
        """
        try:
            formatted_text = template.format(**kwargs)
            return await self.send_message(formatted_text)
        except KeyError as e:
            logger.error("Missing template parameter", extra={"missing_key": str(e)})
            raise ValueError(f"Missing template parameter: {e}") from e
        except Exception as e:
            logger.error("Failed to format template message", extra={"error": str(e)})
            raise


# Example usage:
# service = TelegramService()
# await service.send_template_message(
#     "New feature *{feature_name}* has been deployed to *{environment}*",
#     feature_name="Auto-pipeline",
#     environment="production"
# )