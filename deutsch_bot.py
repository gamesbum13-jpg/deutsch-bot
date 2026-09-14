import asyncio
import logging
import random
import os
import json
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiohttp import web

BOT_TOKEN = "8994443509:AAHfD5CYvZYhGDOLeqEjErEAXqj-e8NxE3g"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ЗАВАНТАЖЕННЯ БАЗИ СЛІВ З JSON ---
def load_words():
    try:
        with open("words.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Помилка завантаження words.json: {e}")
        return [
            {"word": "die Herausforderung", "forms": "-en", "trans": "виклик", "ex": "Das ist eine Herausforderung.", "cat": "💼 Бізнес"}
        ]

WORDS_DATABASE = load_words()

# --- МЕНЮ ---
def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎴 Картки слів")
    kb.button(text="📂 Категорії слів")
    kb.button(text="🧠 Вікторина (Quiz)")
    kb.button(text="📖 Грамматика")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)

def categories_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💼 Бізнес & Робота", callback_data="cat_💼 Бізнес")
    kb.button(text="📱 IT & iPad", callback_data="cat_📱 IT & iPad")
    kb.button(text="💬 Розмовне / Загальне", callback_data="cat_💬 Розмовне")
    kb.button(text="🎲 Випадкове слово", callback_data="cat_all")
    kb.adjust(1)
    return kb.as_markup()

# --- ХЕНДЛЕРИ ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer("🚀 **DEUTSCH PRO оновлено!**\n\nБаза слів успішно підключена 📱💼\nОбирай дію в меню нижче 👇", reply_markup=main_menu(), parse_mode="Markdown")

@dp.message(F.text == "🎴 Картки слів")
async def show_random_card(message: types.Message):
    word = random.choice(WORDS_DATABASE)
    text = f"🏷 **Категорія:** {word.get('cat', 'Загальне')}\n\n🇩🇪 **Слово:** `{word['word']}`\n📝 **Форма:** _{word['forms']}_\n🇺🇦 **Переклад:** **{word['trans']}**\n💬 _{word['ex']}_"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📂 Категорії слів")
async def show_categories(message: types.Message):
    await message.answer("Обери категорію для вивчення:", reply_markup=categories_menu())

@dp.callback_query(F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery):
    cat_type = callback.data.replace("cat_", "")
    
    if cat_type == "all":
        filtered_words = WORDS_DATABASE
    else:
        filtered_words = [w for w in WORDS_DATABASE if w.get('cat') == cat_type]
        if not filtered_words:
            filtered_words = WORDS_DATABASE

    word = random.choice(filtered_words)
    text = f"🏷 **Категорія:** {word.get('cat', 'Загальне')}\n\n🇩🇪 **Слово:** `{word['word']}`\n📝 **Форма:** _{word['forms']}_\n🇺🇦 **Переклад:** **{word['trans']}**\n💬 _{word['ex']}_"
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# --- ІНТЕРАКТИВНА ВІКТОРИНА С 4 ВАРІАНТАМИ ---
@dp.message(F.text == "🧠 Вікторина (Quiz)")
async def start_quiz(message: types.Message):
    correct = random.choice(WORDS_DATABASE)
    others = [w for w in WORDS_DATABASE if w['trans'] != correct['trans']]
    
    # Вибираємо 3 випадкові неправильні відповіді
    wrongs = random.sample(others, min(3, len(others)))
    options = [correct['trans']] + [w['trans'] for w in wrongs]
    random.shuffle(options)
    
    kb = InlineKeyboardBuilder()
    for idx, opt in enumerate(options):
        is_correct = "1" if opt == correct['trans'] else "0"
        kb.button(text=opt, callback_data=f"ans_{is_correct}_{correct['word']}")
    kb.adjust(1)
    
    await message.answer(f"🧠 Як перекладається слово **{correct['word']}**?", reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("ans_"))
async def check_answer(callback: types.CallbackQuery):
    data_parts = callback.data.split("_", 2)
    is_correct = data_parts[1]
    word = data_parts[2]
    
    if is_correct == "1":
        await callback.message.edit_text(f"✅ **Правильно!**\n\n🇩🇪 `{word}`")
    else:
        await callback.message.edit_text(f"❌ **Неправильно!**\n\nСпробуй ще раз через меню вікторини.")
    await callback.answer()

@dp.message(F.text == "📖 Грамматика")
async def grammar_rules(message: types.Message):
    await message.answer("📚 **Perfekt:** `haben/sein` + `Partizip II`\n*Приклад:* Ich habe das gemacht.", parse_mode="Markdown")

@dp.message()
async def catch_all(message: types.Message):
    await message.answer("Натисни /start для відкриття меню!", reply_markup=main_menu())

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
