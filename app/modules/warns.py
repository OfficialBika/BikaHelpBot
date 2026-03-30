from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="warns")


@router.message(Command("warn"))
async def warn_cmd(message: Message) -> None:
    await message.answer("Warns module starter is ready.")
