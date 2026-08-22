from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from tg_bot import tg_db

class LoadUserMiddleware(BaseMiddleware):
    async def __call__(self, 
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable], 
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем объект User конкретного пользователя, вызвавшего событие
        user = data.get("event_from_user")
        is_auth = False

        # Ищем пользователя в БД, если не находим, возвращается False
        user_id_db = tg_db.get_tg_user(telegram_id = str(user.id))
        if user_id_db:
            is_auth = True

        data["is_auth"] = is_auth

        return await handler(event, data)

class GuestOnlyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Если пользователь УЖЕ авторизован — блокируем доступ
        if data.get("is_auth"):
            if isinstance(event, Message):
                await event.answer("Вы уже вошли в аккаунт! Повторная авторизация не требуется.")
            elif isinstance(event, CallbackQuery):
                await event.answer("Вы уже авторизованы!", show_alert=True)
            return None  # Прерываем цепочку, хэндлер не вызывается

        return await handler(event, data)

class AuthOnlyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Если пользователь НЕ авторизован — блокируем доступ
        if not data.get("is_auth"):
            if isinstance(event, Message):
                await event.answer("Для использования бота необходимо войти в аккаунт.")
            elif isinstance(event, CallbackQuery):
                await event.answer("Сначала войдите в аккаунт!", show_alert=True)
            return None  # Прерываем цепочку

        return await handler(event, data)
