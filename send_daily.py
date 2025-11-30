import asyncio
import json
import os
from datetime import date
from typing import Dict, Any

from aiogram import Bot
from dotenv import load_dotenv

USERS_FILE = "users.json"
HOROS_FILE = "horoscopes.json"


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


async def main():
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("Не найден BOT_TOKEN в .env")

    bot = Bot(token=bot_token)

    users = load_json(USERS_FILE)
    horoscopes = load_json(HOROS_FILE)

    today = date.today()
    today_key = today.isoformat()

    day_block = horoscopes.get(today_key)
    if not day_block:
        # нет гороскопов на сегодня — ничего не делаем
        await bot.session.close()
        return

    changed = False

    for uid, udata in users.items():
        zodiac = udata.get("zodiac")
        style = udata.get("style")
        last_sent = udata.get("last_sent_date")

        if not zodiac or not style:
            continue

        # уже отправляли сегодня
        if last_sent == today_key:
            continue

        sign_block = day_block.get(zodiac)
        if not sign_block:
            continue

        text = sign_block.get(style)
        if not text or text.strip() == "":
            continue

        msg_text = f"🌀 Твой сюр-гороскоп на сегодня:\n\n{text}"

        try:
            await bot.send_message(int(uid), msg_text)
            udata["last_sent_date"] = today_key
            changed = True
        except Exception:
            # заблокировал бота или другая ошибка — пропускаем
            continue

    if changed:
        save_json(USERS_FILE, users)

    # Очистка старых дат в horoscopes.json
    cleaned = {}
    for dkey, block in horoscopes.items():
        try:
            d_date = date.fromisoformat(dkey)
        except ValueError:
            continue
        # оставляем только сегодняшнюю и будущие
        if d_date >= today:
            cleaned[dkey] = block

    save_json(HOROS_FILE, cleaned)

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
