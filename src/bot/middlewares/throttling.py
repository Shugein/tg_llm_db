import time
from typing import Callable, Dict, Any, Awaitable
from collections import defaultdict
from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger

from ..config import settings


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов (rate limiting)"""
    
    def __init__(self):
        super().__init__()
        self.rate_limit = settings.rate_limit_messages
        self.time_window = settings.rate_limit_window
        # Хранилище для отслеживания запросов пользователей
        self.user_requests: Dict[int, list] = defaultdict(list)
        self.user_warnings: Dict[int, float] = {}
    
    def _cleanup_old_requests(self, user_id: int, current_time: float) -> None:
        """Удаляет старые запросы из окна времени"""
        cutoff_time = current_time - self.time_window
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id] 
            if req_time > cutoff_time
        ]
    
    def _is_rate_limited(self, user_id: int, current_time: float) -> bool:
        """Проверяет, превышен ли лимит запросов"""
        self._cleanup_old_requests(user_id, current_time)
        return len(self.user_requests[user_id]) >= self.rate_limit
    
    def _should_send_warning(self, user_id: int, current_time: float) -> bool:
        """Определяет, нужно ли отправить предупреждение пользователю"""
        last_warning = self.user_warnings.get(user_id, 0)
        # Отправляем предупреждение не чаще чем раз в минуту
        return current_time - last_warning > 60
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """Проверяет лимит запросов для пользователя"""
        
        user_id = event.from_user.id
        current_time = time.time()
        
        # Проверяем лимит
        if self._is_rate_limited(user_id, current_time):
            logger.warning(
                f"Rate limit exceeded for user {user_id}. "
                f"Requests in window: {len(self.user_requests[user_id])}/{self.rate_limit}"
            )
            
            # Отправляем предупреждение пользователю
            if self._should_send_warning(user_id, current_time):
                self.user_warnings[user_id] = current_time
                remaining_time = int(self.time_window - (current_time - self.user_requests[user_id][0]))
                
                await event.answer(
                    f"⚠️ Вы превысили лимит сообщений!\n"
                    f"Максимум: {self.rate_limit} сообщений за {self.time_window} секунд.\n"
                    f"Попробуйте снова через {remaining_time} секунд."
                )
            
            return
        
        # Добавляем текущий запрос в историю
        self.user_requests[user_id].append(current_time)
        
        # Логируем статистику использования
        requests_count = len(self.user_requests[user_id])
        logger.debug(
            f"User {user_id} requests: {requests_count}/{self.rate_limit} "
            f"in {self.time_window}s window"
        )
        
        return await handler(event, data)