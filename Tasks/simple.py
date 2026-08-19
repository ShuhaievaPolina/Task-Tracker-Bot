from aiogram.fsm.state import State, StatesGroup

class Task(StatesGroup):
    task_name = State()
    hours = State()
    minutes = State()
    time_zone = State()
    task_type = State()
    days_of_week = State()
