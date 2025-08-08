from typing import List, Dict, Optional
from loguru import logger
from sqlalchemy import select, insert

from .openrouter import openrouter_generate_async, OpenRouterError
from .context import ConversationManager
from .external_apis import external_api_service, ExternalAPIError, ServiceType
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
    
    async def _generate_rag_response(
        self,
        user_id: int,
        user_message: str,
        messages: List[Dict[str, str]],
        use_context: bool = True
    ) -> str:
        """Генерирует ответ используя RAG систему"""
        try:
            # Подготавливаем контекст для RAG системы
            context = {}
            if use_context and messages:
                # Берем последние несколько сообщений как контекст
                recent_messages = messages[-3:] if len(messages) > 3 else messages
                context["conversation_history"] = recent_messages
            
            # Обращаемся к RAG системе
            rag_response = await external_api_service.call_rag_service(
                query=user_message,
                context=context,
                user_id=user_id
            )
            
            if rag_response["success"]:
                response_text = rag_response["response"]
                
                # Добавляем информацию об источниках если есть
                if rag_response.get("sources"):
                    sources = rag_response["sources"]
                    response_text += f"\n\n📚 <i>Основано на {len(sources)} источниках</i>"
                
                return response_text
            else:
                return "Извините, RAG система временно недоступна. Попробуйте позже."
                
        except ExternalAPIError as e:
            logger.error(f"RAG system error for user {user_id}: {e}")
            return "Извините, произошла ошибка при обращении к базе знаний. Попробуйте позже."
        
        except Exception as e:
            logger.error(f"Unexpected error in RAG response generation: {e}")
            return "Произошла внутренняя ошибка в RAG системе."
    
    async def _generate_hybrid_response(
        self,
        user_id: int,
        user_message: str,
        messages: List[Dict[str, str]],
        use_context: bool = True,
        model: Optional[str] = None
    ) -> str:
        """Генерирует ответ используя гибридный подход (RAG + LLM)"""
        try:
            # Сначала получаем информацию из RAG системы
            rag_context = {}
            if use_context and messages:
                recent_messages = messages[-3:] if len(messages) > 3 else messages
                rag_context["conversation_history"] = recent_messages
            
            rag_info = None
            try:
                rag_response = await external_api_service.call_rag_service(
                    query=user_message,
                    context=rag_context,
                    user_id=user_id
                )
                
                if rag_response["success"]:
                    rag_info = {
                        "content": rag_response["response"],
                        "sources": rag_response.get("sources", []),
                        "confidence": rag_response.get("confidence", 0.0)
                    }
                    
            except ExternalAPIError:
                logger.warning("RAG system not available for hybrid mode, using LLM only")
            
            # Формируем промпт для LLM с учетом RAG данных
            enhanced_messages = messages.copy()
            
            if rag_info and rag_info["confidence"] > 0.3:  # Используем RAG только если уверенность > 30%
                rag_context_prompt = f"""
Используй следующую информацию из базы знаний для ответа:

{rag_info["content"]}

Источники: {len(rag_info["sources"])} документов

Объедини эту информацию с твоими знаниями для формирования полного ответа на вопрос пользователя.
"""
                enhanced_messages.append({"role": "system", "content": rag_context_prompt})
            
            # Добавляем контекст диалога если нужно
            if use_context:
                context_messages = await self.conversation_manager.get_context_for_llm(user_id)
                enhanced_messages.extend(context_messages)
            else:
                enhanced_messages.append({"role": "user", "content": user_message})
            
            # Генерируем ответ через OpenRouter
            response = await openrouter_generate_async(
                prompt="",
                messages=enhanced_messages,
                model=model or settings.default_model,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            bot_response = response["content"]
            
            # Добавляем информацию об источниках если использовался RAG
            if rag_info and rag_info["sources"]:
                bot_response += f"\n\n🧠 <i>Ответ основан на базе знаний и AI модели</i>"
            
            return bot_response
            
        except OpenRouterError as e:
            logger.error(f"OpenRouter error in hybrid mode for user {user_id}: {e}")
            # Fallback на чистый RAG если LLM недоступен
            return await self._generate_rag_response(user_id, user_message, messages, use_context)
        
        except Exception as e:
            logger.error(f"Unexpected error in hybrid response generation: {e}")
            return "Произошла внутренняя ошибка в гибридном режиме."
    
    async def generate_response(
        self,
        user_id: int,
        user_message: str,
        telegram_user=None,
        model: Optional[str] = None,
        use_context: bool = True,
        system_prompt: Optional[str] = None,
        chat_mode: str = "openrouter"
    ) -> Dict[str, any]:
        """
        Генерирует ответ с учетом выбранного режима общения
        
        :param user_id: ID пользователя
        :param user_message: сообщение пользователя
        :param telegram_user: объект пользователя Telegram
        :param model: модель для использования
        :param use_context: использовать контекст диалога
        :param system_prompt: системный промпт
        :param chat_mode: режим общения (openrouter/rag/hybrid)
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
            
            # Выбираем метод генерации ответа в зависимости от режима
            if chat_mode == "rag":
                bot_response = await self._generate_rag_response(
                    user_id=user_id,
                    user_message=user_message,
                    messages=messages,
                    use_context=use_context
                )
                model_used = "rag_system"
                
            elif chat_mode == "hybrid":
                bot_response = await self._generate_hybrid_response(
                    user_id=user_id,
                    user_message=user_message,
                    messages=messages,
                    use_context=use_context,
                    model=model
                )
                model_used = f"hybrid_{model or settings.default_model}"
                
            else:  # openrouter mode
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
                model_used = response.get("model", "unknown")
            
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
                model_used=model_used,
                tokens_used=response.get("usage", {}).get("total_tokens", 0) if chat_mode == "openrouter" else 0
            )
            
            return {
                "response": bot_response,
                "model": model_used,
                "usage": response.get("usage", {}) if chat_mode == "openrouter" else {},
                "success": True,
                "chat_mode": chat_mode
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