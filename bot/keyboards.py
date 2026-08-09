from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Returns main menu reply keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💼 Получить B2B консультацию"),
                KeyboardButton(text="🎯 Подобрать тариф"),
            ],
            [
                KeyboardButton(text="🔄 Сбросить диалог"),
                KeyboardButton(text="ℹ️ Помощь"),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
    )

def get_consultation_quick_actions() -> InlineKeyboardMarkup:
    """Returns inline keyboard for sales actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌐 Оформить заявку на сайте", url="http://127.0.0.1:8000"),
                InlineKeyboardButton(text="📞 Позвонить менеджеру", callback_data="action_contact"),
            ],
            [
                InlineKeyboardButton(text="🔄 Начать новый диалог", callback_data="action_reset"),
            ],
        ]
    )
