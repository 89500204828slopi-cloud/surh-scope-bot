import json
import os
from datetime import datetime
from aiogram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

with open("horoscopes.json", "r", encoding="utf-8") as f:
    HOROS = json.load(f)

today = datetime.now().date().isoformat()
users = load_users()

async def main():
    for uid, data in users.items():
        zodiac = data.get("zodiac")
        style = data.get("style", "classic")

        # НЕ слать, если пользователь уже получил сегодня
        if data.get("last_sent_date") == today:
            continue

        # Проверяем наличие гороскопа
        if today not in HOROS:
            continue
        if zodiac not in HOROS[today]:
            continue

        horoscope_text = HOROS[today][zodiac][style]

        try:
            await bot.send_message(
                int(uid),
                f"🔮 Твой новый сюр-гороскоп готов!\n\n{horoscope_text}"
            )
            # записываем, что он получил гороскоп
            data["last_sent_date"] = today

        except Exception as e:
            print(f"Не удалось отправить {uid}: {e}")

    save_users(users)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
