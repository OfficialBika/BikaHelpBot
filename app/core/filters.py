from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.config import settings


class IsOwnerFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return bool(message.from_user and message.from_user.id == settings.owner_id)
