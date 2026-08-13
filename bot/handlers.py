import os
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatAction, ParseMode
from aiogram.types import Message, CallbackQuery

from services.ai_service import ai_service
from bot.keyboards import get_main_keyboard, get_consultation_quick_actions, get_site_url

logger = logging.getLogger(__name__)

router = Router(name="bot_router")

@router.message(CommandStart())
async def handle_start(message: Message):
    """Handler for Telegram /start command."""
    user_name = message.from_user.first_name if message.from_user else "уважаемый клиент"
    welcome_text = (
        f"👋 Привет, **{user_name}**! Я автономный бот компании **Sales Pro**.\n\n"
        f"Помогу вам подобрать решения для бизнеса, ответить на любые вопросы по тарифам и быстро оформить заявку.\n\n"
        f"💬 Напишите ваш вопрос или выберите действие в меню ниже:"
    )
    await message.answer(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def handle_help(message: Message):
    """Handler for /help command."""
    site_url = get_site_url()
    help_text = (
        "💡 **Инструкция по работе с ботом компании Sales Pro:**\n\n"
        "• Задайте любой интересующий вопрос по автоматизации B2B продаж.\n"
        "• Бот мгновенно рассчитает стоимость тарифа в сумах (UZS).\n"
        f"• Нажмите **🌐 Оформить заявку на сайте** для перехода на наш сайт: {site_url}\n"
        "• Нажмите **📞 Позвонить менеджеру** для связи с отделом продаж.\n"
        "• Перезапустить диалог: `/reset` или кнопка **🔄 Сбросить диалог**."
    )
    await message.answer(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

@router.message(Command("reset"))
@router.message(F.text == "🔄 Сбросить диалог")
async def handle_reset(message: Message):
    """Resets chat context."""
    user_id = str(message.from_user.id)
    ai_service.reset_chat(user_id)
    await message.answer(
        "🔄 История диалога очищена. Чем я могу помочь компании Sales Pro и вашему бизнесу сегодня?",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "action_reset")
async def handle_callback_reset(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    ai_service.reset_chat(user_id)
    await callback.message.answer(
        "🔄 Контекст диалога очищен. Чем могу помочь?",
        reply_markup=get_main_keyboard()
    )
    await callback.answer("Диалог очищен")

@router.message(F.text == "🌐 Оформить заявку на сайте")
async def handle_site_link(message: Message):
    """Sends direct working URL link to external website."""
    site_url = get_site_url()
    text = (
        f"🌐 **Оформить заявку на сайте Sales Pro**\n\n"
        f"Перейдите по прямой ссылке, чтобы выбрать тариф и оставить заявку:\n"
        f"🔗 [{site_url}]({site_url})"
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)

@router.message(F.text == "📞 Позвонить менеджеру")
@router.callback_query(F.data == "action_contact")
async def handle_contact_manager(event):
    """Sends contact phone number of sales department."""
    contact_text = (
        "📞 **Отдел продаж компании Sales Pro:**\n\n"
        "• **Телефон:** `+998 (77) 003 08 46`\n"
        "• **Email:** `contact@salespro.uz`\n"
        "• **График работы:** Пн — Сб, 09:00 — 18:00\n\n"
        "Наш старший менеджер ответит на все ваши вопросы и поможет с подключением!"
    )
    if isinstance(event, CallbackQuery):
        await event.message.answer(contact_text, parse_mode=ParseMode.MARKDOWN)
        await event.answer()
    else:
        await event.answer(contact_text, parse_mode=ParseMode.MARKDOWN)


@router.message(F.text == "💼 Получить B2B консультацию")
@router.message(F.text == "🎯 Подобрать тариф")
async def handle_menu_quick_prompts(message: Message):
    user_id = str(message.from_user.id)
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    response = await ai_service.generate_response(user_id, message.text, source="telegram")
    await message.answer(response, parse_mode=ParseMode.MARKDOWN, reply_markup=get_consultation_quick_actions())

@router.message(F.text)
async def handle_user_text(message: Message):
    """General text query handler."""
    user_id = str(message.from_user.id)
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    ai_response = await ai_service.generate_response(user_id, message.text, source="telegram")

    try:
        await message.answer(
            ai_response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_consultation_quick_actions()
        )
    except Exception:
        await message.answer(
            ai_response,
            reply_markup=get_consultation_quick_actions()
        )
