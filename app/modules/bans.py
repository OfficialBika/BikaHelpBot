from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import ChatPermissions, Message

from app.core.permissions import extract_target_user_id, is_user_admin
from app.utils.formatters import hcode

router = Router()


@router.message(Command("ban"))
async def ban_cmd(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    if message.chat.type not in {"group", "supergroup"}:
        await message.reply("ဒီ command ကို group ထဲမှာသာသုံးပါ။")
        return
    if not await is_user_admin(message.bot, message.chat.id, user.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return
    target_id = await extract_target_user_id(message)
    if not target_id:
        await message.reply("reply လုပ်ပြီး <code>/ban</code> သုံးပါ။")
        return
    try:
        await message.bot.ban_chat_member(message.chat.id, target_id)
        await message.reply(f"User {hcode(str(target_id))} ကို ban လုပ်ပြီးပါပြီ ✅")
    except Exception as exc:
        await message.reply(f"Ban မလုပ်နိုင်ပါ: <code>{exc}</code>")


@router.message(Command("unban"))
async def unban_cmd(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    if message.chat.type not in {"group", "supergroup"}:
        await message.reply("ဒီ command ကို group ထဲမှာသာသုံးပါ။")
        return
    if not await is_user_admin(message.bot, message.chat.id, user.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return
    target_id = await extract_target_user_id(message)
    if not target_id:
        await message.reply("user id နဲ့ <code>/unban 12345</code> သို့ reply လုပ်ပြီးသုံးပါ။")
        return
    try:
        await message.bot.unban_chat_member(message.chat.id, target_id, only_if_banned=True)
        await message.reply(f"User {hcode(str(target_id))} ကို unban လုပ်ပြီးပါပြီ ✅")
    except Exception as exc:
        await message.reply(f"Unban မလုပ်နိုင်ပါ: <code>{exc}</code>")


@router.message(Command("mute"))
async def mute_cmd(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    if message.chat.type not in {"group", "supergroup"}:
        await message.reply("ဒီ command ကို group ထဲမှာသာသုံးပါ။")
        return
    if not await is_user_admin(message.bot, message.chat.id, user.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return
    target_id = await extract_target_user_id(message)
    if not target_id:
        await message.reply("reply လုပ်ပြီး <code>/mute</code> သုံးပါ။")
        return
    try:
        await message.bot.restrict_chat_member(
            message.chat.id,
            target_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
            ),
        )
        await message.reply(f"User {hcode(str(target_id))} ကို mute လုပ်ပြီးပါပြီ ✅")
    except Exception as exc:
        await message.reply(f"Mute မလုပ်နိုင်ပါ: <code>{exc}</code>")


@router.message(Command("unmute"))
async def unmute_cmd(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    if message.chat.type not in {"group", "supergroup"}:
        await message.reply("ဒီ command ကို group ထဲမှာသာသုံးပါ။")
        return
    if not await is_user_admin(message.bot, message.chat.id, user.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return
    target_id = await extract_target_user_id(message)
    if not target_id:
        await message.reply("reply လုပ်ပြီး <code>/unmute</code> သုံးပါ။")
        return
    try:
        await message.bot.restrict_chat_member(
            message.chat.id,
            target_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False,
            ),
        )
        await message.reply(f"User {hcode(str(target_id))} ကို unmute လုပ်ပြီးပါပြီ ✅")
    except Exception as exc:
        await message.reply(f"Unmute မလုပ်နိုင်ပါ: <code>{exc}</code>")
