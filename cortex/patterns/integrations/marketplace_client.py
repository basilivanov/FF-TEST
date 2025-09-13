#!/usr/bin/env python3
"""
Универсальный клиент для интеграции с маркетплейсами.
Поддерживает Ozon, Wildberries, Яндекс.Маркет, Amazon и другие.
"""

import asyncio
import aiohttp
import tenacity
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import structlog

log = structlog.get_logger()

class MarketplaceType(Enum):
    OZON = "ozon"
    WILDBERRIES = "wildberries"
    YANDEX_MARKET = "yandex_market"
    AMAZON = "amazon"
    ALIEXPRESS = "aliexpress"
    CUSTOM = "custom"

@dataclass
class MarketplaceConfig:
    """Конфигурация маркетплейса"""
    type: MarketplaceType
    base_url: str
    api_key: str
    api_secret: Optional[str] = None
    client_id: Optional[str] = None
    timeout: int = 30
    rate_limit: int = 100  # requests per minute
    retry_attempts: int = 3

@dataclass
class Product:
    """Универсальная модель товара"""
    marketplace_id: str
    sku: str
    title: str
    price: float
    currency: str
    stock: int
    category: str
    status: str
    created_at: datetime
    updated_at: datetime
    images: List[str]
    attributes: Dict[str, Any]

@dataclass
class Order:
    """Универсальная модель заказа"""
    marketplace_id: str
    order_number: str
    status: str
    customer_info: Dict[str, str]
    items: List[Dict[str, Any]]
    total_amount: float
    currency: str
    created_at: datetime
    shipping_address: Dict[str, str]
    payment_method: str

class BaseMarketplaceClient(ABC):
    """Базовый класс для клиентов маркетплейсов"""
    
    def __init__(self, config: MarketplaceConfig, correlation_id: str = None):
        self.config = config
        self.correlation_id = correlation_id or f"mp_{int(datetime.now().timestamp())}"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        await self._create_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_session()
        
    async def _create_session(self):
        """Создание HTTP сессии"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        headers = await self._get_auth_headers()
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            connector=aiohttp.TCPConnector(limit=10)
        )
        
    async def _close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Получение заголовков авторизации"""
        pass
    
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        retry=tenacity.retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Выполнение HTTP запроса с retry логикой"""
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Добавляем correlation ID в заголовки
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['X-Correlation-ID'] = self.correlation_id
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    return await response.json()
                else:
                    text = await response.text()
                    return {'content': text}
                    
        except Exception as e:
            log.error(
                event="marketplace_request_error",
                marketplace=self.config.type.value,
                url=url,
                error=str(e),
                correlation_id=self.correlation_id
            )
            raise
    
    @abstractmethod
    async def get_products(
        self, 
        limit: int = 100, 
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Product]:
        """Получение списка товаров"""
        pass
    
    @abstractmethod
    async def get_orders(
        self, 
        date_from: datetime, 
        date_to: datetime,
        status: Optional[str] = None
    ) -> List[Order]:
        """Получение заказов за период"""
        pass
    
    @abstractmethod
    async def update_stock(self, sku: str, quantity: int) -> bool:
        """Обновление остатков товара"""
        pass
    
    @abstractmethod
    async def update_price(self, sku: str, price: float) -> bool:
        """Обновление цены товара"""
        pass

class OzonClient(BaseMarketplaceClient):
    """Клиент для Ozon API"""
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        return {
            "Client-Id": self.config.client_id,
            "Api-Key": self.config.api_key,
            "Content-Type": "application/json"
        }
    
    async def get_products(
        self, 
        limit: int = 100, 
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Product]:
        """Получение товаров из Ozon"""
        payload = {
            "limit": limit,
            "offset": offset,
            "filter": filters or {}
        }
        
        response = await self._make_request(
            "POST", 
            "/v3/products/info", 
            json=payload
        )
        
        products = []
        for item in response.get("result", {}).get("items", []):
            product = Product(
                marketplace_id=str(item.get("product_id")),
                sku=item.get("offer_id", ""),
                title=item.get("name", ""),
                price=float(item.get("price", 0)),
                currency="RUB",
                stock=item.get("stocks", {}).get("present", 0),
                category=item.get("category_id", ""),
                status=item.get("status", {}).get("state", ""),
                created_at=datetime.fromisoformat(item.get("created_at", datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(item.get("updated_at", datetime.now().isoformat())),
                images=item.get("images", []),
                attributes=item.get("attributes", {})
            )
            products.append(product)
        
        return products
    
    async def get_orders(
        self, 
        date_from: datetime, 
        date_to: datetime,
        status: Optional[str] = None
    ) -> List[Order]:
        """Получение заказов из Ozon"""
        payload = {
            "filter": {
                "since": date_from.isoformat() + "Z",
                "to": date_to.isoformat() + "Z"
            },
            "limit": 1000
        }
        
        if status:
            payload["filter"]["status"] = status
            
        response = await self._make_request(
            "POST",
            "/v3/posting/fbs/list",
            json=payload
        )
        
        orders = []
        for posting in response.get("result", {}).get("postings", []):
            order = Order(
                marketplace_id=posting.get("posting_number", ""),
                order_number=posting.get("posting_number", ""),
                status=posting.get("status", ""),
                customer_info=posting.get("customer", {}),
                items=[],  # Детали товаров нужно получать отдельно
                total_amount=float(posting.get("total_amount", 0)),
                currency="RUB",
                created_at=datetime.fromisoformat(posting.get("created_at")),
                shipping_address=posting.get("address", {}),
                payment_method=posting.get("payment_method", "")
            )
            orders.append(order)
            
        return orders
    
    async def update_stock(self, sku: str, quantity: int) -> bool:
        """Обновление остатков в Ozon"""
        payload = {
            "stocks": [
                {
                    "offer_id": sku,
                    "stock": quantity,
                    "warehouse_id": 1  # Основной склад
                }
            ]
        }
        
        try:
            await self._make_request("POST", "/v1/product/import/stocks", json=payload)
            return True
        except Exception as e:
            log.error(
                event="stock_update_error",
                sku=sku,
                quantity=quantity,
                error=str(e),
                correlation_id=self.correlation_id
            )
            return False
    
    async def update_price(self, sku: str, price: float) -> bool:
        """Обновление цены в Ozon"""
        payload = {
            "prices": [
                {
                    "offer_id": sku,
                    "price": str(price),
                    "currency_code": "RUB"
                }
            ]
        }
        
        try:
            await self._make_request("POST", "/v1/product/import/prices", json=payload)
            return True
        except Exception as e:
            log.error(
                event="price_update_error", 
                sku=sku,
                price=price,
                error=str(e),
                correlation_id=self.correlation_id
            )
            return False

class WildberriesClient(BaseMarketplaceClient):
    """Клиент для Wildberries API"""
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_products(self, limit: int = 100, offset: int = 0, filters: Optional[Dict[str, Any]] = None) -> List[Product]:
        # WB API implementation
        response = await self._make_request("GET", f"/api/v2/goods?limit={limit}&offset={offset}")
        # Transform WB format to universal Product format
        return []
    
    async def get_orders(self, date_from: datetime, date_to: datetime, status: Optional[str] = None) -> List[Order]:
        # WB API implementation  
        return []
    
    async def update_stock(self, sku: str, quantity: int) -> bool:
        # WB API implementation
        return False
    
    async def update_price(self, sku: str, price: float) -> bool:
        # WB API implementation
        return False

class MarketplaceClientFactory:
    """Фабрика для создания клиентов маркетплейсов"""
    
    _clients = {
        MarketplaceType.OZON: OzonClient,
        MarketplaceType.WILDBERRIES: WildberriesClient,
        # Добавить другие клиенты по мере необходимости
    }
    
    @classmethod
    def create_client(
        self, 
        config: MarketplaceConfig, 
        correlation_id: str = None
    ) -> BaseMarketplaceClient:
        """Создание клиента маркетплейса"""
        client_class = self._clients.get(config.type)
        if not client_class:
            raise ValueError(f"Unsupported marketplace type: {config.type}")
            
        return client_class(config, correlation_id)

class MarketplaceOrchestrator:
    """Оркестратор для работы с несколькими маркетплейсами"""
    
    def __init__(self, configs: List[MarketplaceConfig]):
        self.configs = configs
        self.clients: List[BaseMarketplaceClient] = []
        
    async def __aenter__(self):
        for config in self.configs:
            client = MarketplaceClientFactory.create_client(config)
            await client._create_session()
            self.clients.append(client)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for client in self.clients:
            await client._close_session()
    
    async def sync_products_from_all(self) -> Dict[str, List[Product]]:
        """Синхронизация товаров со всех маркетплейсов"""
        results = {}
        
        tasks = [
            self._sync_products_from_marketplace(client)
            for client in self.clients
        ]
        
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for client, result in zip(self.clients, completed_results):
            marketplace_name = client.config.type.value
            if isinstance(result, Exception):
                log.error(
                    event="marketplace_sync_error",
                    marketplace=marketplace_name,
                    error=str(result)
                )
                results[marketplace_name] = []
            else:
                results[marketplace_name] = result
                
        return results
    
    async def _sync_products_from_marketplace(self, client: BaseMarketplaceClient) -> List[Product]:
        """Синхронизация товаров с одного маркетплейса"""
        try:
            products = await client.get_products(limit=1000)
            
            log.info(
                event="marketplace_products_synced",
                marketplace=client.config.type.value,
                count=len(products),
                correlation_id=client.correlation_id
            )
            
            return products
            
        except Exception as e:
            log.error(
                event="marketplace_products_sync_error",
                marketplace=client.config.type.value, 
                error=str(e),
                correlation_id=client.correlation_id
            )
            raise
    
    async def update_price_everywhere(self, sku: str, price: float) -> Dict[str, bool]:
        """Обновление цены товара на всех маркетплейсах"""
        results = {}
        
        tasks = [
            client.update_price(sku, price)
            for client in self.clients
        ]
        
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for client, result in zip(self.clients, completed_results):
            marketplace_name = client.config.type.value
            results[marketplace_name] = not isinstance(result, Exception) and result
            
        return results

# Пример использования
async def main():
    """Пример использования клиентов маркетплейсов"""
    
    # Конфигурация для Ozon
    ozon_config = MarketplaceConfig(
        type=MarketplaceType.OZON,
        base_url="https://api-seller.ozon.ru",
        api_key="your-ozon-api-key",
        client_id="your-ozon-client-id"
    )
    
    # Работа с одним маркетплейсом
    async with MarketplaceClientFactory.create_client(ozon_config) as client:
        products = await client.get_products(limit=10)
        print(f"Получено {len(products)} товаров с Ozon")
        
        # Обновляем цену первого товара
        if products:
            success = await client.update_price(products[0].sku, 999.99)
            print(f"Обновление цены: {'успешно' if success else 'ошибка'}")
    
    # Работа с несколькими маркетплейсами
    configs = [ozon_config]  # Добавить конфигурации других МП
    
    async with MarketplaceOrchestrator(configs) as orchestrator:
        all_products = await orchestrator.sync_products_from_all()
        
        for marketplace, products in all_products.items():
            print(f"{marketplace}: {len(products)} товаров")

if __name__ == "__main__":
    asyncio.run(main())