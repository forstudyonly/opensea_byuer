from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
from core.utils.states import StepsChat
from core.database.base import bd_get_links, bd_get_percent, bd_check_user,  bd_get_all_ignored
from core.settings import settings

group_id = settings.chat.chat_id

help_info = '''
<b>OpenSea</b>:
/help - Возвращает этот же пост

<b>Collections</b>:
/all_links - Выводит все коллекции
/add_links - Добавляет коллекции
/delete_links -  Удаляет коллекции
/edit_range - Изменяет диапазон цены коллекции

<b>Settings</b>:
/edit_percent - Изменяет процент для проверки разницы цены NFT от Top Bid цены, учавствует в формуле:
price_nft &lt;= top_bid * (1 - <b>percent</b>)
/gas - Gas?


/add_ignored - Исключает коллекцию на 24 часа
/get_ignored - Отображает список коллекций которые игнорируем
'''


async def get_ignored(message: types.Message, bot: Bot, state: FSMContext):
    links = bd_get_all_ignored()
    if links == "":
        await message.answer(f"Таких нет")
        return ""
    str_links = "Все игнорирующиеся коллекции:"
    for link in links:
        str_links += "\n" + link[0]
    await message.answer(f"{str_links}")


async def add_ignored(message: types.Message, bot: Bot, state: FSMContext):
    await message.answer(f"Пришлите ссылку на коллекцию (или название) которую нужно игнорировать следующие 24 часа")
    await state.set_state(StepsChat.ADD_IGNORED)


async def get_start(message: types.Message, bot: Bot, state: FSMContext):
    if bd_check_user(message.from_user.id) == "":
        await state.set_state(StepsChat.NOT_ADMIN)
        await message.answer(f"У вас нет доступа к боту.")
        return ""
    await state.clear()
    await message.answer(f"{help_info}", parse_mode="HTML")


async def not_admin(message: types.Message, bot: Bot, state: FSMContext):
    await message.answer(f"У вас нет доступа к боту.")


async def get_help(message: types.Message, bot: Bot, state: FSMContext):
    await message.answer(f"{help_info}", parse_mode="HTML")
    await state.clear()


async def add_links(message: types.Message, bot: Bot, state: FSMContext):
    await message.answer(f"Пришлите ссылки коллекций или их название (присылать по одной)")
    await state.set_state(StepsChat.ADD_LINK)


async def del_links(message: types.Message, bot: Bot, state: FSMContext):
    await message.answer(f"Пришлите ссылки коллекций или названия которые хотите удалить (присылать по одной)")
    await state.set_state(StepsChat.DELETE_LINK)


async def edit_ranges(message: types.Message, bot: Bot, state: FSMContext):
    await message.answer(f"Пришлите ссылкe коллекции или название в которой нужно изменить диапазон (присылать по одной)")
    await state.set_state(StepsChat.EDIT_RANGE)


async def get_links(message: types.Message, bot: Bot, state: FSMContext):
    links = bd_get_links()
    if links == "":
        await message.answer(f"Ссылок нет")
        return ""
    str_links = "Все ссылки:"
    for link in links:
        str_links += "\n" + link[0] + " | "
        str_links += f"{link[1]} - {link[2]} | "
        str_links += "Игнорируется\n" if link[3] == 1 else "Не игнорируется\n"
    await message.answer(f"{str_links}")
    await state.clear()


async def edit_percent(message: types.Message, bot: Bot, state: FSMContext):
    adj = bd_get_percent()
    if adj == "":
        await message.answer(f"Сейчас ничего не установлено")
        return ""
    await message.answer(f"Сейчас разница составляет: {adj}\n Если хотите изменить введите новое значение, если нет введите stop или /help")
    await state.set_state(StepsChat.EDIT_PERCENT)


async def random_mess(message: types.Message, bot: Bot):
    await bot.send_message(chat_id=1354639096, text=f"{message.text}")
    print(message)


async def auth_mess(mess, bot: Bot):
    await bot.send_message(chat_id=1354639096, text=f"{mess}")
    print(mess)


async def find_coll(bot: Bot, info):
    await bot.send_message(chat_id=group_id, text=f"Collection: <b>{info[0]}</b>\nFloor price: <b>{info[1]}</b>\nTop Bid: <b>{info[2]}</b>\nUrl: <b>{info[3]}</b>\n<b>Difference: {info[4]}</b>", parse_mode='HTML')


async def find_buy_nft(bot: Bot, info):
    if info[-1]:
        await bot.send_message(chat_id=group_id, text=f"Успешно приобрели NFT!\nCollection:<b>{info[0]}</b>\nPrice: <b>{info[1]}</b>\nTop bid: <b>{info[2]}</b>\n<b>Tx hash: {info[3]}</b>", parse_mode='HTML')
    else:
        await bot.send_message(chat_id=group_id,
                               text=f"Не получилось купить NFT!\nCollection:<b>{info[0]}</b>\nPrice: <b>{info[1]}</b>\nTop bid: <b>{info[2]}</b>",
                               parse_mode='HTML')

