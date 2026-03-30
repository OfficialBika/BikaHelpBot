from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="misc")


@router.message(Command("ping"))
async def ping_cmd(message: Message) -> None:
    await message.answer("pong")


@router.message(Command("id"))
async def id_cmd(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else 0
    await message.answer(
        f"Chat ID: <code>{message.chat.id}</code>\nUser ID: <code>{user_id}</code>"
    )
