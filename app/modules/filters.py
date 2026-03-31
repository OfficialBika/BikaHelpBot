from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.permissions import is_user_admin
from app.services.mongo import get_collection
from app.utils.formatters import bullet_list, join_lines
from app.utils.parser import remove_command

router = Router()


def filters_collection():
    return get_collection("filters")


def build_filter_payload(message: Message, fallback_text: str = "") -> dict:
    replied = message.reply_to_message

    if replied:
        if replied.photo:
            return {"filter_type": "photo", "file_id": replied.photo[-1].file_id, "reply_text": fallback_text or replied.caption or ""}
        if replied.video:
            return {"filter_type": "video", "file_id": replied.video.file_id, "reply_text": fallback_text or replied.caption or ""}
        if replied.document:
            return {"filter_type": "document", "file_id": replied.document.file_id, "reply_text": fallback_text or replied.caption or ""}
        if replied.animation:
            return {"filter_type": "animation", "file_id": replied.animation.file_id, "reply_text": fallback_text or replied.caption or ""}
        if replied.audio:
            return {"filter_type": "audio", "file_id": replied.audio.file_id, "reply_text": fallback_text or replied.caption or ""}
        if replied.voice:
            return {"filter_type": "voice", "file_id": replied.voice.file_id, "reply_text": fallback_text or replied.caption or ""}
        if replied.sticker:
            return {"filter_type": "sticker", "file_id": replied.sticker.file_id, "reply_text": fallback_text or ""}
        if replied.text or replied.caption:
            return {"filter_type": "text", "reply_text": fallback_text or replied.text or replied.caption or ""}

    return {"filter_type": "text", "reply_text": fallback_text}


async def send_filter_reply(message: Message, data: dict) -> None:
    filter_type = data.get("filter_type", "text")
    file_id = data.get("file_id")
    reply_text = data.get("reply_text", "")

    if filter_type == "text":
        if reply_text:
            await message.reply(reply_text)
    elif filter_type == "photo" and file_id:
        await message.reply_photo(file_id, caption=reply_text or None)
    elif filter_type == "video" and file_id:
        await message.reply_video(file_id, caption=reply_text or None)
    elif filter_type == "document" and file_id:
        await message.reply_document(file_id, caption=reply_text or None)
    elif filter_type == "animation" and file_id:
        await message.reply_animation(file_id, caption=reply_text or None)
    elif filter_type == "audio" and file_id:
        await message.reply_audio(file_id, caption=reply_text or None)
    elif filter_type == "voice" and file_id:
        await message.reply_voice(file_id, caption=reply_text or None)
    elif filter_type == "sticker" and file_id:
        await message.reply_sticker(file_id)
        if reply_text:
            await message.reply(reply_text)
    elif reply_text:
        await message.reply(reply_text)


@router.message(Command("filter"))
async def add_filter_cmd(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    if message.chat.type in {"group", "supergroup"} and not await is_user_admin(message.bot, message.chat.id, user.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    col = filters_collection()
    if col is None:
        await message.reply("MongoDB မချိတ်ထားသေးပါ။")
        return

    if message.reply_to_message:
        args = remove_command(message.text)
        if not args:
            await message.reply(
                "အသုံးပြုပုံ:\n<code>/filter keyword</code> (reply to media/text)\nသို့\n<code>/filter keyword optional caption</code>"
            )
            return

        parts = args.split(maxsplit=1)
        keyword = parts[0].strip().lower()
        extra_text = parts[1].strip() if len(parts) > 1 else ""
        payload = build_filter_payload(message, fallback_text=extra_text)
        await col.update_one(
            {"chat_id": message.chat.id, "keyword": keyword},
            {"$set": {"chat_id": message.chat.id, "keyword": keyword, **payload}},
            upsert=True,
        )
        await message.reply(f"Filter `{keyword}` ကို သိမ်းပြီးပါပြီ ✅")
        return

    args = remove_command(message.text)
    if not args:
        await message.reply("အသုံးပြုပုံ:\n<code>/filter keyword reply text</code>")
        return

    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("အသုံးပြုပုံ:\n<code>/filter keyword reply text</code>")
        return

    keyword, reply_text = parts[0].lower(), parts[1].strip()
    payload = build_filter_payload(message, fallback_text=reply_text)
    await col.update_one(
        {"chat_id": message.chat.id, "keyword": keyword},
        {"$set": {"chat_id": message.chat.id, "keyword": keyword, **payload}},
        upsert=True,
    )
    await message.reply(f"Filter `{keyword}` ကို သိမ်းပြီးပါပြီ ✅")


@router.message(Command("stop"))
async def remove_filter_cmd(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    if message.chat.type in {"group", "supergroup"} and not await is_user_admin(message.bot, message.chat.id, user.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    keyword = remove_command(message.text).strip().lower()
    if not keyword:
        await message.reply("အသုံးပြုပုံ:\n<code>/stop keyword</code>")
        return

    col = filters_collection()
    if col is None:
        await message.reply("MongoDB မချိတ်ထားသေးပါ။")
        return

    result = await col.delete_one({"chat_id": message.chat.id, "keyword": keyword})
    await message.reply("ဖျက်ပြီးပါပြီ ✅" if result.deleted_count else "ဒီ filter မရှိပါ။")


@router.message(Command("filters"))
async def list_filters_cmd(message: Message) -> None:
    col = filters_collection()
    if col is None:
        await message.reply("MongoDB မချိတ်ထားသေးပါ။")
        return

    docs = await col.find({"chat_id": message.chat.id}).sort("keyword", 1).to_list(length=200)
    if not docs:
        await message.reply("ဒီ chat မှာ filters မရှိသေးပါ။")
        return

    items = []
    for doc in docs:
        keyword = doc.get("keyword")
        filter_type = doc.get("filter_type", "text")
        if keyword:
            items.append(f"`{keyword}` ({filter_type})")

    await message.reply(join_lines("<b>Saved Filters</b>", "", bullet_list(items)))


@router.message(F.text)
async def filter_listener(message: Message) -> None:
    if not message.text or message.text.startswith("/"):
        return

    col = filters_collection()
    if col is None:
        return

    docs = await col.find({"chat_id": message.chat.id}).to_list(length=300)
    if not docs:
        return

    lowered = message.text.lower()
    for doc in docs:
        keyword = str(doc.get("keyword", "")).strip().lower()
        if not keyword:
            continue
        if re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", lowered):
            await send_filter_reply(message, doc)
            return
