from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="blacklists")


@router.message(Command("blacklist"))
async def blacklist_cmd(message: Message) -> None:
    await message.answer("Blacklists module starter is ready.")
