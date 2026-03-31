from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.permissions import is_user_admin
from app.services.mongo import add_note, delete_note, get_note, list_notes
from app.utils.formatters import bullet_list, hbold, join_lines
from app.utils.parser import parse_note_name_and_text, remove_command

router = Router()


def build_note_payload(message: Message, fallback_text: str = "") -> dict:
    replied = message.reply_to_message

    if replied:
        if replied.photo:
            return {"note_type": "photo", "file_id": replied.photo[-1].file_id, "text": fallback_text or replied.caption or "", "created_by": message.from_user.id if message.from_user else 0}
        if replied.video:
            return {"note_type": "video", "file_id": replied.video.file_id, "text": fallback_text or replied.caption or "", "created_by": message.from_user.id if message.from_user else 0}
        if replied.document:
            return {"note_type": "document", "file_id": replied.document.file_id, "text": fallback_text or replied.caption or "", "created_by": message.from_user.id if message.from_user else 0}
        if replied.animation:
            return {"note_type": "animation", "file_id": replied.animation.file_id, "text": fallback_text or replied.caption or "", "created_by": message.from_user.id if message.from_user else 0}
        if replied.audio:
            return {"note_type": "audio", "file_id": replied.audio.file_id, "text": fallback_text or replied.caption or "", "created_by": message.from_user.id if message.from_user else 0}
        if replied.voice:
            return {"note_type": "voice", "file_id": replied.voice.file_id, "text": fallback_text or replied.caption or "", "created_by": message.from_user.id if message.from_user else 0}
        if replied.sticker:
            return {"note_type": "sticker", "file_id": replied.sticker.file_id, "text": fallback_text or "", "created_by": message.from_user.id if message.from_user else 0}
        if replied.text or replied.caption:
            return {"note_type": "text", "text": fallback_text or replied.text or replied.caption or "", "created_by": message.from_user.id if message.from_user else 0}

    return {"note_type": "text", "text": fallback_text, "created_by": message.from_user.id if message.from_user else 0}


async def send_note(message: Message, note: dict) -> None:
    note_type = note.get("note_type", "text")
    file_id = note.get("file_id")
    text = note.get("text", "")

    if note_type == "text":
        await message.reply(text or "Empty note")
    elif note_type == "photo" and file_id:
        await message.reply_photo(file_id, caption=text or None)
    elif note_type == "video" and file_id:
        await message.reply_video(file_id, caption=text or None)
    elif note_type == "document" and file_id:
        await message.reply_document(file_id, caption=text or None)
    elif note_type == "animation" and file_id:
        await message.reply_animation(file_id, caption=text or None)
    elif note_type == "audio" and file_id:
        await message.reply_audio(file_id, caption=text or None)
    elif note_type == "voice" and file_id:
        await message.reply_voice(file_id, caption=text or None)
    elif note_type == "sticker" and file_id:
        await message.reply_sticker(file_id)
        if text:
            await message.reply(text)
    else:
        await message.reply(text or "Unsupported saved note format.")


@router.message(Command("save"))
async def save_note_cmd(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    if message.chat.type in {"group", "supergroup"} and not await is_user_admin(message.bot, message.chat.id, user.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    if message.reply_to_message:
        args = remove_command(message.text)
        if not args:
            await message.reply(
                "အသုံးပြုပုံ:\n<code>/save note_name</code> (reply to media/text)\nသို့\n<code>/save note_name optional caption</code>"
            )
            return
        parts = args.split(maxsplit=1)
        name = parts[0].strip().lower()
        extra_text = parts[1].strip() if len(parts) > 1 else ""
        payload = build_note_payload(message, fallback_text=extra_text)
        await add_note(message.chat.id, name, payload)
        await message.reply(f"Note {hbold(name)} ကို သိမ်းပြီးပါပြီ ✅")
        return

    name, text = parse_note_name_and_text(message.text)
    if not name or not text:
        await message.reply("အသုံးပြုပုံ:\n<code>/save note_name note text</code>\nသို့ reply လုပ်ပြီး\n<code>/save note_name</code>")
        return

    payload = build_note_payload(message, fallback_text=text)
    await add_note(message.chat.id, name, payload)
    await message.reply(f"Note {hbold(name)} ကို သိမ်းပြီးပါပြီ ✅")


@router.message(Command("get"))
async def get_note_cmd(message: Message) -> None:
    name = remove_command(message.text).strip().lower()
    if not name:
        await message.reply("အသုံးပြုပုံ:\n<code>/get note_name</code>")
        return
    note = await get_note(message.chat.id, name)
    if not note:
        await message.reply("ဒီ note မရှိသေးပါ။")
        return
    await send_note(message, note)


@router.message(Command("clear"))
async def clear_note_cmd(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    if message.chat.type in {"group", "supergroup"} and not await is_user_admin(message.bot, message.chat.id, user.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    name = remove_command(message.text).strip().lower()
    if not name:
        await message.reply("အသုံးပြုပုံ:\n<code>/clear note_name</code>")
        return

    ok = await delete_note(message.chat.id, name)
    await message.reply("ဖျက်ပြီးပါပြီ ✅" if ok else "ဒီ note မရှိပါ။")


@router.message(Command("notes"))
async def notes_list_cmd(message: Message) -> None:
    notes = await list_notes(message.chat.id)
    if not notes:
        await message.reply("ဒီ chat မှာ notes မရှိသေးပါ။")
        return

    names = []
    for note in notes:
        name = note.get("name", "")
        note_type = note.get("note_type", "text")
        if name:
            names.append(f"`{name}` ({note_type})")

    await message.reply(join_lines("<b>Saved Notes</b>", "", bullet_list(names)))


@router.message(F.text.regexp(r"^#([A-Za-z0-9_]+)$"))
async def hashtag_note_getter(message: Message) -> None:
    if not message.text:
        return
    name = message.text[1:].strip().lower()
    note = await get_note(message.chat.id, name)
    if note:
        await send_note(message, note)
