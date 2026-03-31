from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import get_settings
from app.core.permissions import is_user_admin
from app.services.mongo import get_chat_setting, set_chat_setting
from app.services.telethon_client import is_user_in_chat
from app.utils.parser import remove_command

router = Router()
settings = get_settings()


def join_keyboard(channel_username: str) -> InlineKeyboardMarkup:
    channel_link = channel_username if channel_username.startswith("https://") else f"https://t.me/{channel_username.lstrip('@')}"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📢 Join Channel", url=channel_link)]])


@router.message(Command("forcejoin"))
async def forcejoin_cmd(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    if message.chat.type not in {"group", "supergroup"}:
        await message.reply("ဒီ command ကို group ထဲမှာသာသုံးပါ။")
        return
    if not await is_user_admin(message.bot, message.chat.id, user.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    arg = remove_command(message.text).strip()
    if not arg:
        current = await get_chat_setting(message.chat.id, "force_join_channel", settings.FORCE_JOIN_CHANNEL)
        await message.reply(
            "အသုံးပြုပုံ:\n<code>/forcejoin @channelusername</code>\n<code>/forcejoin off</code>\n\n"
            f"Current: <code>{current or 'not set'}</code>"
        )
        return

    if arg.lower() == "off":
        await set_chat_setting(message.chat.id, "force_join_enabled", False)
        await set_chat_setting(message.chat.id, "force_join_channel", "")
        await message.reply("Force join ကို ပိတ်ပြီးပါပြီ ✅")
        return

    await set_chat_setting(message.chat.id, "force_join_enabled", True)
    await set_chat_setting(message.chat.id, "force_join_channel", arg)
    await message.reply(f"Force join channel ကို <code>{arg}</code> အဖြစ်သိမ်းပြီးပါပြီ ✅")


@router.message()
async def forcejoin_gate(message: Message) -> None:
    if message.chat.type not in {"group", "supergroup"}:
        return
    if not message.from_user or message.from_user.is_bot:
        return

    enabled = await get_chat_setting(message.chat.id, "force_join_enabled", False)
    if not enabled:
        return

    channel = await get_chat_setting(message.chat.id, "force_join_channel", settings.FORCE_JOIN_CHANNEL)
    if not channel:
        return

    try:
        joined = await is_user_in_chat(channel, message.from_user.id)
    except Exception:
        joined = False

    if joined:
        return

    try:
        await message.delete()
    except Exception:
        pass

    await message.answer("ဒီ group မှာ message ပို့မယ်ဆို အရင် channel join လုပ်ပါ။", reply_markup=join_keyboard(channel))
