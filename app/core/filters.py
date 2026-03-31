from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.config import get_settings
from app.services.mongo import is_support_admin

settings = get_settings()


class IsOwnerFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = getattr(event, "from_user", None)
        if user is None:
            return False
        return bool(settings.OWNER_ID) and user.id == settings.OWNER_ID


class IsSupportOrOwnerFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = getattr(event, "from_user", None)
        if user is None:
            return False

        if bool(settings.OWNER_ID) and user.id == settings.OWNER_ID:
            return True

        return await is_support_admin(user.id)


class IsPrivateFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        chat = _extract_chat(event)
        if chat is None:
            return False
        return chat.type == "private"


class IsGroupFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        chat = _extract_chat(event)
        if chat is None:
            return False
        return chat.type in {"group", "supergroup"}


class HasTextFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return bool(message.text and message.text.strip())


def _extract_chat(event: Any):
    if isinstance(event, CallbackQuery):
        return event.message.chat if event.message else None
    return getattr(event, "chat", None)
