from aiogram.fsm.state import State, StatesGroup

class DeleteTask(StatesGroup):
    name = State()
