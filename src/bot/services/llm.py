from typing import List, Dict, Optional
from loguru import logger
from sqlalchemy import select, insert

from .openrouter import openrouter_generate_async, OpenRouterError
from .context import ConversationManager
from ..config import settings
from ..database.database import User, Dialog, get_session

class LLMService:
    """Сервис для работы с LLM через OpenRouter"""
    
    def __init__(self, conversation_manager: ConversationManager):
        self.conversation_manager = conversation_manager
    
    async def _ensure_user_exists(self, user_id: int, telegram_user) -> int:
        """Убеждается что пользователь существует в БД, возвращает внутренний ID"""
        try:
            async for session in get_session():
                # Проверяем существует ли пользователь
                result = await session.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user is None:
                    # Создаем нового пользователя
                    new_user = User(
                        telegram_id=user_id,
                        username=getattr(telegram_user, 'username', None),
                        first_name=getattr(telegram_user, 'first_name', None),
                        last_name=getattr(telegram_user, 'last_name', None)
                    )
                    session.add(new_user)
                    await session.flush()
                    logger.info(f"Created new user: {user_id}")
                    return new_user.id
                else:
                    return user.id
                    
        except Exception as e:
            logger.error(f"Error ensuring user exists: {e}")
            return None
    
    async def _save_dialog(self, internal_user_id: int, telegram_id: int, 
                          user_message: str, bot_response: str, 
                          model_used: str, tokens_used: int):
        """Сохраняет диалог в базу данных"""
        try:
            async for session in get_session():
                dialog = Dialog(
                    user_id=internal_user_id,
                    telegram_id=telegram_id,
                    user_message=user_message,
                    bot_response=bot_response,
                    model_used=model_used,
                    tokens_used=tokens_used
                )
                session.add(dialog)
                logger.debug(f"Saved dialog for user {telegram_id}")
                
        except Exception as e:
            logger.error(f"Error saving dialog: {e}")
    
    async def generate_response(
        self,
        user_id: int,
        user_message: str,
        telegram_user=None,
        model: Optional[str] = None,
        use_context: bool = True,
        system_prompt: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Генерирует ответ от LLM с учетом контекста
        
        :param user_id: ID пользователя
        :param user_message: сообщение пользователя
        :param model: модель для использования
        :param use_context: использовать контекст диалога
        :param system_prompt: системный промпт
        :return: словарь с ответом и метаданными
        """
        try:
            # Убеждаемся что пользователь существует в БД
            internal_user_id = None
            if telegram_user:
                internal_user_id = await self._ensure_user_exists(user_id, telegram_user)
            
            # Добавляем сообщение пользователя в контекст
            await self.conversation_manager.add_message(
                user_id=user_id,
                role="user",
                content=user_message
            )
            
            # Получаем контекст для LLM
            messages = []
            
            # Добавляем системный промпт если указан
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Добавляем контекст диалога если нужно
            if use_context:
                context_messages = await self.conversation_manager.get_context_for_llm(user_id)
                messages.extend(context_messages)
            else:
                # Если контекст не нужен, добавляем только текущее сообщение
                messages.append({"role": "user", "content": user_message})
            
            # Генерируем ответ
            response = await openrouter_generate_async(
                prompt="",  # Не используется когда передаем messages
                messages=messages,
                model=model or settings.default_model,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            bot_response = response["content"]
            
            # Добавляем ответ бота в контекст
            await self.conversation_manager.add_message(
                user_id=user_id,
                role="assistant",
                content=bot_response
            )
            
            logger.info(f"Generated response for user {user_id} using model {response.get('model', 'unknown')}")
            
            # Сохраняем диалог в базу данных
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            await self._save_dialog(
                internal_user_id=internal_user_id,  # Может быть None
                telegram_id=user_id,
                user_message=user_message,
                bot_response=bot_response,
                model_used=response.get("model", "unknown"),
                tokens_used=tokens_used
            )
            
            return {
                "response": bot_response,
                "model": response.get("model"),
                "usage": response.get("usage", {}),
                "success": True
            }
            
        except OpenRouterError as e:
            logger.error(f"OpenRouter error for user {user_id}: {e}")
            return {
                "response": "Извините, произошла ошибка при обращении к AI. Попробуйте позже.",
                "error": str(e),
                "success": False
            }
        
        except Exception as e:
            logger.error(f"Unexpected error in generate_response for user {user_id}: {e}")
            return {
                "response": "Произошла внутренняя ошибка. Попробуйте позже.",
                "error": str(e),
                "success": False
            }

# Глобальный экземпляр сервиса (будет инициализирован в main.py)
llm_service: Optional[LLMService] = None