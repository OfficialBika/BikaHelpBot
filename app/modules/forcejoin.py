from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings

router = Router(name="forcejoin")


@router.message(Command("forcejoin"))
async def forcejoin_cmd(message: Message) -> None:
    if settings.channel_username:
        await message.answer(f"Force-join target: @{settings.channel_username.lstrip('@')}")
    else:
        await message.answer("Set CHANNEL_USERNAME in .env to use force-join.")
