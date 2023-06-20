from aiogram.fsm.state import StatesGroup, State


class StepsChat(StatesGroup):
    ADD_LINK = State()
    DELETE_LINK = State()
    EDIT_PERCENT = State()
    NOT_ADMIN = State()
    SET_SLEEP = State()
    ADD_PROXY = State()
    SET_TRAITS = State()
    EDIT_TRAITS = State()
    ADD_IGNORED = State()
    ADD_PROXY2 = State()
    ADD_RANGE = State()
    EDIT_RANGE = State()
    UPD_RANGE = State()
