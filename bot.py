import asyncio
import json
import os
from datetime import date
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
        # если файл битый — не ломаем бота
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
            "style": None,          # "classic" | "uncensored"
            "last_sent_date": None  # "YYYY-MM-DD"
        }
        save_json(USERS_FILE, users)
    return users[uid]


def update_user(user_id: int, **fields) -> None:
    users = load_json(USERS_FILE)
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "zodiac": None,
            "style": None,
            "last_sent_date": None,
        }
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
        one_time_keyboard=False,
    )


def zodiac_inline_keyboard() -> InlineKeyboardMarkup:
    rows = []
    row = []
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
                InlineKeyboardButton(
                    text="Классический", callback_data="set_style:classic"
                ),
                InlineKeyboardButton(
                    text="Без цензуры", callback_data="set_style:uncensored"
                ),
            ]
        ]
    )


def settings_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="♈ Сменить знак зодиака", callback_data="settings:change_zodiac"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎭 Сменить тип гороскопа", callback_data="settings:change_style"
                )
            ],
        ]
    )


# ---------------------------------------------------------
# Логика получения гороскопа
# ---------------------------------------------------------

def get_today_horoscope(
    zodiac: str, style: str, today: Optional[date] = None
) -> Optional[str]:
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
    if not text:
        return None

    if text.strip() == "":
        return None

    return text


# ---------------------------------------------------------
# /start
# ---------------------------------------------------------

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = get_or_create_user(message.from_user.id)

    text = (
        "🌀 Добро пожаловать в сюр-гороскопы.\n\n"
        "Сейчас выберем твой знак, потом стиль — классический или без цензуры.\n"
        "А дальше — каждый день свежий прогноз с лёгким налётом безумия."
    )

    await message.answer(text)
    await message.answer("Сначала выбери свой знак зодиака:", reply_markup=zodiac_inline_keyboard())


# ---------------------------------------------------------
# Выбор знака
# ---------------------------------------------------------

@dp.callback_query(F.data.startswith("set_zodiac:"))
async def cb_set_zodiac(query: CallbackQuery):
    zodiac = query.data.split(":", 1)[1]
    if zodiac not in ZODIAC_LABELS:
        await query.answer("Неизвестный знак.")
        return

    update_user(query.from_user.id, zodiac=zodiac)

    await query.message.answer(
        f"Знак зодиака установлен: {ZODIAC_LABELS[zodiac]}.\n\n"
        "Теперь выбери стиль гороскопа:",
        reply_markup=style_inline_keyboard(),
    )
    await query.answer()


# ---------------------------------------------------------
# Выбор стиля
# ---------------------------------------------------------

@dp.callback_query(F.data.startswith("set_style:"))
async def cb_set_style(query: CallbackQuery):
    style = query.data.split(":", 1)[1]
    if style not in ("classic", "uncensored"):
        await query.answer("Неизвестный стиль.")
        return

    update_user(query.from_user.id, style=style)

    style_label = "классический" if style == "classic" else "без цензуры"
    await query.message.answer(
        f"Стиль гороскопа установлен: {style_label}.\n\n"
        "Теперь можно получать ежедневный сюр-прогноз.",
        reply_markup=main_reply_keyboard(),
    )
    await query.answer()


# ---------------------------------------------------------
# Настройки
# ---------------------------------------------------------

@dp.message(Command("settings"))
async def cmd_settings(message: Message):
    user = get_or_create_user(message.from_user.id)

    zodiac = user.get("zodiac")
    style = user.get("style")

    zodiac_txt = ZODIAC_LABELS.get(zodiac, "не выбран")
    if style == "classic":
        style_txt = "классический"
    elif style == "uncensored":
        style_txt = "без цензуры"
    else:
        style_txt = "не выбран"

    text = (
        "⚙ Текущие настройки:\n"
        f"• Знак: {zodiac_txt}\n"
        f"• Стиль: {style_txt}\n\n"
        "Что хочешь изменить?"
    )

    await message.answer(text, reply_markup=settings_inline_keyboard())


@dp.message(F.text == "⚙ Настройки")
async def msg_settings_button(message: Message):
    await cmd_settings(message)


@dp.callback_query(F.data == "settings:change_zodiac")
async def cb_settings_change_zodiac(query: CallbackQuery):
    await query.message.answer(
        "Выбери новый знак зодиака:", reply_markup=zodiac_inline_keyboard()
    )
    await query.answer()


@dp.callback_query(F.data == "settings:change_style")
async def cb_settings_change_style(query: CallbackQuery):
    await query.message.answer(
        "Выбери новый тип гороскопа:", reply_markup=style_inline_keyboard()
    )
    await query.answer()


# ---------------------------------------------------------
# Гороскоп на сегодня (кнопка + команда)
# ---------------------------------------------------------

async def send_today_horoscope(message: Message):
    user = get_or_create_user(message.from_user.id)
    zodiac = user.get("zodiac")
    style = user.get("style")

    if not zodiac or not style:
        await message.answer(
            "Сначала нужно выбрать знак и стиль.\n"
            "Нажми /start, чтобы пройти настройку заново."
        )
        return

    today = date.today()
    text = get_today_horoscope(zodiac, style, today)

    if not text:
        await message.answer(
            "Сегодняшний гороскоп ещё в процессе вызревания.\n"
            "Загляни позже или на следующей неделе."
        )
        return

    zodiac_label = ZODIAC_LABELS.get(zodiac, "")
    style_label = "классический" if style == "classic" else "без цензуры"

    reply = (
        f"🌀 Сюр-гороскоп на сегодня\n"
        f"{zodiac_label} · {style_label}\n\n"
        f"{text}"
    )

    await message.answer(reply)


@dp.message(Command("today"))
async def cmd_today(message: Message):
    await send_today_horoscope(message)


@dp.message(F.text == "📜 Гороскоп на сегодня")
async def msg_today_button(message: Message):
    await send_today_horoscope(message)


# ---------------------------------------------------------
# Запуск
# ---------------------------------------------------------

async def main():
    await dp.start_polling(bot)

@dp.message(Command("stats"))
async def stats_cmd(message):
    # Доступ только владельцу
    if message.from_user.id != OWNER_ID:
        return await message.answer("Эта команда недоступна.")

    # Загружаем данные
    if not os.path.exists("users.json"):
        return await message.answer("users.json отсутствует.")

    with open("users.json", "r", encoding="utf-8") as f:
        users = json.load(f)

    total_users = len(users)

    classic_count = sum(1 for u in users.values() if u.get("type") == "classic")
    uncensored_count = sum(1 for u in users.values() if u.get("type") == "uncensored")

    # сколько уже получило гороскоп сегодня
    today = datetime.now().strftime("%Y-%m-%d")
    received_today = sum(1 for u in users.values() if u.get("last_sent_date") == today)

    # статистика по знакам
    sign_stats = {}
    for u in users.values():
        sign = u.get("sign")
        if sign:
            sign_stats[sign] = sign_stats.get(sign, 0) + 1

    # Формируем текст
    sign_lines = "\n".join([f"• {sign}: {count}" for sign, count in sign_stats.items()]) or "Нет данных"

    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"🌗 Classic: <b>{classic_count}</b>\n"
        f"🔥 Uncensored: <b>{uncensored_count}</b>\n"
        f"📬 Получили гороскоп сегодня: <b>{received_today}</b>\n\n"
        f"♈ Пользователи по знакам:\n{sign_lines}"
    )

    await message.answer(text)
    
if __name__ == "__main__":
    asyncio.run(main())
