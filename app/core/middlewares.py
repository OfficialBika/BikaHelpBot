from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import get_settings
from app.services.redis import is_flooded

settings = get_settings()


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        chat = getattr(event, "chat", None)

        if isinstance(event, CallbackQuery) and event.message:
            chat = event.message.chat

        data["event_user"] = user
        data["event_chat"] = chat
        data["settings"] = settings
        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 8, window: int = 12) -> None:
        self.limit = limit
        self.window = window

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        chat = getattr(event, "chat", None)

        if isinstance(event, CallbackQuery) and event.message:
            chat = event.message.chat

        if user is None or chat is None:
            return await handler(event, data)

        flooded = await is_flooded(
            chat_id=chat.id,
            user_id=user.id,
            limit=self.limit,
            window=self.window,
        )
        if not flooded:
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            try:
                await event.answer("မကြာမကြာမနှိပ်ပါနဲ့။ ခဏစောင့်ပါ။", show_alert=False)
            except Exception:
                pass
            return None

        if isinstance(event, Message):
            return None

        return None
