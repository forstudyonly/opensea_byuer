import time
from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
from core.utils.states import StepsChat
from core.handlers.basic import get_help
from core.database.base import bd_add_ignored, bd_add_link, bd_delete_link, bd_edit_percent, bd_get_range, bd_update_range

dict_names = {}


async def set_ignored(message: types.Message, bot: Bot, state: FSMContext):
    if message.text.strip() == "stop":
        await state.clear()
        await get_help(message, bot, state)
    else:
        if "/" in message.text:
            name = message.text.split("/")[-1].strip()
        else:
            name = message.text.strip()

        time_expired = int(int(time.time()) + 24 * 60 * 60)
        check = bd_add_ignored(name, str(time_expired))
        if check == "suc":
            await message.answer("Игнорируется! можете еще добавить или если добавили всё напишите stop или /help")
        else:
            await message.answer(f"Не получилось игнорировать коллекцию, проверьте есть ли она")


async def add_link(message: types.Message, bot: Bot, state: FSMContext):
    if message.text.strip() == "stop":
        await state.clear()
        await get_help(message, bot, state)
    else:
        if "/" in message.text:
            name = message.text.split("/")[-1]
        else:
            name = message.text.strip()
        dict_names[message.chat.id] = name
        await message.answer("Теперь введите диапазон цен в формате (0.5-1) или напишите stop или /help")
        await state.set_state(StepsChat.ADD_RANGE)


async def add_range(message: types.Message, bot: Bot, state: FSMContext):
    if message.text.strip() == "stop":
        await state.clear()
        await get_help(message, bot, state)
    else:
        if "-" in message.text:
            range = message.text.split("-")
            min_price = range[0].strip()
            max_price = range[1].strip()
            if float(min_price) <= float(max_price):
                pass
            else:
                await message.answer(f"Некорректный диапазон, введите корректный или напишите stop или /help")
                return ""
        else:
            await message.answer(f"Некорректный диапазон, введите корректный или напишите stop или /help")
            return ""

        check = bd_add_link(dict_names[message.chat.id], min_price, max_price)
        if check == "suc":
            await message.answer("Успешно! Пришлите ссылку/название следующей коллекции или напишите stop или /help")
            await state.set_state(StepsChat.ADD_LINK)
        else:
            bd_update_range(dict_names[message.chat.id], min_price, max_price)
            await message.answer(f"Коллекция уже была {check} - обновили ее диапазон.\nПришлите ссылку/название следующей коллекции или напишите stop или /help")
            await state.set_state(StepsChat.ADD_LINK)


async def edit_range(message: types.Message, bot: Bot, state: FSMContext):
    if message.text.strip() == "stop":
        await state.clear()
        await get_help(message, bot, state)
    else:
        if "/" in message.text:
            name = message.text.split("/")[-1].strip()
        else:
            name = message.text.strip()
        check = bd_get_range(name)
        if check:
            dict_names[message.chat.id] = name
            col_info = f"Сейчас установлено:\n{check[0][0]} | {check[0][1]}-{check[0][2]} | {check[0][3]}\n"
            await message.answer(f"{col_info}Теперь введите новый диапазон цен в формате (0.5-1) или напишите stop или /help")
            await state.set_state(StepsChat.UPD_RANGE)
        else:
            await message.answer(f"Такой коллекции нету, попробуйте еще раз")


async def update_range(message: types.Message, bot: Bot, state: FSMContext):
    if message.text.strip() == "stop":
        await state.clear()
        await get_help(message, bot, state)
    else:
        if "-" in message.text:
            range = message.text.split("-")
            min_price = range[0].strip()
            max_price = range[1].strip()
            if float(min_price) <= float(max_price):
                pass
            else:
                await message.answer(f"Некорректный диапазон, введите корректный или напишите stop или /help")
                return ""
        else:
            await message.answer(f"Некорректный диапазон, введите корректный или напишите stop или /help")
            return ""

        check = bd_update_range(dict_names[message.chat.id], min_price, max_price)
        if check == "suc":
            await message.answer("Успешно! Пришлите ссылку/название для изменения диапазона след коллекции или напишите stop или /help")
            await state.set_state(StepsChat.EDIT_RANGE)
        else:
            await message.answer("Ошибка при записи в бд")
            await get_help(message, bot, state)


async def del_link(message: types.Message, bot: Bot, state: FSMContext):
    if message.text.strip() == "stop":
        await get_help(message, bot, state)
    else:
        if "/" in message.text:
            name = message.text.split("/")[-1].strip()
        else:
            name = message.text.strip()
        check = bd_delete_link(name)
        if check == "suc":
            await message.answer("Ссылка Удалена! Если удалили все ссылки напишите stop или /help")
        else:
            await message.answer(f"Ошибка удаления, скорее всего такой ссылки и нету")


async def ed_percent(message: types.Message, bot: Bot, state: FSMContext):
    if message.text.strip() == "stop":
        await get_help(message, bot, state)
    else:
        percent = message.text
        if "," in percent:
            percent = message.text.replace(",", ".")
        check = bd_edit_percent(percent)
        if check == "suc":
            await message.answer(f"Изменено на: {percent}")
            await get_help(message, bot, state)
        else:
            await message.answer(f"Непонятная ошибка в работе с бд")
            await get_help(message, bot, state)