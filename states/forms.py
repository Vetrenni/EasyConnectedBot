from aiogram.fsm.state import State, StatesGroup


class ReportForm(StatesGroup):
    streamer_id = State()
    hours = State()
    amount = State()


class SettingsForm(StatesGroup):
    payout_method = State()
    requisites = State()
    country = State()
    bank = State()
    add_user = State()
    give_admin = State()
    make_streamer = State()


class ChatForm(StatesGroup):
    waiting_for_initial_message = State()
    selecting_chat = State()
    waiting_for_message = State()