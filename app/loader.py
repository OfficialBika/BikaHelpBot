from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.core.middlewares import UserContextMiddleware
from app.modules import ALL_ROUTERS


def create_bot() -> Bot:
    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.message.middleware(UserContextMiddleware())
    for router in ALL_ROUTERS:
        dp.include_router(router)
    return dp
