import asyncio
import os

from dotenv import load_dotenv
from handlers import router

from func import is_emoji_only, sanitize_text, split_message

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
import keyboard as kb
from collections import defaultdict

from openai import AsyncOpenAI
from config import AI_TOKEN, ADMIN_GROUP_ID

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=AI_TOKEN,
)

active_requests: set[int] = set()

chat_history = defaultdict(list)

class Gen(StatesGroup):
    waiting = State()

async def ai_generate(text: str) -> str:
    try:
        completion = await client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1:free",
            messages=[{"role": "user", "content": text}],
        )
        if not completion.choices:
            return "Модель не вернула ответа."
        return completion.choices[0].message.content
    except Exception as e:
        return f"Ошибка: {e}"

async def ai_analyze_image(img_url: str) -> str:
    try: # qwen/qwen3-vl-235b-a22b-thinking
        completion = await client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Опиши, что изображено на фото:"},
                    {"type": "image_url", "image_url": {"url": img_url}},
                ],
            }],
        )
        if not completion.choices:
            return "Модель не вернула анализ"
        return completion.choices[0].message.content
    except Exception as e:
        return f"Ошибка при анализе изображения: {e}"

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer_sticker(
        'CAACAgIAAxkBAAOtaMa_dmkx7FarFK2RGi1Ze_zoPzMAAkQAA0QNzxdTIKghIbDQHjYE')
    await message.answer(
        f"Привет, {message.from_user.first_name}👋\n\n Я готов помочь тебе, отвечая на вопросы."
        "\nИли же анализом изображений. Всевозможное управление мной ― внизу 👇",
        reply_markup=kb.firstinfo)

@dp.message(F.text == "Очистить чат")
async def clear_chat(message: types.Message):
    chat_id = message.chat.id

    for msg_id in range(message.message_id, message.message_id - 50, -1):
        try:
            await bot.delete_message(chat_id, msg_id)
        except:
            pass
    await bot.send_message(chat_id, "Чат очищен.\n Выбери модель общения снова!.", 
                           reply_markup=kb.firstinfo)

@dp.message(F.text)
async def generating(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    full_name = message.from_user.full_name

    if is_emoji_only(message.text):
        await message.reply(
            "Отличный выбор эмодзи, но сообщение не имеет символов, я не могу его обработать.")
        return

    if user_id in active_requests:
        await message.reply("⏳ Подожди! Твой предыдущий запрос ещё обрабатывается.")
        return

    if len(message.text) > 1000:
        await message.reply("Сообщение слишком длинное! До 1000 символов.")
        return

    log_text = (
        f"👤 Новый запрос\n"
        f"ID: <code>{user_id}</code>\n"
        f"Имя: {full_name}\n"
        f"Username: @{username}\n\n"
        f"Запрос: {message.text}"
    )
    await bot.send_message(ADMIN_GROUP_ID, log_text, parse_mode="HTML")
    active_requests.add(user_id)
    thinking_msg = None

    try:
        thinking_msg = await message.answer(
"⌛ Думаю над ответом...\n\n Иногда ответ приходит с задержкой в связи с внутренней задержкой, пожалуйста, подождите.")
        response = await ai_generate(message.text)
        response = sanitize_text(response)


        if thinking_msg:
            try:
                await bot.delete_message(
                    chat_id=thinking_msg.chat.id,
                    message_id=thinking_msg.message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение 'думаю': {e}")

        if len(response) <= 4096:
            await message.answer(response, parse_mode="HTML", reply_markup=kb.clearchat)
        else:
            parts = split_message(response)
            total = len(parts)
            for i, part in enumerate(parts, start=1):
                await message.answer(
                f"(Превышен лимит символов. Текст разделен на части {i}/{len(parts)})\n\n{part}", 
                                     parse_mode="HTML", reply_markup=kb.clearchat 
                                     if i == total else None)
    finally:

        active_requests.discard(user_id)

@dp.message(F.photo)
async def analyze_photo(message: Message):
    user_id = message.from_user.id

    if user_id in active_requests:
        await message.reply("⏳ Подожди! Твой предыдущий запрос ещё обрабатывается.")
        return

    active_requests.add(user_id)
    processing_msg = None
    try:
        processing_msg = await message.answer("⌛ Анализирую фото...")

        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        caption = (
            f"📩 <b>Новый запрос с фото</b>\n"
            f"👤 ID: <code>{user_id}</code>\n"
            f"Имя: {message.from_user.full_name}\n"
            f"Username: @{message.from_user.username}" if message.from_user.username else ""
        )
        await bot.send_photo(chat_id=ADMIN_GROUP_ID, 
                             photo=photo.file_id, caption=caption, parse_mode="HTML")

        result = await ai_analyze_image(file_url)
        result = sanitize_text(result)

        if processing_msg:
            try:
                await bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
            except Exception as e:
                print(f"Не удалось удалить сообщение '⌛': {e}")

        await message.reply(f"📷 Анализ изображения:\n\n{result}", parse_mode="HTML")

    finally:

        active_requests.discard(user_id)

async def main():
    dp.include_router(router)
    print("Bot started. Press Ctrl+C to stop.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")