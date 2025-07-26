import asyncio
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from .config import settings
from .handlers import setup_routers
from .middlewares import setup_middlewares
from .services.context import ConversationManager
from .database.database import init_database

async def create_bot() -> Bot:
    """Создание экземпляра бота"""
    return Bot(
        token=settings.telegram_bot_token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True
        )
    )

async def create_dispatcher() -> Dispatcher:
    """Создание диспетчера"""
    # Подключение к Redis для FSM
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)
    
    # Настройка middleware
    setup_middlewares(dp)
    
    # Подключение роутеров
    dp.include_routers(*setup_routers())
    
    return dp

async def main():
    """Главная функция запуска бота"""
    # Настройка логирования
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level
    )
    
    try:
        # Инициализация базы данных
        await init_database()
        
        # Инициализация менеджера контекста
        conversation_manager = ConversationManager()
        await conversation_manager.initialize()
        
        # Создание бота и диспетчера
        bot = await create_bot()
        dp = await create_dispatcher()
        
        logger.info("Starting polling mode...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())