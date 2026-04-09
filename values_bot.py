import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import requests
from dotenv import load_dotenv
import json
import sqlite3

load_dotenv()

bot = Bot(os.getenv("bot_key"))
value_key = os.getenv("value_key")
dp = Dispatcher()

user_data = {}

user_in_registration = []

conn = sqlite3.connect('values.sql')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS values_us (id int auto_increment primary key, user_id varchar(50), currency varchar(50))')
conn.commit()
cur.close()
conn.close()

line = "-"*10

@dp.message(Command("reset"))

async def reset(message):

    conn = sqlite3.connect('values.sql')
    cur = conn.cursor()

    cur.execute('DELETE FROM values_us WHERE user_id = ?', (str(message.from_user.id),))
    conn.commit()

    cur.close()

    conn.close()


    markup = types.ReplyKeyboardRemove()

    await message.answer("data reset")

@dp.message(Command("start"))

async def start(message: types.Message):

    user_in_registration.append(message.from_user.id)

    conn = sqlite3.connect('values.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS values_us (id int auto_increment primary key, user_id varchar(50), currency varchar(50))')
    conn.commit()
    cur.execute('SELECT currency FROM values_us WHERE user_id = ?',(message.from_user.id,))

    user_data = cur.fetchone()


    if user_data:

        saved_currency = user_data[0]
        await message.answer(f"you are registered ! your currency : {saved_currency.upper()}. \n")


        if message.from_user.id in user_in_registration:
            user_in_registration.remove(message.from_user.id)

        cur.close()
        conn.close()

    else:

        if message.from_user.id not in user_in_registration:
            user_in_registration.append(message.from_user.id)

        await message.answer(f"hi , {message.from_user.username} , to use this bot , enter your currency :")


@dp.message(F.text)

async def process_amount(message: types.Message):

    user_id = message.from_user.id
    text = message.text.strip().upper()

    if user_id in user_in_registration:
        res = requests.get(f"https://v6.exchangerate-api.com/v6/{value_key}/latest/{text}")
        if res.status_code == 200:
            conn = sqlite3.connect('values.sql')
            cur = conn.cursor()
            cur.execute('INSERT INTO values_us (user_id, currency) VALUES (?, ?)', (str(user_id), text))
            conn.commit()
            conn.close()
            user_in_registration.remove(user_id)
            await message.answer(f"you have been registered ! your currency is {text} .")
        else:
            await message.answer("wrong currency ! try again \n(for example : USD)")
        return

    conn = sqlite3.connect('values.sql')
    cur = conn.cursor()
    cur.execute('SELECT currency FROM values_us WHERE user_id = ?', (str(user_id),))
    user_db_data = cur.fetchone()
    cur.close()
    conn.close()

    if not user_db_data:
        await message.answer("register firstly ! type /start")
        return

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

    base_curr = callback.data.upper()

    amount = user_data.get(callback.from_user.id)

    if res_data["result"] == "success":

        rates = res_data["conversion_rates"]

        text = f"{amount} {base_curr}\n{line}\n"

        target_currencies = ['USD', 'EUR', 'UAH', 'RUB']

        for curr in target_currencies:
            if curr != base_curr:
                res_val = round(amount * rates[curr], 2)
                text += f" {curr}: {res_val}\n{line}\n"

        await callback.message.edit_text(text,  parse_mode="Markdown")

    await callback.answer()

        #await callback.message.edit_text(f"IN USD : {amount*rates['USD']}\nIN EUR : {amount*rates['EUR']}\nIN UAH : {amount*rates['UAH']}\n IN RUB : {amount*rates['RUB']}")


async def main():

    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())

