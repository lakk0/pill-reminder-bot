import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import os
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()
users = {}  # {user_id: {"took_pill": False}}

USERS_FILE = "users.json"


# ===== Работа с файлом =====
def load_users():
    global users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    else:
        users = {}


def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


# ===== Кнопка =====
def get_pill_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="💊 Я выпила", callback_data="took_pill"))
    return builder.as_markup()


# ===== Когда кто-то пишет боту =====
@dp.message()
async def register_user(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"took_pill": False}
        save_users()
        await message.answer("Привет, киска! 👋 Я буду напоминать тебе выпить таблетку каждый день в 22:00!")
    else:
        await message.answer("Я уже тебя помню 💊")


# ===== Отправляем напоминание =====
async def send_reminders():
    for user_id, data in users.items():
        users[user_id]["took_pill"] = False
        save_users()
        await bot.send_photo(
            user_id,
            photo="https://i.pinimg.com/736x/e4/d2/4e/e4d24ee70625de94c5fb4e973903af0c.jpg",
            caption="Выпей таблетку, котенок) 💊",
            reply_markup=get_pill_keyboard()
        )
        asyncio.create_task(reminder_loop(user_id))


# ===== Проверка каждые 2 минуты =====
async def reminder_loop(user_id):
    for _ in range(30):  # максимум 1 час
        await asyncio.sleep(120)
        if users[user_id]["took_pill"]:
            break
        await bot.send_message(
            user_id,
            "Моя любимая — не забудь выпить таблетку!",
            reply_markup=get_pill_keyboard()
        )


# ===== Когда человек нажимает кнопку =====
@dp.callback_query(lambda c: c.data == "took_pill")
async def pill_taken(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    if user_id in users:
        users[user_id]["took_pill"] = True
        save_users()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Отлично! 👏 Не забудь завтра тоже.")


# ===== Основная функция =====
async def main():
    load_users()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_reminders, 'cron', hour=22, minute=0)
    scheduler.start()

    print("✅ Бот запущен и готов работать с несколькими пользователями!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())