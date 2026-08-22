from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

import tg_bot.tg_keyboards as tgk

router = Router()

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

import tg_bot.tg_keyboards as tgk

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, is_auth: bool):
    user_name = message.from_user.first_name
    
    if is_auth:
        # --- Сценарий для АВТОРИЗОВАННОГО пользователя ---
        text = (
            f"С возвращением, <b>{user_name}</b>! 🚀\n\n"
            f"Главное меню открыто. Выберите нужный инструмент ниже 👇"
        )
        await message.answer(text, reply_markup=tgk.get_main_menu_ikb(), parse_mode="HTML")
    else:
        # --- Сценарий для ГОСТЯ ---
        text = (
            f"👋 Добро пожаловать, <b>{user_name}</b>! Я — ваш бот-помощник.\n\n"
            f"Чтобы получить доступ к функциям (например, Переводчику), "
            f"пожалуйста, войдите в систему или создайте аккаунт."
        )
        await message.answer(text, reply_markup=tgk.get_auth_choice_ikb(), parse_mode="HTML")

@router.callback_query(StateFilter("*"), F.data == "cancel_action")
async def cancel_callback(call: CallbackQuery, state: FSMContext, is_auth: bool):
    await state.clear()
    
    # Возвращаем пользователя в нужное меню в зависимости от его статуса
    if is_auth:
        text = "Действие отменено. Главное меню: 👇"
        reply_markup = tgk.get_main_menu_ikb()
    else:
        text = "Действие отменено. Выберите действие: 👇"
        reply_markup = tgk.get_auth_choice_ikb()
        
    await call.message.edit_text(text, reply_markup=reply_markup)
    await call.answer("Отменено")