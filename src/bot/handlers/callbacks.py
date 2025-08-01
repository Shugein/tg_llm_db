from aiogram import Router, F
from aiogram.types import CallbackQuery
from loguru import logger

from ..keyboards.inline import get_main_menu, get_settings_menu, get_model_selection_menu, get_confirm_clear_menu
from ..services.context import ConversationManager

router = Router(name="callbacks")

# Глобальная переменная для ConversationManager (будет инициализирована в main.py)
conversation_manager: ConversationManager = None

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Обработчик главного меню"""
    await callback.answer()
    
    welcome_text = f"""
🤖 <b>AI Bot - Главное меню</b>

Выберите действие:
• ⚙️ <b>Настройки</b> - изменить модель и режим работы  
• 📊 <b>Статистика</b> - просмотр статистики использования
• 🆘 <b>Помощь</b> - справка по командам
• 🧹 <b>Очистить контекст</b> - начать новый диалог

<i>Просто напишите сообщение для общения с AI!</i>
"""
    
    await callback.message.edit_text(
        welcome_text,
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "settings")
async def callback_settings(callback: CallbackQuery):
    """Обработчик настроек"""
    await callback.answer()
    
    settings_text = """
⚙️ <b>Настройки бота</b>

Здесь вы можете настроить работу бота под свои нужды:

• 🤖 <b>Выбрать модель</b> - выбор AI модели для генерации ответов
• 🎯 <b>Режим генерации</b> - настройка стиля ответов

<i>Выберите нужную опцию:</i>
"""
    
    await callback.message.edit_text(
        settings_text,
        reply_markup=get_settings_menu()
    )

@router.callback_query(F.data == "select_model")
async def callback_select_model(callback: CallbackQuery):
    """Обработчик выбора модели"""
    await callback.answer()
    
    model_text = """
🤖 <b>Выбор AI модели</b>

Доступные модели:

• <b>GPT-4o</b> - самая мощная модель OpenAI
• <b>GPT-4o Mini</b> - быстрая и эффективная модель 
• <b>Claude 3.5 Sonnet</b> - модель от Anthropic
• <b>Gemini Pro</b> - модель от Google
• <b>Llama 3.1 70B</b> - открытая модель от Meta

<i>Выберите модель для использования:</i>
"""
    
    await callback.message.edit_text(
        model_text,
        reply_markup=get_model_selection_menu()
    )

@router.callback_query(F.data.startswith("model:"))
async def callback_model_selected(callback: CallbackQuery):
    """Обработчик выбора конкретной модели"""
    model_id = callback.data.split(":", 1)[1]
    await callback.answer(f"Модель {model_id} выбрана!")
    
    # Здесь можно сохранить выбор модели в базе данных или Redis
    
    await callback.message.edit_text(
        f"✅ Выбрана модель: <code>{model_id}</code>\n\n"
        "Модель будет использована для следующих запросов.",
        reply_markup=get_settings_menu()
    )

@router.callback_query(F.data == "clear_context")
async def callback_clear_context(callback: CallbackQuery):
    """Обработчик очистки контекста"""
    await callback.answer()
    
    confirm_text = """
🧹 <b>Очистка контекста диалога</b>

Вы уверены, что хотите очистить историю диалога? 

После очистки бот забудет весь предыдущий контекст разговора и начнет новый диалог с чистого листа.

<i>Это действие нельзя отменить!</i>
"""
    
    await callback.message.edit_text(
        confirm_text,
        reply_markup=get_confirm_clear_menu()
    )

@router.callback_query(F.data == "confirm_clear")
async def callback_confirm_clear(callback: CallbackQuery):
    """Подтверждение очистки контекста"""
    await callback.answer("Контекст очищен!")
    
    user_id = callback.from_user.id
    
    # Очищаем контекст если менеджер инициализирован
    if conversation_manager:
        try:
            await conversation_manager.clear_context(user_id)
            logger.info(f"Context cleared for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to clear context for user {user_id}: {e}")
    
    await callback.message.edit_text(
        "✅ <b>Контекст диалога очищен!</b>\n\n"
        "Теперь можете начать новый диалог. "
        "Бот забыл всю предыдущую историю разговора.",
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "stats")
async def callback_stats(callback: CallbackQuery):
    """Обработчик статистики"""
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Получаем статистику контекста
    context_info = {"message_count": 0, "oldest_message": None, "newest_message": None}
    if conversation_manager:
        try:
            context_info = await conversation_manager.get_context_summary(user_id)
        except Exception as e:
            logger.error(f"Failed to get context summary for user {user_id}: {e}")
    
    stats_text = f"""
📊 <b>Статистика использования</b>

<b>Текущая сессия:</b>
• Сообщений в контексте: {context_info['message_count']}
• Начало диалога: {context_info['oldest_message'] or 'Нет данных'}
• Последняя активность: {context_info['newest_message'] or 'Нет данных'}

<b>Общая статистика:</b>
• Всего запросов: Недоступно
• Использованных токенов: Недоступно
• Любимая модель: Недоступно

<i>Подробная статистика будет добавлена в следующих версиях.</i>
"""
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Обработчик справки"""
    await callback.answer()
    
    help_text = """
🆘 <b>Справка по использованию бота</b>

<b>Основные возможности:</b>
• Отправьте любое текстовое сообщение для общения с AI
• Бот поддерживает контекст диалога
• Доступны различные AI модели на выбор

<b>Команды:</b>
• /start - перезапуск бота
• /help - показать справку
• /settings - открыть настройки
• /clear - очистить контекст диалога

<b>Советы:</b>
• Для лучших результатов формулируйте вопросы четко
• Используйте контекст для развития темы разговора
• Экспериментируйте с разными моделями

<b>Поддержка:</b>
Если у вас возникли проблемы, обратитесь к администратору.
"""
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_main_menu()
    )