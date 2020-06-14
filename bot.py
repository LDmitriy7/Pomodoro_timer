import os
import asyncio
import config
import re
from time import time as TIME, sleep
from aiogram import Bot, Dispatcher, executor, types
from SQLighter import SQLighter
from math import ceil

# инициализируем бота
token = os.environ.get('BOT_TOKEN')
bot = Bot(token=token)
dp = Dispatcher(bot)

# инициализируем соединение с БД
db = SQLighter('users.db')

keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.row('W', 'R', 'W2', 'R2')
keyboard.row('T', 'P', 'P2', 'S', 'S2', 'D')
keyboard.row('/set_timers', '/get_timers')


# стартовая инструкция
@dp.message_handler(commands=['start', 'help'])
async def set_time(message: types.Message):
    await message.answer(config.start_text, disable_web_page_preview=True, reply_markup=keyboard)


# открыть клавиатуру
@dp.message_handler(commands=['keyboard'])
async def set_time(message: types.Message):
    await message.answer("Открываю клавиатуру", reply_markup=keyboard)


# Установка стандартных таймеров
@dp.message_handler(commands=['set_timers'])
async def set_time(message: types.Message):
    await message.answer("Введите через пробел 4 числа:\nжелаемое время для W, R, W2 и R2 соответственно (в минутах)",
                         reply_markup=types.ForceReply())


# Продолжение
@dp.message_handler(lambda msg: msg.reply_to_message and msg.reply_to_message.text in [
    "Введите через пробел 4 числа:\nжелаемое время для "
    "W, R, W2 и R2 соответственно (в минутах)",
    "Ошибка, введите 4 целых числа в пределах от 1 до 999"])
async def set_time2(message: types.Message):
    text = message.text.split()
    if len(text) == 4:
        if all(map(lambda x: x.isdigit() and int(x) in range(1, 1000), text)):
            db.set_config(message.from_user.id, text[0], text[1], text[2], text[3])
            await message.answer("Новые параметры успешно установлены", reply_markup=keyboard)
        else:
            await message.answer("Ошибка, введите 4 целых числа в пределах от 1 до 999",
                                 reply_markup=types.ForceReply())
    else:
        await message.answer("Ошибка, введите 4 целых числа в пределах от 1 до 999", reply_markup=types.ForceReply())


# Просмотр стандартных таймеров
@dp.message_handler(commands=['get_timers'])
async def get_time(message: types.Message):
    result = db.get_config(message.from_user.id)
    await message.answer(f"Сейчас установлено (минут):\nW={result[0]}, R={result[1]}, W2={result[2]}, R2={result[3]}")


# получение статистики
@dp.message_handler(lambda msg: msg.text.lower().replace('.', '') == 's')
async def get_stats(msg: types.Message):
    if msg.text[-1] == '.':
        sleep(10)
    result = db.get_stats(msg.from_user.id)
    if result:
        await msg.answer(
            f"Сегодня вы:\n-------------------------------------------------\n  "
            f"* Работали {result[2]} мин.\n    (закончено таймеров: {result[0]})\n\n"
            f"  * Отдыхали {result[3]} мин.\n    (закончено таймеров: {result[1]})")
    else:
        await msg.answer("Сегодня еще нет законченных таймеров")


# очистка статистики
@dp.message_handler(lambda msg: msg.text.lower().replace('.', '') == 's2')
async def del_stats(msg: types.Message):
    if msg.text[-1] == '.':
        sleep(10)
    db.update_stats(msg.from_user.id)
    await msg.answer("Статистика сброшена")


# Заведение одного из стандартных таймеров
@dp.message_handler(lambda msg: msg.text.lower().replace('.', '') in ('w', 'r', 'w2', 'r2'))
async def start_timer(msg: types.Message):
    if msg.text[-1] == '.':
        sleep(10)
    text = msg.text.lower().replace('.', '')
    result = db.get_config(msg.from_user.id)
    result = {'w': result[0], 'r': result[1], 'w2': result[2], 'r2': result[3], }
    min_dur = result[text]
    if text in ['w', 'w2']:
        db.set_timer(msg.from_user.id, min_dur, 'w')
        await msg.answer(f"Завожу {min_dur} мин. работы")
    else:
        db.set_timer(msg.from_user.id, min_dur, 'r')
        await msg.answer(f"Завожу {min_dur} мин. отдыха")


# Заведение произвольного таймера
@dp.message_handler(lambda msg: re.fullmatch(r'\d+[w,W,r,R]\.?', msg.text))
async def start_arb_timer(msg: types.Message):
    integer = int(msg.text.replace('.', '')[:-1])
    mode = msg.text.replace('.', '')[-1]
    if msg.text[-1] == '.':
        sleep(10)
    if integer in range(1, 1000):
        if mode in ['w', 'W']:
            db.set_timer(msg.from_user.id, integer, 'w')
            await msg.answer(f"Завожу {integer} мин. работы")
        else:
            db.set_timer(msg.from_user.id, integer, 'r')
            await msg.answer(f"Завожу {integer} мин. отдыха")
    else:
        await msg.answer("Время должно быть в пределах от 1 до 999 минут")


# Удаление текущего таймера
@dp.message_handler(lambda msg: msg.text.lower().replace('.', '') == 'd')
async def del_timer(msg: types.Message):
    if msg.text[-1] == '.':
        sleep(10)
    db.del_timer(msg.from_user.id)
    await msg.answer("Таймер удален")


# Просмотр оставшегося времени текущего таймера
@dp.message_handler(lambda msg: msg.text.lower().replace('.', '') == 't')
async def get_timer(msg: types.Message):
    time = db.get_timer(msg.from_user.id)
    if msg.text[-1] == '.':
        sleep(10)
    if time:
        result = ceil((time - TIME()) / 60)
        if db.get_mode_from_timers_on(msg.from_user.id) in ['w', 'W']:
            await msg.answer(f"Осталось меньше {result} мин. работы")
        else:
            await msg.answer(f"Осталось меньше {result} мин. отдыха")
    else:
        await msg.answer("Нет заведенных таймеров")


# Приостановка таймера
@dp.message_handler(lambda msg: msg.text.lower().replace('.', '') == 'p')
async def pause(msg: types.Message):
    time = db.get_timer(msg.from_user.id)
    if msg.text[-1] == '.':
        sleep(10)
    if time:
        result = ceil((time - TIME()) / 60)
        if db.pause_timer(msg.from_user.id) in ['w', 'W']:
            await msg.answer(f"Таймер приостановлен, оставалось меньше {result} мин. работы")
        else:
            await msg.answer(f"Таймер приостановлен, оставалось меньше {result} мин. отдыха")
    else:
        await msg.answer("Нет заведенных таймеров")


# Возобновение таймера
@dp.message_handler(lambda msg: msg.text.lower().replace('.', '') == 'p2')
async def pause(msg: types.Message):
    duration = db.resume_timer(msg.from_user.id)
    if msg.text[-1] == '.':
        sleep(10)
    if duration:
        min_dur = round(duration / 60)
        if db.get_mode_from_timers_on(msg.from_user.id) in ['w', 'W']:
            await msg.answer(f"Таймер возобновлен, завожу около {min_dur} мин. работы")
        else:
            await msg.answer(f"Таймер возобновлен, завожу около {min_dur} мин. отдыха")
    else:
        await msg.answer("Нет приостановленных таймеров")


@dp.message_handler(lambda msg: True)
async def answer(msg: types.Message):
    time = db.get_timer(msg.from_user.id)
    if msg.text[-1] == '.':
        sleep(10)
    if time:
        result = ceil((time - TIME()) / 60)
        if db.get_mode_from_timers_on(msg.from_user.id) in ['w', 'W']:
            await msg.answer(f"Осталось меньше {result} мин. работы")
        else:
            await msg.answer(f"Осталось меньше {result} мин. отдыха")
    else:
        await msg.answer("Нет заведенных таймеров")


# проверка вышедших таймеров
async def check(wait_for):
    while True:
        await asyncio.sleep(wait_for)
        result = db.check_timers()
        if result:
            user_id, points, mode = result
            db.give_points_and_del_timer(user_id, points, mode)
            if mode in ['w', 'W']:
                await bot.send_message(user_id, f"Время таймера вышло, начислено {points} мин. работы")
            else:
                await bot.send_message(user_id, f"Время таймера вышло, начислено {points} мин. отдыха")

# запускаем лонг-поллинг
if __name__ == '__main__':
    dp.loop.create_task(check(1))
    executor.start_polling(dp, skip_updates=True)
