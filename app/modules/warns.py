from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import ChatPermissions, Message

from app.core.permissions import can_restrict_members, extract_target_user_id, is_user_admin
from app.services.mongo import get_collection, get_warn_settings, set_warn_action, set_warn_limit
from app.utils.formatters import hcode, join_lines
from app.utils.parser import parse_int, remove_command

router = Router()


def warns_collection():
    return get_collection("warns")


async def get_warn_count(chat_id: int, user_id: int) -> int:
    col = warns_collection()
    if col is None:
        return 0
    doc = await col.find_one({"chat_id": chat_id, "user_id": user_id})
    return int(doc.get("count", 0)) if doc else 0


async def reset_warn_count(chat_id: int, user_id: int) -> None:
    col = warns_collection()
    if col is None:
        return
    await col.delete_one({"chat_id": chat_id, "user_id": user_id})


async def apply_warn_action(message: Message, target_id: int, action: str) -> tuple[bool, str]:
    try:
        if action == "ban":
            await message.bot.ban_chat_member(message.chat.id, target_id)
            return True, "ban"
        if action == "mute":
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
            return True, "mute"
        return False, "off"
    except Exception as exc:
        return False, str(exc)


@router.message(Command("warn"))
async def warn_cmd(message: Message) -> None:
    admin = message.from_user
    if not admin:
        return
    if message.chat.type not in {"group", "supergroup"}:
        await message.reply("ဒီ command ကို group ထဲမှာသာသုံးပါ။")
        return
    if not await is_user_admin(message.bot, message.chat.id, admin.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    target_id = await extract_target_user_id(message)
    if not target_id:
        await message.reply("reply လုပ်ပြီး <code>/warn reason</code> သို့ user id နဲ့သုံးပါ။")
        return
    if target_id == admin.id:
        await message.reply("ကိုယ့်ကိုယ်ကို warn မပေးပါနဲ့။")
        return

    col = warns_collection()
    if col is None:
        await message.reply("MongoDB မချိတ်ထားသေးပါ။")
        return

    reason = remove_command(message.text)
    await col.update_one(
        {"chat_id": message.chat.id, "user_id": target_id},
        {"$inc": {"count": 1}, "$set": {"reason": reason or "No reason"}},
        upsert=True,
    )

    count = await get_warn_count(message.chat.id, target_id)
    warn_settings = await get_warn_settings(message.chat.id)
    warn_limit = int(warn_settings.get("warn_limit", 3))
    warn_action = str(warn_settings.get("warn_action", "mute")).lower()

    text = join_lines(
        "⚠️ <b>User warned</b>",
        f"User ID: {hcode(str(target_id))}",
        f"Warn count: {hcode(str(count))}",
        f"Warn limit: {hcode(str(warn_limit))}",
        f"Warn action: {hcode(warn_action)}",
        f"Reason: {reason or 'No reason'}",
    )

    if warn_action != "off" and count >= warn_limit:
        bot_can_restrict = await can_restrict_members(message.bot, message.chat.id, (await message.bot.get_me()).id)
        if not bot_can_restrict:
            await message.reply(join_lines(text, "", "Auto action လုပ်ဖို့ bot မှာ restrict/ban permission မရှိပါ။"))
            return

        ok, result = await apply_warn_action(message, target_id, warn_action)
        if ok:
            await reset_warn_count(message.chat.id, target_id)
            await message.reply(join_lines(text, "", f"✅ Warn limit ပြည့်လို့ auto {warn_action} လုပ်ပြီးပါပြီ။", "Warn count ကို reset လုပ်လိုက်ပါတယ်။"))
            return

        await message.reply(join_lines(text, "", f"❌ Auto action မအောင်မြင်ပါ: <code>{result}</code>"))
        return

    await message.reply(text)


@router.message(Command("warns"))
async def warns_cmd(message: Message) -> None:
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    else:
        target_id = await extract_target_user_id(message) or (message.from_user.id if message.from_user else None)

    if not target_id:
        await message.reply("user မတွေ့ပါ။")
        return

    count = await get_warn_count(message.chat.id, target_id)
    warn_settings = await get_warn_settings(message.chat.id)
    await message.reply(
        join_lines(
            "<b>Warn Info</b>",
            f"User: {hcode(str(target_id))}",
            f"Warn count: {hcode(str(count))}",
            f"Warn limit: {hcode(str(warn_settings.get('warn_limit', 3)))}",
            f"Warn action: {hcode(str(warn_settings.get('warn_action', 'mute')))}",
        )
    )


@router.message(Command("resetwarns"))
async def resetwarns_cmd(message: Message) -> None:
    admin = message.from_user
    if not admin:
        return
    if message.chat.type not in {"group", "supergroup"}:
        await message.reply("ဒီ command ကို group ထဲမှာသာသုံးပါ။")
        return
    if not await is_user_admin(message.bot, message.chat.id, admin.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    target_id = await extract_target_user_id(message)
    if not target_id:
        await message.reply("reply လုပ်ပြီး <code>/resetwarns</code> သုံးပါ။")
        return

    col = warns_collection()
    if col is None:
        await message.reply("MongoDB မချိတ်ထားသေးပါ။")
        return

    await col.delete_one({"chat_id": message.chat.id, "user_id": target_id})
    await message.reply("Warns reset လုပ်ပြီးပါပြီ ✅")


@router.message(Command("warnlimit"))
async def warnlimit_cmd(message: Message) -> None:
    admin = message.from_user
    if not admin:
        return
    if message.chat.type not in {"group", "supergroup"}:
        await message.reply("ဒီ command ကို group ထဲမှာသာသုံးပါ။")
        return
    if not await is_user_admin(message.bot, message.chat.id, admin.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    value = parse_int(remove_command(message.text))
    if value is None or value < 1 or value > 100:
        await message.reply("အသုံးပြုပုံ: <code>/warnlimit 3</code>")
        return

    await set_warn_limit(message.chat.id, value)
    await message.reply(f"Warn limit ကို {hcode(str(value))} အဖြစ်သိမ်းပြီးပါပြီ ✅")


@router.message(Command("warnaction"))
async def warnaction_cmd(message: Message) -> None:
    admin = message.from_user
    if not admin:
        return
    if message.chat.type not in {"group", "supergroup"}:
        await message.reply("ဒီ command ကို group ထဲမှာသာသုံးပါ။")
        return
    if not await is_user_admin(message.bot, message.chat.id, admin.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    action = remove_command(message.text).strip().lower()
    if action not in {"mute", "ban", "off"}:
        await message.reply("အသုံးပြုပုံ:\n<code>/warnaction mute</code>\n<code>/warnaction ban</code>\n<code>/warnaction off</code>")
        return

    await set_warn_action(message.chat.id, action)
    await message.reply(f"Warn action ကို {hcode(action)} အဖြစ်သိမ်းပြီးပါပြီ ✅")
