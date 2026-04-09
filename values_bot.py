import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import requests
from dotenv import load_dotenv
import json

load_dotenv()

bot = Bot(os.getenv("bot_key"))
value_key = os.getenv("value_key")
dp = Dispatcher()

user_data = {}

@dp.message(Command("start"))

async def start(message: types.Message):

    await message.answer(f"hi {message.from_user.username} , in this bot u can convert almost all currencies , enter amount of currency : ")

@dp.message(F.text)

async def process_amount(message: types.Message):

    try:
        val = float(message.text.strip())
        user_data[message.from_user.id] = val

        builder = InlineKeyboardBuilder()

        builder.add(types.InlineKeyboardButton(text='USD', callback_data='usd'))
        builder.add(types.InlineKeyboardButton(text='EUR', callback_data='eur'))
        builder.add(types.InlineKeyboardButton(text='UAH', callback_data='uah'))
        builder.add(types.InlineKeyboardButton(text='RUB', callback_data='rub'))
        builder.adjust(2)

        await message.answer(f"your amount : {message.text} , choose currency pair to convert",reply_markup=builder.as_markup())

    except Exception:

        await message.answer("this is not number")

@dp.callback_query()

async def callback_handler(callback: types.CallbackQuery):

    res = requests.get(f"https://v6.exchangerate-api.com/v6/{value_key}/latest/{callback.data.upper()}")
    res_data = res.json()

    amount = user_data.get(callback.from_user.id)

    if res_data["result"] == "success":

        rates = res_data["conversion_rates"]

        await callback.message.edit_text(f"IN USD : {amount*rates['USD']}\nIN EUR : {amount*rates['EUR']}\nIN UAH : {amount*rates['UAH']}\n IN RUB : {amount*rates['RUB']}")


async def main():

    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())

