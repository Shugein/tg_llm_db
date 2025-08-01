from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger

from ..config import settings


class AuthMiddleware(BaseMiddleware):
    """Middleware для авторизации пользователей"""
    
    def __init__(self):
        super().__init__()
        self.allowed_users = settings.allowed_user_ids
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """Проверяет авторизацию пользователя"""
        
        user_id = event.from_user.id
        
        # Если список разрешенных пользователей пуст, разрешаем всем
        if not self.allowed_users:
            logger.warning("No allowed users configured - allowing all users")
            return await handler(event, data)
        
        # Проверяем, есть ли пользователь в списке разрешенных
        if user_id not in self.allowed_users:
            logger.warning(f"Unauthorized access attempt from user {user_id}")
            await event.answer(
                "❌ У вас нет доступа к этому боту.\n"
                "Обратитесь к администратору для получения разрешения."
            )
            return
        
        logger.debug(f"User {user_id} authorized")
        return await handler(event, data)