import asyncio
import logging
import sys
import os
import traceback

sys.path.append(os.path.abspath("."))
from google import genai
from google.genai import types
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_gemini():
    print(f"Loading GEMINI_API_KEY from config: '{config.GEMINI_API_KEY[:10]}...'")
    print(f"Loading GEMINI_MODEL: '{config.GEMINI_MODEL}'")

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents="Здравствуйте! Проверка связи.",
            config=types.GenerateContentConfig(
                system_instruction="Ты — AI-консультант по продажам."
            )
        )

        print("\n--- GEMINI SUCCESS RESPONSE ---")
        print(response.text)
        print("--------------------------------\n")
    except Exception as e:
        print("\n--- GEMINI ERROR TRACEBACK ---")
        logger.error(f"Gemini test failed with exception: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_gemini())
