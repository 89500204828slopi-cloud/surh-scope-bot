import asyncio
import json
import os
from datetime import date, datetime
from typing import Dict, Any, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from dotenv import load_dotenv

# ---------------------------------------------------------
# Настройки
# ---------------------------------------------------------

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # ← Твой ID берётся из .env

if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN в .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

USERS_FILE = "users.json"
HOROS_FILE = "horoscopes.json"

ZODIAC_ORDER = [
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
]

ZODIAC_LABELS = {
    "aries": "♈ Овен",
    "taurus": "♉ Телец",
    "gemini": "♊ Близнецы",
    "cancer": "♋ Рак",
    "leo": "♌ Лев",
    "virgo": "♍ Дева",
    "libra": "♎ Весы",
    "scorpio": "♏ Скорпион",
    "sagittarius": "♐ Стрелец",
    "capricorn": "♑ Козерог",
    "aquarius": "♒ Водолей",
    "pisces": "♓ Рыбы",
}


# ---------------------------------------------------------
# Работа с файлами
# ---------------------------------------------------------

def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_or_create_user(user_id: int) -> Dict[str, Any]:
    users = load_json(USERS_FILE)
    uid = str(user_id)

    if uid not in users:
        users[uid] = {
            "zodiac": None,
            "style": None,
            "last_sent_date": None
        }
        save_json(USERS_FILE, users)

    return users[uid]


def update_user(user_id: int, **fields) -> None:
    users = load_json(USERS_FILE)
    uid = str(user_id)

    if uid not in users:
        users[uid] = {"zodiac": None, "style": None, "last_sent_date": None}

    users[uid].update(fields)
    save_json(USERS_FILE, users)


def load_horoscopes() -> Dict[str, Any]:
    return load_json(HOROS_FILE)


# ---------------------------------------------------------
# Клавиатуры
# ---------------------------------------------------------

def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📜 Гороскоп на сегодня")],
            [KeyboardButton(text="⚙ Настройки")],
        ],
        resize_keyboard=True,
    )


def zodiac_inline_keyboard() -> InlineKeyboardMarkup:
    rows, row = [], []

    for i, z in enumerate(ZODIAC_ORDER, start=1):
        row.append(
            InlineKeyboardButton(
                text=ZODIAC_LABELS[z],
                callback_data=f"set_zodiac:{z}",
            )
        )
        if i % 3 == 0:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def style_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Классический", callback_data="set_style:classic"),
                InlineKeyboardButton(text="Без цензуры", callback_data="set_style:uncensored"),
            ]
        ]
    )


def settings_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="♈ Сменить знак зодиака", callback_data="settings:change_zodiac")],
            [InlineKeyboardButton(text="🎭 Сменить тип гороскопа", callback_data="settings:change_style")],
        ]
    )


# ---------------------------------------------------------
# Логика гороскопа
# ---------------------------------------------------------

def get_today_horoscope(zodiac: str, style: str, today: Optional[date] = None) -> Optional[str]:
    if today is None:
        today = date.today()

    horoscopes = load_horoscopes()
    today_key = today.isoformat()

    day_block = horoscopes.get(today_key)
    if not day_block:
        return None

    sign_block = day_block.get(zodiac)
    if not sign_block:
        return None

    text = sign_block.get(style)
    if not text or not text.strip():
        return None

    return text


# ---------------------------------------------------------
# /start
# ---------------------------------------------------------

@dp.message(Command("start"))
async def cmd_start(message: Message):
    get_or_create_user(message.from_user.id)

    txt = (
        "🌀 Добро пожаловать в сюр-гороскопы!\n\n"
        "Сначала выбери знак, затем стиль — классический или без цензуры."
    )

    await message.answer(txt)
    await message.answer("Выбери свой знак:", reply_markup=zodiac_inline_keyboard())


# ---------------------------------------------------------
# Выбор знака
# ---------------------------------------------------------

@dp.callback_query(F.data.startswith("set_zodiac:"))
async def cb_set_zodiac(query: CallbackQuery):
    zodiac = query.data.split(":", 1)[1]

    update_user(query.from_user.id, zodiac=zodiac)

    await query.message.answer(
        f"Знак установлен: {ZODIAC_LABELS[zodiac]}.\nТеперь выбери стиль:",
        reply_markup=style_inline_keyboard(),
    )
    await query.answer()


# ---------------------------------------------------------
# Выбор стиля
# ---------------------------------------------------------

@dp.callback_query(F.data.startswith("set_style:"))
async def cb_set_style(query: CallbackQuery):
    style = query.data.split(":", 1)[1]

    update_user(query.from_user.id, style=style)

    style_label = "классический" if style == "classic" else "без цензуры"

    await query.message.answer(
        f"Стиль установлен: {style_label}.",
        reply_markup=main_reply_keyboard(),
    )
    await query.answer()


# ---------------------------------------------------------
# Настройки
# ---------------------------------------------------------

@dp.message(Command("settings"))
async def cmd_settings(message: Message):
    user = get_or_create_user(message.from_user.id)

    zodiac_txt = ZODIAC_LABELS.get(user.get("zodiac"), "не выбран")
    style_txt = {"classic": "классический", "uncensored": "без цензуры"}.get(
        user.get("style"), "не выбран"
    )

    text = (
        "⚙ Текущие настройки:\n"
        f"• Знак: {zodiac_txt}\n"
        f"• Стиль: {style_txt}\n"
    )

    await message.answer(text, reply_markup=settings_inline_keyboard())


@dp.message(F.text == "⚙ Настройки")
async def msg_settings_button(message: Message):
    await cmd_settings(message)


@dp.callback_query(F.data == "settings:change_zodiac")
async def cb_settings_change_zodiac(query: CallbackQuery):
    await query.message.answer("Выбери новый знак:", reply_markup=zodiac_inline_keyboard())
    await query.answer()


@dp.callback_query(F.data == "settings:change_style")
async def cb_settings_change_style(query: CallbackQuery):
    await query.message.answer("Выбери стиль:", reply_markup=style_inline_keyboard())
    await query.answer()


# ---------------------------------------------------------
# Гороскоп на сегодня
# ---------------------------------------------------------

async def send_today_horoscope(message: Message):
    user = get_or_create_user(message.from_user.id)

    zodiac = user.get("zodiac")
    style = user.get("style")

    if not zodiac or not style:
        return await message.answer("Сначала выбери знак и стиль (/start).")

    today = date.today()
    text = get_today_horoscope(zodiac, style, today)

    if not text:
        return await message.answer("Гороскоп на сегодня ещё не готов.")

    reply = (
        f"🌀 Сюр-гороскоп на сегодня\n"
        f"{ZODIAC_LABELS[zodiac]} · {('классический' if style == 'classic' else 'без цензуры')}\n\n"
        f"{text}"
    )

    # отмечаем получение гороскопа
    update_user(message.from_user.id, last_sent_date=today.isoformat())

    await message.answer(reply)


@dp.message(Command("today"))
async def cmd_today(message: Message):
    await send_today_horoscope(message)


@dp.message(F.text == "📜 Гороскоп на сегодня")
async def msg_today_button(message: Message):
    await send_today_horoscope(message)


# ---------------------------------------------------------
# 📊 Статистика
# ---------------------------------------------------------

@dp.message(Command("stats"))
async def stats_cmd(message: Message):

    if message.from_user.id != OWNER_ID:
        return await message.answer("Эта команда доступна только администратору.")

    if not os.path.exists(USERS_FILE):
        return await message.answer("users.json отсутствует.")

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)

    total_users = len(users)

    classic_count = sum(1 for u in users.values() if u.get("style") == "classic")
    uncensored_count = sum(1 for u in users.values() if u.get("style") == "uncensored")

    today = datetime.now().strftime("%Y-%m-%d")
    received_today = sum(1 for u in users.values() if u.get("last_sent_date") == today)

    # статистика по знакам
    sign_stats = {}
    for u in users.values():
        sign = u.get("zodiac")
        if sign:
            sign_stats[sign] = sign_stats.get(sign, 0) + 1

    sign_lines = "\n".join(
        f"• {ZODIAC_LABELS.get(sign, sign)}: {count}"
        for sign, count in sign_stats.items()
    ) or "Нет данных"

    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"🌗 Classic: <b>{classic_count}</b>\n"
        f"🔥 Uncensored: <b>{uncensored_count}</b>\n"
        f"📬 Получили гороскоп сегодня: <b>{received_today}</b>\n\n"
        f"♈ Пользователи по знакам:\n{sign_lines}"
    )

    await message.answer(text, parse_mode="HTML")
    def admin_menu_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
            [InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin:users")],
            [InlineKeyboardButton(text="📝 Последние регистрации", callback_data="admin:last10")],
            [InlineKeyboardButton(text="📬 Рассылка", callback_data="admin:broadcast")],
            [InlineKeyboardButton(text="🌗 Статистика по стилям", callback_data="admin:styles")],
            [InlineKeyboardButton(text="♈ Статистика по знакам", callback_data="admin:signs")],
        ]
    )
@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.answer("Команда недоступна.")
    
    await message.answer(
        "🛠 <b>Админ-панель</b>\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard()
    )
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@dp.callback_query(F.data == "admin:stats")
async def admin_stats(query: CallbackQuery):
    users = load_users()

    total = len(users)
    classic = sum(1 for u in users.values() if u.get("style") == "classic")
    uncensored = sum(1 for u in users.values() if u.get("style") == "uncensored")

    today = datetime.now().strftime("%Y-%m-%d")
    received = sum(1 for u in users.values() if u.get("last_sent_date") == today)

    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"🌗 Classic: <b>{classic}</b>\n"
        f"🔥 Uncensored: <b>{uncensored}</b>\n"
        f"📬 Получили гороскоп сегодня: <b>{received}</b>\n"
    )

    await query.message.edit_text(text, parse_mode="HTML", reply_markup=admin_menu_keyboard())
    await query.answer()
@dp.callback_query(F.data == "admin:users")
async def admin_users(query: CallbackQuery):
    users = load_users()

    if not users:
        await query.answer("Нет пользователей.", show_alert=True)
        return

    lines = []
    for uid, data in users.items():
        zodiac = data.get("zodiac") or "не выбран"
        style = data.get("style") or "-"
        lines.append(f"{uid} · {zodiac} · {style}")

    text = "👥 <b>Пользователи:</b>\n\n" + "\n".join(lines)

    await query.message.edit_text(text, parse_mode="HTML", reply_markup=admin_menu_keyboard())
    await query.answer()
@dp.callback_query(F.data == "admin:last10")
async def admin_last10(query: CallbackQuery):
    users = load_users()

    last10 = list(users.items())[-10:]
    lines = []

    for uid, data in last10:
        zodiac = data.get("zodiac") or "-"
        style = data.get("style") or "-"
        lines.append(f"{uid} · {zodiac} · {style}")

    text = "📝 <b>Последние регистрации:</b>\n\n" + "\n".join(lines)

    await query.message.edit_text(text, parse_mode="HTML", reply_markup=admin_menu_keyboard())
    await query.answer()
@dp.callback_query(F.data == "admin:signs")
async def admin_signs(query: CallbackQuery):
    users = load_users()
    stats = {}

    for u in users.values():
        z = u.get("zodiac")
        if z:
            stats[z] = stats.get(z, 0) + 1

    lines = "\n".join(f"{ZODIAC_LABELS.get(sign)}: {count}" for sign, count in stats.items())
    text = "♈ <b>Пользователи по знакам:</b>\n\n" + lines

    await query.message.edit_text(text, parse_mode="HTML", reply_markup=admin_menu_keyboard())
    await query.answer()
@dp.callback_query(F.data == "admin:styles")
async def admin_styles(query: CallbackQuery):
    users = load_users()

    classic = sum(1 for u in users.values() if u.get("style") == "classic")
    uncensored = sum(1 for u in users.values() if u.get("style") == "uncensored")

    text = (
        "🌗 <b>Статистика по стилям:</b>\n\n"
        f"Классический: {classic}\n"
        f"Без цензуры: {uncensored}"
    )

    await query.message.edit_text(text, parse_mode="HTML", reply_markup=admin_menu_keyboard())
    await query.answer()
@dp.callback_query(F.data == "admin:broadcast")
async def admin_broadcast(query: CallbackQuery):
    await query.message.answer("Введите текст рассылки:")
    query.bot.broadcast_mode = True
    await query.answer()
@dp.message(F.text)
async def broadcast_handler(message: Message):
    if not hasattr(bot, "broadcast_mode"):
        return

    users = load_users()
    text = message.text

    count = 0
    for uid in users.keys():
        try:
            await bot.send_message(uid, text)
            count += 1
        except:
            pass

    await message.answer(f"Готово! Отправлено {count} пользователям.")
    del bot.broadcast_mode


# ---------------------------------------------------------
# Запуск
# ---------------------------------------------------------

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
