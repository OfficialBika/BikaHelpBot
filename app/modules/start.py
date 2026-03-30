from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import settings
from app.keyboards.inline import start_keyboard

router = Router(name="start")


@router.message(CommandStart())
async def start_cmd(message: Message) -> None:
    text = (
        "<b>Rose Bika Bot</b>\n\n"
        "Miss Rose style modular group management bot starter.\n"
        f"Owner ID: <code>{settings.owner_id}</code>"
    )
    if settings.start_img:
        await message.answer_photo(photo=settings.start_img, caption=text, reply_markup=start_keyboard())
        return
    await message.answer(text, reply_markup=start_keyboard())
