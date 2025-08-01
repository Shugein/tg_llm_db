import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from loguru import logger
import redis.asyncio as redis

from ..config import settings

@dataclass
class Message:
    """Структура сообщения в контексте"""
    role: str  # "user" или "assistant"
    content: str
    timestamp: datetime
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )

class ConversationManager:
    """Менеджер контекста диалогов пользователей"""
    
    def __init__(self, max_context_messages: int = 20, context_ttl: int = 3600):
        self.redis_client: Optional[redis.Redis] = None
        self.max_context_messages = max_context_messages
        self.context_ttl = context_ttl  # время жизни контекста в секундах
    
    async def initialize(self):
        """Инициализация Redis соединения"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Проверяем соединение
            await self.redis_client.ping()
            logger.info("ConversationManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ConversationManager: {e}")
            raise
    
    def _get_context_key(self, user_id: int) -> str:
        """Генерирует ключ для хранения контекста пользователя"""
        return f"context:{user_id}"
    
    async def get_context(self, user_id: int) -> List[Message]:
        """Получает контекст диалога пользователя"""
        if not self.redis_client:
            raise RuntimeError("ConversationManager not initialized")
        
        try:
            key = self._get_context_key(user_id)
            context_data = await self.redis_client.get(key)
            
            if not context_data:
                return []
            
            messages_data = json.loads(context_data)
            messages = [Message.from_dict(msg) for msg in messages_data]
            
            # Фильтруем устаревшие сообщения
            cutoff_time = datetime.now() - timedelta(seconds=self.context_ttl)
            recent_messages = [msg for msg in messages if msg.timestamp > cutoff_time]
            
            logger.debug(f"Retrieved {len(recent_messages)} messages for user {user_id}")
            return recent_messages
            
        except Exception as e:
            logger.error(f"Error getting context for user {user_id}: {e}")
            return []
    
    async def add_message(self, user_id: int, role: str, content: str):
        """Добавляет сообщение в контекст пользователя"""
        if not self.redis_client:
            raise RuntimeError("ConversationManager not initialized")
        
        try:
            # Получаем текущий контекст
            messages = await self.get_context(user_id)
            
            # Добавляем новое сообщение
            new_message = Message(
                role=role,
                content=content,
                timestamp=datetime.now()
            )
            messages.append(new_message)
            
            # Ограничиваем количество сообщений
            if len(messages) > self.max_context_messages:
                # Удаляем старые сообщения, оставляя последние max_context_messages
                messages = messages[-self.max_context_messages:]
            
            # Сохраняем в Redis
            key = self._get_context_key(user_id)
            messages_data = [msg.to_dict() for msg in messages]
            
            await self.redis_client.setex(
                key,
                self.context_ttl,
                json.dumps(messages_data, ensure_ascii=False)
            )
            
            logger.debug(f"Added {role} message for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error adding message for user {user_id}: {e}")
            raise
    
    async def clear_context(self, user_id: int):
        """Очищает контекст пользователя"""
        if not self.redis_client:
            raise RuntimeError("ConversationManager not initialized")
        
        try:
            key = self._get_context_key(user_id)
            await self.redis_client.delete(key)
            logger.info(f"Cleared context for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error clearing context for user {user_id}: {e}")
            raise
    
    async def get_context_for_llm(self, user_id: int) -> List[Dict[str, str]]:
        """Получает контекст в формате для отправки в LLM"""
        messages = await self.get_context(user_id)
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    async def get_context_summary(self, user_id: int) -> Dict[str, any]:
        """Получает краткую информацию о контексте пользователя"""
        messages = await self.get_context(user_id)
        
        if not messages:
            return {
                "message_count": 0,
                "oldest_message": None,
                "newest_message": None
            }
        
        return {
            "message_count": len(messages),
            "oldest_message": messages[0].timestamp.isoformat(),
            "newest_message": messages[-1].timestamp.isoformat()
        }
    
    async def close(self):
        """Закрывает соединение с Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("ConversationManager connection closed")