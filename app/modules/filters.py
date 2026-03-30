from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="filters")


@router.message(Command("filter"))
async def filter_cmd(message: Message) -> None:
    await message.answer("Filters module starter is ready.")
