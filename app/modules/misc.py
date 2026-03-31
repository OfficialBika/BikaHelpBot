from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from app.core.filters import IsOwnerFilter
from app.core.permissions import is_user_admin
from app.services.mongo import export_chat_backup, get_all_chat_settings, import_chat_backup, replace_chat_settings
from app.utils.formatters import hcode, hpre, join_lines
from app.utils.helpers import get_full_name

router = Router()


async def is_group_admin_message(message: Message) -> bool:
    user = message.from_user
    if not user or message.chat.type not in {"group", "supergroup"}:
        return False
    return await is_user_admin(message.bot, message.chat.id, user.id)


@router.message(Command("ping"))
async def ping_cmd(message: Message) -> None:
    start = time.perf_counter()
    sent = await message.reply("Pinging ...")
    latency = (time.perf_counter() - start) * 1000
    await sent.edit_text(f"Pong! {latency:.2f} ms")


@router.message(Command("id"))
async def id_cmd(message: Message) -> None:
    user = message.from_user
    chat = message.chat
    text = join_lines(
        "<b>ID Information</b>",
        "",
        f"User: {get_full_name(user)}",
        f"User ID: {hcode(str(user.id if user else 0))}",
        f"Chat ID: {hcode(str(chat.id if chat else 0))}",
        f"Chat Type: {hcode(str(chat.type if chat else 'unknown'))}",
    )
    if message.reply_to_message and message.reply_to_message.from_user:
        replied = message.reply_to_message.from_user
        text = join_lines(text, "", f"Replied User: {get_full_name(replied)}", f"Replied User ID: {hcode(str(replied.id))}")
    await message.reply(text)


@router.message(Command("json"), IsOwnerFilter())
async def json_cmd(message: Message) -> None:
    target = message.reply_to_message or message
    data = target.model_dump(mode="json", exclude_none=True)
    pretty = json.dumps(data, indent=2, ensure_ascii=False)
    if len(pretty) > 3900:
        pretty = pretty[:3900] + "\n... (truncated)"
    await message.reply(hpre(pretty))


@router.message(Command("about"))
async def about_cmd(message: Message) -> None:
    await message.reply(join_lines("<b>About This Bot</b>", "", "Modern modular Telegram group management bot.", "Framework: <code>aiogram 3.x</code>", "Raw layer: <code>Telethon</code>", "Database: <code>MongoDB + Redis</code>"))


@router.message(Command("exportsettings"))
async def export_settings_cmd(message: Message) -> None:
    if not await is_group_admin_message(message):
        await message.reply("ဒီ command ကို group admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    data = await get_all_chat_settings(message.chat.id)
    export_data = {"chat_id": message.chat.id, "chat_title": message.chat.title, "exported_by": message.from_user.id if message.from_user else 0, "settings": data}
    raw = json.dumps(export_data, indent=2, ensure_ascii=False).encode("utf-8")
    file = BufferedInputFile(raw, filename=f"settings_backup_{message.chat.id}.json")
    await message.reply_document(file, caption="ဒီ file ကို `/importsettings` နဲ့ reply လုပ်ပြီး restore ပြန်လုပ်လို့ရပါတယ်။")


@router.message(Command("importsettings"))
async def import_settings_cmd(message: Message) -> None:
    if not await is_group_admin_message(message):
        await message.reply("ဒီ command ကို group admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    replied = message.reply_to_message
    if not replied or not replied.document:
        await message.reply("အသုံးပြုပုံ:\nsettings backup `.json` file ကို reply လုပ်ပြီး\n<code>/importsettings</code>")
        return
    if not replied.document.file_name or not replied.document.file_name.endswith(".json"):
        await message.reply("JSON backup file ကို reply လုပ်ပေးပါ။")
        return

    file = await message.bot.get_file(replied.document.file_id)
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / replied.document.file_name
        await message.bot.download_file(file.file_path, destination=file_path)
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            await message.reply(f"JSON file ဖတ်မရပါ: <code>{exc}</code>")
            return

    settings_data = payload.get("settings")
    if not isinstance(settings_data, dict):
        await message.reply("Backup file format မမှန်ပါ။")
        return

    ok = await replace_chat_settings(message.chat.id, settings_data)
    if not ok:
        await message.reply("Settings import မအောင်မြင်ပါ။")
        return
    await message.reply("Settings import လုပ်ပြီးပါပြီ ✅")


@router.message(Command("exportchat"))
async def export_chat_cmd(message: Message) -> None:
    if not await is_group_admin_message(message):
        await message.reply("ဒီ command ကို group admin တွေပဲသုံးလို့ရပါတယ်။")
        return
    backup = await export_chat_backup(message.chat.id)
    export_data = {"version": 1, "chat_id": message.chat.id, "chat_title": message.chat.title, "exported_by": message.from_user.id if message.from_user else 0, "data": backup}
    raw = json.dumps(export_data, indent=2, ensure_ascii=False).encode("utf-8")
    file = BufferedInputFile(raw, filename=f"full_chat_backup_{message.chat.id}.json")
    await message.reply_document(file, caption=join_lines("<b>Full chat backup ready</b>", "", "ပါဝင်သည့် data:", "• settings", "• notes", "• filters", "• blacklists", "", "ဒီ file ကို `/importchat` နဲ့ reply လုပ်ပြီး restore ပြန်လုပ်လို့ရပါတယ်။"))


@router.message(Command("importchat"))
async def import_chat_cmd(message: Message) -> None:
    if not await is_group_admin_message(message):
        await message.reply("ဒီ command ကို group admin တွေပဲသုံးလို့ရပါတယ်။")
        return
    replied = message.reply_to_message
    if not replied or not replied.document:
        await message.reply("အသုံးပြုပုံ:\nfull backup `.json` file ကို reply လုပ်ပြီး\n<code>/importchat</code>")
        return
    if not replied.document.file_name or not replied.document.file_name.endswith(".json"):
        await message.reply("JSON backup file ကို reply လုပ်ပေးပါ။")
        return

    file = await message.bot.get_file(replied.document.file_id)
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / replied.document.file_name
        await message.bot.download_file(file.file_path, destination=file_path)
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            await message.reply(f"JSON file ဖတ်မရပါ: <code>{exc}</code>")
            return

    data = payload.get("data")
    if not isinstance(data, dict):
        await message.reply("Full backup file format မမှန်ပါ။")
        return

    result = await import_chat_backup(message.chat.id, data)
    await message.reply(join_lines("✅ <b>Full chat backup imported</b>", "", f"Settings: <code>{result.get('settings', 0)}</code>", f"Notes: <code>{result.get('notes', 0)}</code>", f"Filters: <code>{result.get('filters', 0)}</code>", f"Blacklists: <code>{result.get('blacklists', 0)}</code>"))
