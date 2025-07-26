from aiogram import Router, F
from aiogram.types import CallbackQuery
from loguru import logger

router = Router(name="callbacks")

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Обработчик главного меню"""
    await callback.answer()
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=None
    )

@router.callback_query(F.data == "settings")
async def callback_settings(callback: CallbackQuery):
    """Обработчик настроек"""
    await callback.answer()
    await callback.message.edit_text(
        "⚙️ Настройки бота",
        reply_markup=None
    )