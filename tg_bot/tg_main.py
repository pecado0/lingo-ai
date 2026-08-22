from tg_bot import tg_proxy
from tg_bot.bot_handlers import h_common, h_registration, h_authorization, h_translate
from tg_bot.middlewares import LoadUserMiddleware, GuestOnlyMiddleware, AuthOnlyMiddleware

import asyncio
import os
import logging
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommandScopeDefault

"""
todo: разбить этот файл на мейн и хендлеры (для этого сделать роутер), дописать клавиатуру, авторизацию. Переписать хендлеры более компактно, обработку исключений вынести в мейн
"""
# Чтение файлов локального окружения 
load_dotenv()

BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TG_BOT_TOKEN не найден в окружении!")

# ==========================================
# ЗАПУСК БОТА (ДЛЯ ЛОКАЛЬНОГО ТЕСТИРОВАНИЯ)
# ==========================================

async def main():
    logging.basicConfig(level=logging.INFO)

    session = tg_proxy.SystemProxySession()
    bot = Bot(token = BOT_TOKEN, session = session)
    dp = Dispatcher()

    dp.update.outer_middleware(LoadUserMiddleware())

    h_authorization.router.message.middleware(GuestOnlyMiddleware())
    h_authorization.router.callback_query.middleware(GuestOnlyMiddleware())

    h_registration.router.message.middleware(GuestOnlyMiddleware())
    h_registration.router.callback_query.middleware(GuestOnlyMiddleware())
    
    h_translate.router.message.middleware(AuthOnlyMiddleware())
    h_translate.router.callback_query.middleware(AuthOnlyMiddleware())
    

    dp.include_routers(
        h_common.router,
        h_registration.router,
        h_authorization.router, 
        h_translate.router
    )

    await bot.delete_webhook(drop_pending_updates=True)

    await bot.set_my_description(
    "👋 Привет! Я — твой умный бот-переводчик.\n\n"
    "Нажми кнопку «Запустить» внизу, чтобы войти в систему и начать работу!",
    language_code="ru" 
    )

    from aiogram.types import BotCommand
    await bot.set_my_commands(
        [BotCommand(command="start", description="Перезапустить бота / Главное меню")],
        scope=BotCommandScopeDefault()
    )

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        

if __name__ == "__main__":
    try:
        print("Бот запущен локально! Нажми Ctrl+C для остановки.")
        asyncio.run(main())
    except KeyboardInterrupt: 
        print("Бот остановлен")