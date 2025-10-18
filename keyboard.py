from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton



firstinfo = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Канал разработчика чат-бота', url='')],
    [InlineKeyboardButton(text='Текстовой запрос', callback_data='textawait'),
    InlineKeyboardButton(text='Анализ изображений', callback_data='photoawait')]
])

clearchat = ReplyKeyboardMarkup(
    keyboard=[

        [KeyboardButton(text="Очистить чат")] 
    ],
    resize_keyboard=True,
    input_field_placeholder="Задайте вопрос..."
)