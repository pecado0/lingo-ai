import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

import backend.db as db
import backend.auth as auth

import tg_bot.tg_keyboards as tgk
from tg_bot.states import Authorization
from tg_bot.utils import get_item

router = Router()

@router.message(Command("auth"))
@router.callback_query(F.data == "auth_start")
async def auth_enter(event: Message | CallbackQuery, state: FSMContext):
    if isinstance(event, CallbackQuery):
        await event.answer()
        message = event.message
    else:
        message = event

    await message.answer(
        "🔑 <b>Пожалуйста, введите ваш email для входа:</b>", 
        reply_markup=tgk.get_cancel_ikb(), parse_mode="HTML"
        )
    await state.set_state(Authorization.passing_login)

@router.message(Authorization.passing_login)
async def auth_login(message: Message, state: FSMContext):
    email = get_item(message=message, entity="email")
    if not email:
        await message.answer(
            "Упс, похоже на опечатку 🧐 Пожалуйста, проверьте формат email и попробуйте еще раз:"
            )
        return None
    
    try:
        db_user_data = db.check_user(email=email)
    except Exception as e:
        await message.answer(
            "Сервер временно недоступен 🛠 Пожалуйста, попробуйте чуть позже."
        )
        logging.error(e)
        return None
    
    if not db_user_data:
        await message.answer(
            "Аккаунт с таким email не найден 🤷‍♂️\n\nПожалуйста, проверьте адрес или перейдите к регистрации."
            )
        return None

    pw_hash = db_user_data["hash_password"]
    user_id = db_user_data["id"]
    await state.update_data(email=email, pw_hash=pw_hash, user_id=user_id)

    await message.answer(
        "Отлично! ✅ Теперь введите ваш пароль:",
        reply_markup=tgk.get_step_ikb(back_callback="back_to_auth_email")
    )
    await state.set_state(Authorization.passing_password)

@router.callback_query(StateFilter(Authorization.passing_password), F.data == "back_to_auth_email")
async def back_to_auth_email(call: CallbackQuery, state: FSMContext):
    await state.set_state(Authorization.passing_login)
    await call.message.edit_text(
        "🔑 <b>Пожалуйста, введите ваш email для входа:</b>", 
        reply_markup=tgk.get_step_ikb(),
        parse_mode="HTML"
    )
    await call.answer()

@router.message(Authorization.passing_password)
async def auth_password(message: Message, state: FSMContext):
    password = get_item(message=message, entity="password")
    if not password:
        await message.answer(
            "Пароль не соответствует требованиям безопасности 🛡 Попробуйте еще раз:"
        )
        return None
    
    user_data = await state.get_data()
    pw_hash = user_data["pw_hash"]
    if not auth.verify_password(plain_password=password, hashed_password=pw_hash):
        await message.answer(
            "Неверный пароль 🚫 Пожалуйста, попробуйте еще раз:"
        )
        return None

    await message.answer(
        "Успешная авторизация! 🎉\n\nГлавное меню открыто. Выберите нужный инструмент ниже 👇"
    )
    user_id = user_data["user_id"]
    token = auth.generate_token(user_id=user_id)

    await state.clear()