from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.keyboards.inline import close_keyboard

router = Router(name="help")

HELP_TEXT = (
    "<b>Help Menu</b>\n\n"
    "/start - Start the bot\n"
    "/help - Show help\n"
    "/id - Show chat and user ids\n"
    "/ping - Basic ping test\n"
    "/rules - Show group rules\n"
    "/setrules - Set rules (admin only)\n"
    "/welcome on|off - Toggle welcome\n"
    "/setwelcome text - Set welcome text\n"
    "/warn - Starter warn module\n"
    "/ticket - Starter ticket module"
)


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=close_keyboard())


@router.callback_query(F.data == "help:main")
async def help_cb(query: CallbackQuery) -> None:
    await query.message.edit_text(HELP_TEXT, reply_markup=close_keyboard())
    await query.answer()


@router.callback_query(F.data == "close")
async def close_cb(query: CallbackQuery) -> None:
    await query.message.delete()
    await query.answer()
