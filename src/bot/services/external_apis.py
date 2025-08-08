import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from loguru import logger
from enum import Enum

from ..config import settings


class ServiceType(Enum):
    """Типы внешних сервисов"""
    RAG_SYSTEM = "rag_system"
    OPENROUTER = "openrouter"


class ExternalAPIError(Exception):
    """Исключение для ошибок внешних API"""
    pass


class ExternalAPIService:
    """Сервис для интеграции с внешними FastAPI проектами"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Получение или создание HTTP сессии"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=settings.external_services_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Закрытие HTTP сессии"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def call_rag_service(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Обращение к RAG системе
        
        :param query: запрос пользователя
        :param context: дополнительный контекст
        :param user_id: ID пользователя
        :return: ответ от RAG системы
        """
        if not settings.rag_service_url:
            raise ExternalAPIError("RAG service URL not configured")
        
        session = await self.get_session()
        
        # Подготавливаем данные для запроса
        request_data = {
            "query": query,
            "user_id": user_id
        }
        
        if context:
            request_data["context"] = context
        
        # Подготавливаем заголовки
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Telegram-LLM-Bot/1.0"
        }
        
        # Добавляем API ключ если настроен
        if settings.rag_service_api_key:
            headers["Authorization"] = f"Bearer {settings.rag_service_api_key.get_secret_value()}"
        
        try:
            logger.debug(f"Calling RAG service: {settings.rag_service_url}")
            
            async with session.post(
                f"{settings.rag_service_url}/query",
                json=request_data,
                headers=headers
            ) as response:
                
                response.raise_for_status()
                response_data = await response.json()
                
                logger.debug("RAG service request completed successfully")
                return {
                    "success": True,
                    "response": response_data.get("answer", ""),
                    "sources": response_data.get("sources", []),
                    "confidence": response_data.get("confidence", 0.0),
                    "service": ServiceType.RAG_SYSTEM.value
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"RAG service request failed: {e}")
            raise ExternalAPIError(f"RAG service request failed: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error in RAG service call: {e}")
            raise ExternalAPIError(f"Unexpected error: {e}")
    
    async def call_custom_service(
        self,
        service_url: str,
        endpoint: str,
        data: Dict[str, Any],
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Универсальный метод для обращения к кастомным FastAPI сервисам
        
        :param service_url: базовый URL сервиса
        :param endpoint: конечная точка API
        :param data: данные для отправки
        :param method: HTTP метод
        :param headers: дополнительные заголовки
        :param api_key: API ключ для авторизации
        :return: ответ от сервиса
        """
        session = await self.get_session()
        
        # Подготавливаем заголовки
        request_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Telegram-LLM-Bot/1.0"
        }
        
        if headers:
            request_headers.update(headers)
        
        if api_key:
            request_headers["Authorization"] = f"Bearer {api_key}"
        
        url = f"{service_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            logger.debug(f"Calling custom service: {url}")
            
            async with session.request(
                method,
                url,
                json=data,
                headers=request_headers
            ) as response:
                
                response.raise_for_status()
                response_data = await response.json()
                
                logger.debug("Custom service request completed successfully")
                return {
                    "success": True,
                    "data": response_data,
                    "status_code": response.status
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"Custom service request failed: {e}")
            raise ExternalAPIError(f"Custom service request failed: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error in custom service call: {e}")
            raise ExternalAPIError(f"Unexpected error: {e}")


# Глобальный экземпляр сервиса
external_api_service = ExternalAPIService()


async def cleanup_external_services():
    """Очистка ресурсов внешних сервисов"""
    await external_api_service.close()