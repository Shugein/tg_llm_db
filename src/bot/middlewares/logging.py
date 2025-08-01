import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from loguru import logger


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования входящих сообщений и запросов"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Логирует входящие события и время обработки"""
        
        start_time = time.time()
        
        # Получаем информацию о пользователе
        user = event.from_user
        user_info = f"{user.full_name} (@{user.username})" if user.username else user.full_name
        
        # Логируем в зависимости от типа события
        if isinstance(event, Message):
            content = event.text[:100] + "..." if event.text and len(event.text) > 100 else event.text
            logger.info(
                f"📨 Message from {user_info} (ID: {user.id}): {content}"
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                f"🔘 Callback from {user_info} (ID: {user.id}): {event.data}"
            )
        
        try:
            # Выполняем обработчик
            result = await handler(event, data)
            
            # Логируем время выполнения
            execution_time = time.time() - start_time
            logger.debug(
                f"✅ Request processed in {execution_time:.3f}s for user {user.id}"
            )
            
            return result
            
        except Exception as e:
            # Логируем ошибки
            execution_time = time.time() - start_time
            logger.error(
                f"❌ Error processing request from user {user.id} "
                f"after {execution_time:.3f}s: {str(e)}"
            )
            raise