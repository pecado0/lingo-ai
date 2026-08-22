import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

import backend.db as db
import tg_bot.tg_db as tg_db
import backend.auth as auth

import tg_bot.tg_keyboards as tgk
from tg_bot.states import Register
from tg_bot.utils import get_item

router = Router()

@router.message(Command("reg"))
@router.callback_query(F.data == "reg_start")
async def reg_enter(event: Message | CallbackQuery, state: FSMContext):
    if isinstance(event, CallbackQuery):
        await event.answer()
        message = event.message
    else:
        message = event

    await message.answer(
        "📝 <b>Давайте создадим аккаунт! Пожалуйста, введите ваш email:</b>", 
        reply_markup=tgk.get_cancel_ikb(), 
        parse_mode="HTML")
    await state.set_state(Register.passing_login)

@router.message(Register.passing_login)
async def reg_login(message: Message, state: FSMContext):
    email = get_item(message=message, entity="email")
    if not email:
        await message.answer(
            "Упс, похоже на опечатку 🧐 Пожалуйста, проверьте формат email и попробуйте еще раз:"
            )
        return None

    if db.check_user(email=email):
        await message.answer(
            "Аккаунт с таким email уже существует 📂\n\nПожалуйста, используйте другой адрес или войдите в систему."
        )
        return None
    
    await state.update_data(email=email)
    await message.answer(
        "Супер! ✅ Теперь придумайте надежный пароль (минимум 8 символов):",
        reply_markup=tgk.get_step_ikb(back_callback="back_to_reg_email")
    )
    await state.set_state(Register.passing_password)

@router.callback_query(StateFilter(Register.passing_password), F.data == "back_to_reg_email")
async def back_to_reg_email(call: CallbackQuery, state: FSMContext):
    await state.set_state(Register.passing_login)
    await call.message.edit_text(
        "📝 <b>Пожалуйста, введите ваш email для регистрации:</b>", 
        reply_markup=tgk.get_step_ikb(),
        parse_mode="HTML"
    )
    await call.answer()

@router.message(Register.passing_password)
async def reg_password(message: Message, state: FSMContext):
    password = get_item(message=message, entity="password")
    if not password:
        await message.answer(
            "Пароль слишком простой или содержит недопустимые символы 🛡 Попробуйте придумать другой:"
        )
        return None

    await state.update_data(password=password)
    msg = await message.answer("⏳ Создаем ваш аккаунт, буквально пару секунд...")
    
    user_data = await state.get_data()
    hashed_password = auth.hash_password(password=user_data["password"])
    email = user_data["email"]
    telegram_id = str(message.from_user.id)

    try:
        user_id = db.create_user(email=email, password_hash=hashed_password)
        tg_db.link_tg_user(telegram_id=telegram_id, user_id=user_id)
        await msg.delete()
        await message.answer(
            "🎉 <b>Регистрация успешно завершена! Добро пожаловать!</b>\n\nВыберите нужный инструмент ниже 👇",
            reply_markup=tgk.get_main_menu_ikb(),
            parse_mode="HTML"
        )
    except Exception as e:
        await msg.delete()
        await message.answer("Что-то пошло не так при создании аккаунта 🛠 Пожалуйста, попробуйте еще раз позже.")
        logging.error(f"Ошибка при создании пользователя: {e}")
    finally:
        await state.clear()