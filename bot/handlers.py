import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatAction, ParseMode
from aiogram.types import Message, CallbackQuery

from services.ai_service import ai_service
from bot.keyboards import get_main_keyboard, get_consultation_quick_actions

logger = logging.getLogger(__name__)

router = Router(name="bot_router")

@router.message(CommandStart())
async def handle_start(message: Message):
    """Handler for Telegram /start command."""
    user_name = message.from_user.first_name if message.from_user else "уважаемый клиент"
    welcome_text = (
        f"👋 Здравствуйте, **{user_name}**!\n\n"
        f"Приветствую вас в автономном B2B AI-сервисе продаж.\n"
        f"Я умный **AI-консультант**, помогу вам подобрать решения для бизнеса, ответить на любые тарифные вопросы и оформить заявку.\n\n"
        f"💬 Напишите ваш вопрос или выберите действие ниже:"
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
    help_text = (
        "💡 **Инструкция по работе с AI-консультантом:**\n\n"
        "• Напишите любую задачу вашего бизнеса или интересующий вопрос.\n"
        "• Бот автоматически ведет диалог и адаптирует рекомендации.\n"
        "• Оставить заявку на звонок менеджера или консультацию можно прямо через нашего бота или на сайте.\n"
        "• Запустить диалог заново: `/reset` или кнопка **🔄 Сбросить диалог**."
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
        "🔄 История диалога очищена. Чем я могу помочь вашему бизнесу сегодня?",
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

@router.callback_query(F.data == "action_contact")
async def handle_callback_contact(callback: CallbackQuery):
    contact_text = (
        "📞 **Связь с отделом B2B продаж:**\n\n"
        "Вы можете оставить заявку на нашем веб-сайте `http://127.0.0.1:8000` "
        "или написать оператору. Наш менеджер свяжется с вами в ближайшее время!"
    )
    await callback.message.answer(contact_text, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

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
