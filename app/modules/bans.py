from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="bans")


@router.message(Command("ban"))
async def ban_cmd(message: Message) -> None:
    await message.answer("Bans module starter is ready.")
