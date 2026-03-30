from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="tickets")


@router.message(Command("ticket"))
async def ticket_cmd(message: Message) -> None:
    await message.answer("Tickets module starter is ready.")
