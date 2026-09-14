import asyncio
import logging
import random
import os
from gtts import gTTS
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import FSInputFile
from aiohttp import web

# Токен вашого бота
BOT_TOKEN = "8994443509:AAHfD5CYvZYhGDOLeqEjErEAXqj-e8NxE3g"

logging.basicConfig(level=logging.INFO)

# Ініціалізація бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- БАЗА СЛІВ ---
WORDS_DATABASE = [
    (1, "die Herausforderung", "-en", "виклик, випробування", "Das ist eine große Herausforderung für mich.", "Робота"),
    (2, "entscheiden", "entschied, hat entschieden", "вирішувати", "Wir müssen uns schnell entscheiden.", "Загальне"),
    (3, "die Auswirkung", "-en", "вплив, наслідок", "Das hat direkte Auswirkungen auf die Wirtschaft.", "Бізнес"),
    (4, "vereinbaren", "vereinbarte, hat vereinbart", "узгоджувати", "Ich möchte einen Termin vereinbaren.", "Побут"),
    (5, "das Ergebnis", "-se", "результат", "Das Ergebnis war überraschend gut.", "Робота")
]

def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎴 Картки слів")
    kb.button(text="🧠 Вікторина (Quiz)")
    kb.button(text="📖 Грамматика A2-B1")
    kb.adjust(2, 1)
    return kb.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer("🚀 **DEUTSCH PRO працює!**\n\nОбирай дію в меню нижче 👇", reply_markup=main_menu(), parse_mode="Markdown")

@dp.message(F.text == "🎴 Картки слів")
async def show_card(message: types.Message):
    word = random.choice(WORDS_DATABASE)
    text = f"🇩🇪 **Слово:** `{word[1]}`\n📝 **Форма:** _{word[2]}_\n🇺🇦 **Переклад:** **{word[3]}**\n💬 _{word[4]}_"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🧠 Вікторина (Quiz)")
async def start_quiz(message: types.Message):
    correct_word = random.choice(WORDS_DATABASE)
    await message.answer(f"🧠 Як перекладається слово **{correct_word[1]}**?\n\n👉 Відповідь: **{correct_word[3]}**", parse_mode="Markdown")

@dp.message(F.text == "📖 Грамматика A2-B1")
async def grammar_rules(message: types.Message):
    await message.answer("📚 **Perfekt:** `haben/sein` + `Partizip II`\n*Приклад:* Ich habe das gemacht.", parse_mode="Markdown")

@dp.message()
async def catch_all(message: types.Message):
    await message.answer("Натисни /start, щоб відкрити головне меню!", reply_markup=main_menu())

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER FREE ---
async def handle_ping(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
