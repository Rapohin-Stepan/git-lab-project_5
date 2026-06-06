import os
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

from api import fetch_synonyms

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Ошибка: Не найден токен бота (BOT_TOKEN) в файле .env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Простая инициализация без кастомной сессии
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот для поиска синонимов.\n\n"
        "🔹 Отправь /help, чтобы узнать команды.\n"
        "🔹 Или сразу используй: /synonym <слово>"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 Доступные команды:\n"
        "• /start — Запуск бота\n"
        "• /help — Эта справка\n"
        "• /synonym <слово> — Найти синонимы\n\n"
        "💡 Пример: /synonym большой\n"
        "🌐 Данные берутся из публичного Datamuse API."
    )

@dp.message(Command("synonym"))
async def cmd_synonym(message: Message):
    # Разделяем текст на команду и аргумент
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ Пожалуйста, укажите слово после команды.\nПример: /synonym красивый")
        return

    word = parts[1].strip()
    if len(word) < 2:
        await message.answer("⚠️ Слово слишком короткое.")
        return

    await message.answer("⏳ Ищу синонимы...")
    
    try:
        synonyms = await fetch_synonyms(word)
        if not synonyms:
            await message.answer(f"😔 Синонимы для слова «{word}» не найдены. Попробуйте другое.")
        else:
            # Формируем читаемый список
            result = f"📝 Синонимы к слову «{word}»:\n" + "\n".join(f"• {syn}" for syn in synonyms)
            await message.answer(result)
    except ConnectionError as e:
        await message.answer(f"🌐 Ошибка подключения: {e}")
    except Exception as e:
        await message.answer(f"❌ Произошла непредвиденная ошибка. Попробуйте позже.")
        logging.error(f"Ошибка при обработке /synonym для '{word}': {e}")

async def main():
    logging.info("✅ Бот запущен и ожидает сообщения...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())