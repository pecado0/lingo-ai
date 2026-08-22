from aiogram.fsm.state import StatesGroup, State

class Register(StatesGroup):
    passing_login = State()
    passing_password = State()

class Authorization(StatesGroup):
    passing_login = State()
    passing_password = State()

class Translate(StatesGroup):
    passing_word = State()
    passing_context = State()
    showing_result = State()