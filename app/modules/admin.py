from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.permissions import is_user_admin

router = Router(name="admin")


@router.message(Command("admins"))
async def admins_cmd(message: Message) -> None:
    admins = await message.bot.get_chat_administrators(message.chat.id)
    text = "<b>Admins:</b>\n" + "\n".join(
        f"• {admin.user.full_name} (<code>{admin.user.id}</code>)" for admin in admins
    )
    await message.answer(text)


@router.message(Command("broadcast"))
async def broadcast_stub(message: Message) -> None:
    if not await is_user_admin(message):
        await message.answer("Admins only.")
        return
    await message.answer("Broadcast starter is ready. Connect your DB logic here.")
