import asyncio
from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from ..services.llm import llm_service

router = Router(name="messages")

@router.message(F.text & ~F.text.startswith('/'))
async def handle_text_message(message: Message):
    """Обработчик текстовых сообщений"""
    user_id = message.from_user.id
    user_text = message.text
    
    logger.info(f"Processing message from user {user_id}: {user_text[:50]}...")
    
    # Отправляем typing action
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Получаем ответ от LLM
        ai_response = await llm_service.process_message(user_id, user_text)
        
        # Отправляем ответ (разбивая если необходимо)
        if len(ai_response) <= 4096:
            await message.answer(ai_response)
        else:
            # Разбиваем длинное сообщение
            parts = [ai_response[i:i+4000] for i in range(0, len(ai_response), 4000)]
            for i, part in enumerate(parts):
                await message.answer(part)
                if i < len(parts) - 1:
                    await asyncio.sleep(0.5)
            
    except Exception as e:
        logger.error(f"Error processing message from user {user_id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке вашего сообщения. "
            "Попробуйте еще раз или обратитесь к администратору."
        )