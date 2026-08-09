import logging
from google import genai
from google.genai import types
import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — высококлассный AI-консультант по продажам.
Твоя главная цель — выявлять потребности клиентов, грамотно и вежливо презентовать продукты и услуги, профессионально обрабатывать возражения и помогать клиенту сделать наилучший выбор.

Правила работы:
1. Будь вежливым, позитивным и эмпатичным.
2. Задавай 1-2 уточняющих вопроса, чтобы лучше понять задачи и боли клиента.
3. Объясняй выгоду и ценность продукта, а не только технические параметры.
4. Используй красивое Telegram-форматирование (жирный шрифт, списки, эмодзи).
5. Завершай ответ мягким призывом к действию (Call to Action) или уточняющим вопросом.
6. Отвечай на том языке, на котором пишет клиент (по умолчанию на русском).
"""

class AISalesConsultant:
    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = config.GEMINI_MODEL
        # Dict to store user active chat sessions: user_id -> chat object
        self._user_chats = {}

    def _create_chat_session(self):
        """Creates a new async chat session with system prompt configuration."""
        return self.client.aio.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            )
        )

    def get_or_create_chat(self, user_id: int):
        """Retrieves an existing chat session or initializes a new one for user."""
        if user_id not in self._user_chats:
            self._user_chats[user_id] = self._create_chat_session()
        return self._user_chats[user_id]

    async def generate_sales_response(self, user_id: int, text: str) -> str:
        """Sends a message to the AI chat session and returns the AI sales consultant response."""
        try:
            chat = self.get_or_create_chat(user_id)
            response = await chat.send_message(text)
            return response.text or "Извините, не удалось сформировать ответ. Попробуйте еще раз."
        except Exception as e:
            logger.error(f"Error generating AI response for user {user_id}: {e}")
            # If session state was invalidated, recreate session and retry once
            try:
                self.reset_chat(user_id)
                chat = self.get_or_create_chat(user_id)
                response = await chat.send_message(text)
                return response.text or "Извините, произошла ошибка. Обратитесь снова."
            except Exception as retry_err:
                logger.error(f"Retry failed for user {user_id}: {retry_err}")
                return "К сожалению, произошел сбой при связи с AI-сервисом. Попробуйте позже."

    def reset_chat(self, user_id: int):
        """Resets dialogue history for a specific user."""
        if user_id in self._user_chats:
            del self._user_chats[user_id]

# Singleton instance
ai_service = AISalesConsultant()
