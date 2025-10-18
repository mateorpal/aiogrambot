from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram import F

router = Router()

@router.message()
async def handle_unknown(message: Message):
    if message.sticker:
        await message.reply("😅 Стикеры я пока не понимаю, напиши текстом. ")
    elif message.video:
        await message.reply("🎥 Видео обработать не могу, нужен текстовый запрос.")
    elif message.document:
        await message.reply("📄 Файлы я не читаю напрямую, пиши текстом.")
    elif "http" in (message.text or ""):
        await message.reply("🔗 Я вижу ссылку, но лучше напиши текстом, что именно нужно.")
    else:
        await message.reply(
            "🤔 Я обрабатываю только текстовые запросы. Попробуй написать словами.")

@router.callback_query(F.data == 'textawait')
async def textawait(callback: CallbackQuery):
    await callback.answer('Модель текстовых запросов')
    await callback.message.reply(
        'Вы выбрали модель текстовых запросов... Я в ожидании Вашего вопроса!')

@router.callback_query(F.data == 'photoawait')
async def textawait(callback: CallbackQuery):
    await callback.answer('Модель анализа изображений')
    await callback.message.reply(
        'Вы выбрали модель анализа изображений... Я в ожидании Вашего изображения!')