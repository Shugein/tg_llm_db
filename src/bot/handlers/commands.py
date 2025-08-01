from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from loguru import logger

from ..services import llm as llm_module
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

@router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Обработчик команды /settings"""
    settings_text = """
⚙️ <b>Настройки бота</b>

Здесь вы можете настроить работу бота под свои нужды:

• 🤖 <b>Выбрать модель</b> - выбор AI модели для генерации ответов
• 🎯 <b>Режим генерации</b> - настройка стиля ответов

<i>Выберите нужную опцию:</i>
"""
    
    await message.answer(
        settings_text,
        reply_markup=get_settings_menu()
    )

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Обработчик команды /stats"""
    user_id = message.from_user.id
    
    stats_text = f"""
📊 <b>Статистика использования</b>

<b>Текущая сессия:</b>
• Пользователь: {message.from_user.full_name}
• ID: {user_id}

<b>Общая статистика:</b>
• Всего запросов: Недоступно
• Использованных токенов: Недоступно
• Любимая модель: Недоступно

<i>Подробная статистика будет добавлена в следующих версиях.</i>
"""
    
    await message.answer(stats_text)

@router.message(Command("clear"))
async def cmd_clear(message: Message):
    """Обработчик команды /clear"""
    from ..handlers import callbacks as callbacks_module
    
    user_id = message.from_user.id
    
    # Очищаем контекст если менеджер инициализирован
    if callbacks_module.conversation_manager:
        try:
            await callbacks_module.conversation_manager.clear_context(user_id)
            logger.info(f"Context cleared for user {user_id}")
            await message.answer(
                "✅ <b>Контекст диалога очищен!</b>\n\n"
                "Теперь можете начать новый диалог. "
                "Бот забыл всю предыдущую историю разговора."
            )
        except Exception as e:
            logger.error(f"Failed to clear context for user {user_id}: {e}")
            await message.answer("❌ Ошибка при очистке контекста.")
    else:
        await message.answer("❌ Сервис контекста недоступен.")