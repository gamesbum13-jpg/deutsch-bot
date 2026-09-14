# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
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
    await start_web_server()  # Запускаємо веб-сервер
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

BOT_TOKEN = "8994443509:AAHfD5CYvZYhGDOLeqEjErEAXqj-e8NxE3g"
MY_TELEGRAM_ID = 882424834

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- БАЗА ДАНИХ ТА СЛОВНИК A2-B1 ---
WORDS_DATABASE = [
    # (id, german, plural, ukrainian, example, category)
    (1, "die Herausforderung", "-en", "виклик, випробування", "Das ist eine große Herausforderung für mich.", "Робота/Бізнес"),
    (2, "entscheiden", "entschied, hat entschieden", "вирішувати", "Wir müssen uns schnell entscheiden.", "Загальне"),
    (3, "die Auswirkung", "-en", "вплив, наслідок", "Das hat direkte Auswirkungen auf die Wirtschaft.", "Бізнес/Політика"),
    (4, "vereinbaren", "vereinbarte, hat vereinbart", "узгоджувати, домовлятися", "Ich möchte einen Termin vereinbaren.", "Побут/Офіс"),
    (5, "das Ergebnis", "-se", "результат", "Das Ergebnis war überraschend gut.", "Робота"),
    (6, "überzeugen", "überzeugte, hat überzeugt", "переконувати", "Seine Argumente haben mich überzeugt.", "Спілкування"),
    (7, "die Voraussetzung", "-en", "передумова, вимога", "Gute Deutschkenntnisse sind die Voraussetzung.", "Робота"),
    (8, "stattfinden", "fand statt, hat stattgefunden", "відбуватися, проходити", "Das Treffen findet morgen statt.", "Події"),
    (9, "der Einfluss", "die Einflüsse", "вплив", "Er hat großen Einfluss auf das Team.", "Спілкування"),
    (10, "verfügbar", "-", "доступний, у наявності", "Diese Option ist derzeit nicht verfügbar.", "IT/Побут"),
    (11, "die Vorbereitung", "-en", "підготовка", "Die Vorbereitung dauert zwei Wochen.", "Навчання/Робота"),
    (12, "abhängen von", "hing ab, hat abgehangen", "залежати від", "Es hängt vom Wetter ab.", "Розмовне"),
    (13, "die Entwicklung", "-en", "розвиток, розробка", "Die Entwicklung dieser App läuft gut.", "IT/Бізнес"),
    (14, "empfehlen", "empfahl, hat empfohlen", "рекомендувати", "Was können Sie mir empfehlen?", "Побут"),
    (15, "die Verantwortung", "-en", "відповідальність", "Ich übernehme die Verantwortung dafür.", "Робота")
]

def init_db():
    conn = sqlite3.connect("deutsch_learning.db")
    cursor = conn.cursor()
    
    # Таблиця налаштувань користувача
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            daily_limit INTEGER DEFAULT 5,
            is_paused INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 1
        )
    """)
    
    # Таблиця прогресу вивчення слів
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_words (
            user_id INTEGER,
            word_id INTEGER,
            status TEXT DEFAULT 'learning', -- 'learned', 'review', 'learning'
            PRIMARY KEY (user_id, word_id)
        )
    """)
    conn.commit()
    conn.close()

def get_user_config(user_id):
    conn = sqlite3.connect("deutsch_learning.db")
    cursor = conn.cursor()
    cursor.execute("SELECT daily_limit, is_paused FROM user_settings WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if not res:
        cursor.execute("INSERT INTO user_settings (user_id, daily_limit, is_paused) VALUES (?, 5, 0)", (user_id,))
        conn.commit()
        res = (5, 0)
    conn.close()
    return {"limit": res[0], "paused": res[1]}

def update_user_config(user_id, limit=None, paused=None):
    conn = sqlite3.connect("deutsch_learning.db")
    cursor = conn.cursor()
    if limit is not None:
        cursor.execute("UPDATE user_settings SET daily_limit = ? WHERE user_id = ?", (limit, user_id))
    if paused is not None:
        cursor.execute("UPDATE user_settings SET is_paused = ? WHERE user_id = ?", (paused, user_id))
    conn.commit()
    conn.close()

# --- КЛАВІАТУРИ ---
def main_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎴 Учити слова")
    kb.button(text="🔄 На повторення")
    kb.button(text="📊 Статистика")
    kb.button(text="⚙️ Налаштування")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)

def card_inline_kb(word_id, revealed=False):
    builder = InlineKeyboardBuilder()
    if not revealed:
        builder.button(text="👁 Показати переклад", callback_data=f"reveal_{word_id}")
    else:
        builder.button(text="✅ Знаю!", callback_data=f"know_{word_id}")
        builder.button(text="🔁 На повтор", callback_data=f"repeat_{word_id}")
    builder.adjust(1)
    return builder.as_markup()

# --- МІДЛВАР ПЕРЕВІРКИ ---
@dp.message.outer_middleware()
async def check_access(handler, event: types.Message, data):
    if event.from_user.id != MY_TELEGRAM_ID:
        await event.answer("⛔️ Це приватний бот для вивчення німецької.")
        return
    return await handler(event, data)

# --- ХЕНДЛЕРИ ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    get_user_config(message.from_user.id)
    await message.answer(
        "🇩🇪 **Willkommen! Ласкаво просимо до німецького тренажера A2➔B1!**\n\n"
        "Тут ти будеш вчити актуальні німецькі слова за допомогою інтерактивних карток, "
        "формувати свій активний словник та отримувати щоденні тренування.\n\n"
        "Обери дію в меню нижче 👇",
        reply_markup=main_menu_kb()
    )

@dp.message(F.text == "🎴 Учити слова")
async def start_cards(message: types.Message):
    config = get_user_config(message.from_user.id)
    if config["paused"]:
        await message.answer("⏸ Твоє щоденне навчання зараз на паузі. Віднови його в ⚙️ Налаштуваннях.")
        return

    # Беремо перше доступне слово з бази
    word = WORDS_DATABASE[0] 
    
    text = (
        f"🎯 **Слово:** `{word[1]}`\n"
        f"📚 **Форма/Plural:** _{word[2]}_\n"
        f"🏷 **Категорія:** {word[5]}\n\n"
        f"💬 **Приклад:**\n_{word[4]}_"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=card_inline_kb(word[0], revealed=False))

@dp.callback_query(F.data.startswith("reveal_"))
async def reveal_card(call: types.CallbackQuery):
    word_id = int(call.data.split("_")[1])
    word = next((w for w in WORDS_DATABASE if w[0] == word_id), None)
    
    if word:
        text = (
            f"🎯 **Слово:** `{word[1]}`\n"
            f"📚 **Форма/Plural:** _{word[2]}_\n\n"
            f"🇺🇦 **Переклад:** **{word[3]}**\n\n"
            f"💬 **Приклад:**\n_{word[4]}_"
        )
        await call.message.edit_text(text, parse_mode="Markdown", reply_markup=card_inline_kb(word_id, revealed=True))
    await call.answer()

@dp.callback_query(F.data.startswith("know_"))
async def know_word(call: types.CallbackQuery):
    word_id = int(call.data.split("_")[1])
    # Позначити як вивчене
    conn = sqlite3.connect("deutsch_learning.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO user_words (user_id, word_id, status) VALUES (?, ?, 'learned')",
                   (call.from_user.id, word_id))
    conn.commit()
    conn.close()
    
    await call.answer("👍 Чудово! Додано в засвоєні.")
    await call.message.edit_text("🎉 **Слово засвоєно!** Тисни «🎴 Учити слова» для наступного.")

@dp.callback_query(F.data.startswith("repeat_"))
async def repeat_word(call: types.CallbackQuery):
    word_id = int(call.data.split("_")[1])
    conn = sqlite3.connect("deutsch_learning.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO user_words (user_id, word_id, status) VALUES (?, ?, 'review')",
                   (call.from_user.id, word_id))
    conn.commit()
    conn.close()
    
    await call.answer("🔁 Відправлено на повторення.")
    await call.message.edit_text("🔄 **Слово збережено у блок повторення.**")

@dp.message(F.text == "⚙️ Налаштування")
async def settings_menu(message: types.Message):
    config = get_user_config(message.from_user.id)
    status = "⏸ На паузі" if config["paused"] else "▶️ Активно"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="5 слів / день", callback_data="set_limit_5")
    builder.button(text="10 слів / день", callback_data="set_limit_10")
    if config["paused"]:
        builder.button(text="▶️ Відновити навчання", callback_data="toggle_pause_0")
    else:
        builder.button(text="⏸ Поставити на паузу", callback_data="toggle_pause_1")
    builder.adjust(2, 1)

    await message.answer(
        f"⚙️ **Налаштування профілю:**\n\n"
        f"• Поточна денна норма: **{config['limit']} слів**\n"
        f"• Стан розсилки: **{status}**\n\n"
        f"Обери потрібний параметр нижче:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("set_limit_"))
async def set_limit(call: types.CallbackQuery):
    limit = int(call.data.split("_")[2])
    update_user_config(call.from_user.id, limit=limit)
    await call.answer(f"✅ Встановлено норму: {limit} слів/день")
    await call.message.edit_text(f"🎯 Денну норму оновлено до **{limit} слів на день**.")

@dp.callback_query(F.data.startswith("toggle_pause_"))
async def toggle_pause(call: types.CallbackQuery):
    val = int(call.data.split("_")[2])
    update_user_config(call.from_user.id, paused=val)
    st = "призупинено ⏸" if val == 1 else "відновлено ▶️"
    await call.answer(f"Навчання {st}")
    await call.message.edit_text(f"Статус розсилки: **Навчання {st}**.")

@dp.message(F.text == "📊 Статистика")
async def stats_view(message: types.Message):
    conn = sqlite3.connect("deutsch_learning.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_words WHERE user_id = ? AND status = 'learned'", (message.from_user.id,))
    learned_cnt = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM user_words WHERE user_id = ? AND status = 'review'", (message.from_user.id,))
    review_cnt = cursor.fetchone()[0] or 0
    conn.close()

    await message.answer(
        f"📊 **Твій прогрес вивчення німецької:**\n\n"
        f"🏆 Вивчених слів (A2-B1): **{learned_cnt}**\n"
        f"🔄 Слів на повторенні: **{review_cnt}**\n"
        f"🔥 Поточний Streak: **3 дні поспіль**\n\n"
        f"💪 *Продовжуй у тому ж дусі! Weiter so!*"
    )

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
