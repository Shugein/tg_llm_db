from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
    )
    builder.row(
        InlineKeyboardButton(text="🆘 Помощь", callback_data="help"),
        InlineKeyboardButton(text="🧹 Очистить контекст", callback_data="clear_context")
    )
    
    return builder.as_markup()

def get_settings_menu() -> InlineKeyboardMarkup:
    """Меню настроек"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🤖 Выбрать модель", callback_data="select_model")
    )
    builder.row(
        InlineKeyboardButton(text="🎯 Режим общения", callback_data="chat_mode")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()

def get_model_selection_menu() -> InlineKeyboardMarkup:
    """Меню выбора модели"""
    builder = InlineKeyboardBuilder()
    
    # Популярные модели
    models = [
        ("GPT-4o", "openai/gpt-4o"),
        ("GPT-4o Mini", "openai/gpt-4o-mini"),
        ("Claude 3.5 Sonnet", "anthropic/claude-3.5-sonnet"),
        ("Gemini Pro", "google/gemini-pro"),
        ("Llama 3.1 70B", "meta-llama/llama-3.1-70b-instruct")
    ]
    
    for name, model_id in models:
        builder.row(
            InlineKeyboardButton(
                text=name, 
                callback_data=f"model:{model_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="settings")
    )
    
    return builder.as_markup()

def get_chat_mode_menu() -> InlineKeyboardMarkup:
    """Меню режимов общения"""
    builder = InlineKeyboardBuilder()
    
    modes = [
        ("🤖 OpenRouter LLM", "chat_mode:openrouter"),
        ("📚 RAG система", "chat_mode:rag"),
        ("🧠 Гибридный", "chat_mode:hybrid")
    ]
    
    for name, callback in modes:
        builder.row(
            InlineKeyboardButton(text=name, callback_data=callback)
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="settings")
    )
    
    return builder.as_markup()

def get_generation_mode_menu() -> InlineKeyboardMarkup:
    """Меню режимов генерации для OpenRouter"""
    builder = InlineKeyboardBuilder()
    
    modes = [
        ("💬 Обычный", "gen_mode:normal"),
        ("🎨 Креативный", "gen_mode:creative"),
        ("🔬 Технический", "gen_mode:technical"),
        ("📝 Помощник", "gen_mode:assistant")
    ]
    
    for name, callback in modes:
        builder.row(
            InlineKeyboardButton(text=name, callback_data=callback)
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="settings")
    )
    
    return builder.as_markup()

def get_confirm_clear_menu() -> InlineKeyboardMarkup:
    """Меню подтверждения очистки контекста"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Да, очистить", callback_data="confirm_clear"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")
    )
    
    return builder.as_markup()