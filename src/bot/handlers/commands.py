from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from loguru import logger

from ..services.llm import llm_service
from ..keyboards.inline import get_main_menu, get_settings_menu

router = Router(name="commands")

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    logger.info(f"User {user.id} (@{user.username}) started the bot")
    
    welcome_text = f"""
🤖 <b>Добро пожаловать в AI Bot!</b>

Привет, {user.first_name}! Я современный Telegram бот с интеграцией различных LLM моделей через OpenRouter API.

<b>Что я умею:</b>
• 💬 Отвечать на вопросы используя GPT-4, Claude, Gemini и другие модели
• 🧠 Запоминать контекст наших диалогов
• ⚙️ Работать в разных режимах (обычный, креативный, технический)
• 📊 Предоставлять статистику использования

<b>Начните просто написав мне сообщение!</b>
"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
🆘 <b>Справка по командам:</b>

<b>Основные команды:</b>
/start - Начать работу с ботом
/help - Показать эту справку
/settings - Настройки бота
/stats - Статистика использования
/clear - Очистить контекст диалога

<b>Дополнительно:</b>
• Просто напишите сообщение для общения с AI
• Используйте inline кнопки для быстрого доступа к функциям
• Бот запоминает контекст в рамках сессии (24 часа)
"""
    
    await message.answer(help_text)