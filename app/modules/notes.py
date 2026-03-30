from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="notes")


@router.message(Command("save"))
async def save_note(message: Message) -> None:
    await message.answer("Notes module starter is ready. Add Mongo note save logic here.")


@router.message(Command("get"))
async def get_note(message: Message) -> None:
    await message.answer("Notes module starter is ready. Add Mongo note fetch logic here.")
