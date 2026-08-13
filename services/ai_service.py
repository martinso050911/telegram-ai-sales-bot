import logging
from groq import AsyncGroq
from sqlalchemy.future import select
from database.connection import AsyncSessionLocal
from database.models import SystemPromptConfig, ChatMessage
import config

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """Ты — высококлассный AI-консультант по продажам компании Sales Pro.
Твоя главная цель — выявлять потребности клиентов, профессионально презентовать продукты и решения компании Sales Pro, выявлять боли бизнеса, обрабатывать возражения и побуждать к оставлению заявки на консультацию или покупку.

СТРОГИЕ ЯЗЫКОВЫЕ ПРАВИЛА:
1. Отвечай ИСКЛЮЧИТЕЛЬНО на чистом, грамотном и естественном русском языке.
2. Категорически ЗАПРЕЩЕНО использовать любые китайские иероглифы (например, 客户, 帮助), китайские слова или гибриды вроде «客户ский»! Всегда используй исключительно чистое русское слово «клиентский» (например: «клиентский опыт», «клиентский сервис», «клиентская база»).

ВАЖНЕЙШЕЕ ПРАВИЛО ПО ВАЛЮТЕ И ЦЕНАМ:
1. Все цены, стоимости тарифов и финансовых условий ты обязан указывать ИСКЛЮЧИТЕЛЬНО в узбекских сумах (UZS).
2. Наша тарифная сетка компании Sales Pro:
   - Тариф «Старт»: 650 000 UZS / мес (до 1 000 чат-сессий, Telegram-бот).
   - Тариф «Бизнес Pro»: 1 700 000 UZS / мес (безлимитные сессии, веб-виджет + Telegram бот, защищенная админка).
   - Тариф «Enterprise»: Индивидуальный расчет под задачи клиента.
3. Категорически запрещено указывать рубли (руб, ₽) или любые другие валюты!

Правила работы:
1. Представляйся как AI-консультант компании Sales Pro.
2. Будь вежливым, деловым, позитивным и эмпатичным.
3. Задавай 1-2 уточняющих вопроса для погружения в сферу деятельности клиента.
4. Фокусируйся на выгодах, ROI и ценности для бизнеса.
5. Отвечай кратко, структурированно и с понятным призывом к действию (CTA).
6. При предложении оставить заявку напоминай про удобную форму на нашем сайте!
"""



class AISalesConsultantService:
    def __init__(self):
        logger.info(f"Initializing Groq Client with API key: '{config.GROQ_API_KEY[:10]}...' and model: '{config.GROQ_MODEL}'")
        self.client = AsyncGroq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
        self._user_chats = {}

    async def get_system_prompt(self) -> str:
        """Fetch active system prompt from DB or create default if not present."""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(SystemPromptConfig).where(SystemPromptConfig.key == "sales_consultant")
                )
                config_entry = result.scalar_one_or_none()
                if not config_entry:
                    config_entry = SystemPromptConfig(
                        key="sales_consultant",
                        prompt_text=DEFAULT_SYSTEM_PROMPT
                    )
                    db.add(config_entry)
                    await db.commit()
                    await db.refresh(config_entry)
                return config_entry.prompt_text
        except Exception as e:
            logger.error(f"Error fetching system prompt from DB: {e}. Using DEFAULT_SYSTEM_PROMPT.", exc_info=True)
            return DEFAULT_SYSTEM_PROMPT

    async def update_system_prompt(self, new_prompt: str) -> str:
        """Update system prompt in DB and invalidate cached session histories."""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(SystemPromptConfig).where(SystemPromptConfig.key == "sales_consultant")
                )
                config_entry = result.scalar_one_or_none()
                if not config_entry:
                    config_entry = SystemPromptConfig(
                        key="sales_consultant",
                        prompt_text=new_prompt
                    )
                    db.add(config_entry)
                else:
                    config_entry.prompt_text = new_prompt
                await db.commit()
                self._user_chats.clear()  # Reset active memory sessions to pick up new prompt
                logger.info("System prompt updated successfully in DB and active session histories reset.")
                return config_entry.prompt_text
        except Exception as e:
            logger.error(f"Error updating system prompt in DB: {e}", exc_info=True)
            raise

    async def generate_response(self, session_id: str, user_text: str, source: str = "web") -> str:
        """Generates AI response via Groq API and logs dialogue to SQLite database."""
        session_id_str = str(session_id)
        
        # 1. Save user message to SQLite Database
        try:
            async with AsyncSessionLocal() as db:
                user_msg = ChatMessage(
                    session_id=session_id_str,
                    source=source,
                    sender="user",
                    content=user_text
                )
                db.add(user_msg)
                await db.commit()
        except Exception as db_err:
            logger.error(f"Failed to log user message to DB: {db_err}", exc_info=True)

        # Retrieve system prompt
        sys_prompt = await self.get_system_prompt()

        # Initialize session history list if not present
        if session_id_str not in self._user_chats:
            self._user_chats[session_id_str] = []

        history = self._user_chats[session_id_str]
        
        # Construct message payload for Groq chat completions
        messages = [{"role": "system", "content": sys_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})

        try:
            logger.info(f"Sending request to Groq API (model: {self.model}) for session '{session_id_str}'...")
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            ai_text = completion.choices[0].message.content
            
            # Update active chat memory history
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": ai_text})

        except Exception as e:
            logger.error(f"🚨 [Groq API Error] Exception during generation for session '{session_id_str}': {e}", exc_info=True)
            ai_text = f"Произошла ошибка при обращении к Groq AI: {e}"

        # 2. Save AI response to SQLite Database
        try:
            async with AsyncSessionLocal() as db:
                ai_msg = ChatMessage(
                    session_id=session_id_str,
                    source=source,
                    sender="ai",
                    content=ai_text
                )
                db.add(ai_msg)
                await db.commit()
        except Exception as db_err:
            logger.error(f"Failed to log AI response to DB: {db_err}", exc_info=True)

        return ai_text

    def reset_chat(self, session_id: str):
        """Resets active chat session in memory."""
        session_id_str = str(session_id)
        if session_id_str in self._user_chats:
            del self._user_chats[session_id_str]

ai_service = AISalesConsultantService()
