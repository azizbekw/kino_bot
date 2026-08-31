from aiogram.fsm.state import State, StatesGroup

class AddMovie(StatesGroup):
    waiting_for_code = State()
    waiting_for_media = State()
    confirm_save = State()

class DeleteMovie(StatesGroup):
    waiting_for_code = State()

class AddChannel(StatesGroup):
    waiting_for_name = State()
    waiting_for_url = State()
    waiting_for_chat_id = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()
