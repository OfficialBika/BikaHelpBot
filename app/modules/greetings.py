from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, Message

from app.core.permissions import is_user_admin
from app.services.mongo import mongo
from app.utils.helpers import mention_html
from app.utils.parser import extract_args

router = Router(name="greetings")

DEFAULT_WELCOME = "Welcome {mention} to {chat_name}!"


async def _settings_collection():
    return mongo.db["greetings"] if mongo.db is not None else None


@router.chat_member()
async def greet_new_member(event: ChatMemberUpdated) -> None:
    if not event.new_chat_member or not event.new_chat_member.user:
        return
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    if old_status == new_status:
        return
    if new_status not in {"member", "administrator"}:
        return

    collection = await _settings_collection()
    enabled = True
    template = DEFAULT_WELCOME
    if collection is not None:
        doc = await collection.find_one({"chat_id": event.chat.id}) or {}
        enabled = doc.get("enabled", True)
        template = doc.get("welcome_text", DEFAULT_WELCOME)
    if not enabled:
        return

    user = event.new_chat_member.user
    text = template.format(mention=mention_html(user), first=user.first_name, chat_name=event.chat.title or "this chat")
    await event.bot.send_message(event.chat.id, text)


@router.message(Command("welcome"))
async def welcome_toggle(message: Message) -> None:
    if not await is_user_admin(message):
        await message.answer("Admins only.")
        return
    arg = extract_args(message.text or "").lower()
    if arg not in {"on", "off"}:
        await message.answer("Usage: /welcome on OR /welcome off")
        return
    collection = await _settings_collection()
    if collection is None:
        await message.answer("MongoDB is not connected. Only default welcome is active.")
        return
    await collection.update_one(
        {"chat_id": message.chat.id},
        {"$set": {"enabled": arg == "on"}},
        upsert=True,
    )
    await message.answer(f"Welcome set to: {arg}")


@router.message(Command("setwelcome"))
async def set_welcome(message: Message) -> None:
    if not await is_user_admin(message):
        await message.answer("Admins only.")
        return
    text = extract_args(message.text or "")
    if not text:
        await message.answer("Usage: /setwelcome Welcome {mention} to {chat_name}!")
        return
    collection = await _settings_collection()
    if collection is None:
        await message.answer("MongoDB is not connected.")
        return
    await collection.update_one(
        {"chat_id": message.chat.id},
        {"$set": {"welcome_text": text}},
        upsert=True,
    )
    await message.answer("Custom welcome text saved.")
