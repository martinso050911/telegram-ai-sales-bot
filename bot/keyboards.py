import os
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_site_url() -> str:
    """Returns external public website URL from RENDER_EXTERNAL_URL or fallback to local address."""
    return os.getenv("RENDER_EXTERNAL_URL", "http://127.0.0.1:8000").rstrip("/")

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Returns main menu reply keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💼 Получить B2B консультацию"),
                KeyboardButton(text="🎯 Подобрать тариф"),
            ],
            [
                KeyboardButton(text="🌐 Оформить заявку на сайте"),
                KeyboardButton(text="📞 Позвонить менеджеру"),
            ],
            [
                KeyboardButton(text="🔄 Сбросить диалог"),
                KeyboardButton(text="ℹ️ Помощь"),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
    )

def get_consultation_quick_actions(site_url: str = None) -> InlineKeyboardMarkup:
    """Returns inline keyboard for sales actions with dynamic website URL."""
    url = site_url or get_site_url()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌐 Оформить заявку на сайте", url=url),
                InlineKeyboardButton(text="📞 Позвонить менеджеру", callback_data="action_contact"),
            ],
            [
                InlineKeyboardButton(text="🔄 Начать новый диалог", callback_data="action_reset"),
            ],
        ]
    )
