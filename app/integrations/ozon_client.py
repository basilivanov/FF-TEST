#!/usr/bin/env python3
"""
Ozon API client for importing raw data.
"""

import httpx
import tenacity
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import structlog
from app.logging_helpers import log_http, log_job, log_db

# Настройка логгера
log = structlog.get_logger()

class OzonClient:
    """HTTP client for Ozon API with retry logic."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://api-seller.ozon.ru"):
        """
        Initialize Ozon client.
        
        Args:
            api_key (str): Ozon API key
            api_secret (str): Ozon API secret
            base_url (str): Base URL for Ozon API
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        
        # HTTP клиент с таймаутами и ретраями
        self.client = httpx.Client(
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0),
            headers={
                "Client-Id": self.api_key,
                "Api-Key": self.api_secret,
                "Content-Type": "application/json"
            }
        )
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.client.close()
    
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        reraise=True
    )
    @log_http
    def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            method (str): HTTP method
            endpoint (str): API endpoint
            **kwargs: Additional arguments for request
            
        Returns:
            httpx.Response: HTTP response
            
        Raises:
            httpx.HTTPStatusError: For HTTP errors
            httpx.RequestError: For request errors
        """
        url = f"{self.base_url}{endpoint}"
        
        # Добавляем correlation_id если есть
        correlation_id = kwargs.pop('correlation_id', None)
        if correlation_id:
            self.client.headers['X-Correlation-ID'] = correlation_id
        
        try:
            response = self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            log.error(
                event="http_error",
                component="integrations",
                agent_role="Dev",
                kv={
                    "method": method,
                    "url": url,
                    "status": e.response.status_code,
                    "error": str(e)
                }
            )
            raise
        except httpx.RequestError as e:
            log.error(
                event="request_error",
                component="integrations",
                agent_role="Dev",
                kv={
                    "method": method,
                    "url": url,
                    "error": str(e)
                }
            )
            raise
    
    @log_job("ozon_import_postings")
    def import_postings(self, date_from: datetime, date_to: datetime) -> List[Dict[str, Any]]:
        """
        Import postings from Ozon for specified date range.
        
        Args:
            date_from (datetime): Start date
            date_to (datetime): End date
            
        Returns:
            List[Dict[str, Any]]: List of postings
            
        Raises:
            Exception: If import fails
        """
        try:
            postings = []
            
            # Формируем запрос
            payload = {
                "filter": {
                    "since": date_from.isoformat() + "Z",
                    "to": date_to.isoformat() + "Z"
                },
                "page": 1,
                "page_size": 1000
            }
            
            while True:
                # Делаем запрос к API
                response = self._make_request(
                    "POST", 
                    "/v3/posting/fbs/list", 
                    json=payload
                )
                
                # Парсим ответ
                data = response.json()
                
                # Логируем извлечение страницы
                log.info(
                    event="extract_page",
                    component="integrations",
                    agent_role="Dev",
                    kv={
                        "source": "ozon",
                        "page": payload["page"],
                        "items": len(data.get("result", {}).get("postings", [])),
                        "total": data.get("result", {}).get("total", 0)
                    }
                )
                
                # Извлекаем постинги
                page_postings = data.get("result", {}).get("postings", [])
                
                # Добавляем постинги в список
                for posting in page_postings:
                    postings.append({
                        "source": "ozon",
                        "posting_id": posting.get("posting_number"),
                        "payload_json": json.dumps(posting, ensure_ascii=False),
                        "fetched_at": datetime.utcnow().isoformat() + "Z",
                        "period_from": date_from.date().isoformat(),
                        "period_to": date_to.date().isoformat()
                    })
                
                # Проверяем, есть ли еще страницы
                total = data.get("result", {}).get("total", 0)
                current_items = len(page_postings)
                if current_items == 0 or payload["page"] * payload["page_size"] >= total:
                    break
                    
                # Переходим к следующей странице
                payload["page"] += 1
                
            return postings
        except Exception as e:
            log.error(
                event="ozon_import_error",
                component="integrations",
                agent_role="Dev",
                kv={
                    "error": str(e),
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat()
                },
                stack=True
            )
            raise
    
    def close(self):
        """Close HTTP client."""
        self.client.close()

# Функции-обертки для удобства использования
def create_ozon_client(api_key: str, api_secret: str) -> OzonClient:
    """
    Create Ozon client.
    
    Args:
        api_key (str): Ozon API key
        api_secret (str): Ozon API secret
        
    Returns:
        OzonClient: Initialized Ozon client
    """
    return OzonClient(api_key, api_secret)

def import_ozon_postings(api_key: str, api_secret: str, date_from: datetime, date_to: datetime) -> List[Dict[str, Any]]:
    """
    Import Ozon postings for specified date range.
    
    Args:
        api_key (str): Ozon API key
        api_secret (str): Ozon API secret
        date_from (datetime): Start date
        date_to (datetime): End date
        
    Returns:
        List[Dict[str, Any]]: List of postings
    """
    with create_ozon_client(api_key, api_secret) as client:
        return client.import_postings(date_from, date_to)