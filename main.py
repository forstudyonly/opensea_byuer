from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.filters import Command
import asyncio

from core.handlers.basic import get_start, edit_ranges, get_help, add_links, get_links, del_links, edit_percent, random_mess, not_admin, add_ignored, get_ignored, auth_mess
from core.handlers.fsm import add_link, del_link, ed_percent, set_ignored, add_range, edit_range, update_range
from core.utils.states import StepsChat
from core.settings import settings

token = settings.bots.bot_token


async def start():
    bot = Bot(token=token)

    dp = Dispatcher()

    dp.message.register(get_start, Command(commands="start"))
    dp.message.register(not_admin, StepsChat.NOT_ADMIN)
    dp.message.register(get_help, Command(commands="help"))
    dp.message.register(add_links, Command(commands="add_links"))
    dp.message.register(del_links, Command(commands="delete_links"))
    dp.message.register(get_links, Command(commands="all_links"))
    dp.message.register(edit_percent, Command(commands="edit_percent"))
    dp.message.register(edit_ranges, Command(commands="edit_range"))
    dp.message.register(add_ignored, Command(commands="add_ignored"))
    dp.message.register(get_ignored, Command(commands="get_ignored"))
    dp.message.register(set_ignored, StepsChat.ADD_IGNORED)
    dp.message.register(ed_percent, StepsChat.EDIT_PERCENT)
    dp.message.register(add_link, StepsChat.ADD_LINK)
    dp.message.register(del_link, StepsChat.DELETE_LINK)
    dp.message.register(add_range, StepsChat.ADD_RANGE)
    dp.message.register(edit_range, StepsChat.EDIT_RANGE)
    dp.message.register(update_range, StepsChat.UPD_RANGE)
    dp.message.register(random_mess)

    try:
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(start())
