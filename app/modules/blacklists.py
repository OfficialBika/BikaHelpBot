from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.permissions import can_delete_messages, is_user_admin
from app.services.mongo import get_collection
from app.utils.formatters import bullet_list, join_lines
from app.utils.parser import remove_command

router = Router()


def blacklist_collection():
    return get_collection("blacklists")


@router.message(Command("blacklist"))
async def add_blacklist_cmd(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    if message.chat.type in {"group", "supergroup"} and not await is_user_admin(message.bot, message.chat.id, user.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    word = remove_command(message.text).strip().lower()
    if not word:
        await message.reply("အသုံးပြုပုံ: <code>/blacklist badword</code>")
        return

    col = blacklist_collection()
    if col is None:
        await message.reply("MongoDB မချိတ်ထားသေးပါ။")
        return

    await col.update_one({"chat_id": message.chat.id, "word": word}, {"$set": {"chat_id": message.chat.id, "word": word}}, upsert=True)
    await message.reply(f"`{word}` ကို blacklist ထဲထည့်ပြီးပါပြီ ✅")


@router.message(Command("unblacklist"))
async def remove_blacklist_cmd(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    if message.chat.type in {"group", "supergroup"} and not await is_user_admin(message.bot, message.chat.id, user.id):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    word = remove_command(message.text).strip().lower()
    if not word:
        await message.reply("အသုံးပြုပုံ: <code>/unblacklist badword</code>")
        return

    col = blacklist_collection()
    if col is None:
        await message.reply("MongoDB မချိတ်ထားသေးပါ။")
        return

    result = await col.delete_one({"chat_id": message.chat.id, "word": word})
    await message.reply("ဖျက်ပြီးပါပြီ ✅" if result.deleted_count else "ဒီ word မရှိပါ။")


@router.message(Command("blacklists"))
async def list_blacklists_cmd(message: Message) -> None:
    col = blacklist_collection()
    if col is None:
        await message.reply("MongoDB မချိတ်ထားသေးပါ။")
        return

    docs = await col.find({"chat_id": message.chat.id}).sort("word", 1).to_list(length=300)
    if not docs:
        await message.reply("Blacklist words မရှိသေးပါ။")
        return

    await message.reply(
        join_lines(
            "<b>Blacklisted Words</b>",
            "",
            bullet_list([f"`{doc['word']}`" for doc in docs if doc.get("word")]),
        )
    )


@router.message(F.text)
async def blacklist_listener(message: Message) -> None:
    if not message.text or message.text.startswith("/") or message.chat.type == "private":
        return

    col = blacklist_collection()
    if col is None:
        return

    docs = await col.find({"chat_id": message.chat.id}).to_list(length=300)
    if not docs:
        return

    lowered = message.text.lower()
    matched = any(doc.get("word", "").lower() in lowered for doc in docs if doc.get("word"))
    if not matched:
        return

    actor = message.from_user
    if actor and await is_user_admin(message.bot, message.chat.id, actor.id):
        return

    me = await message.bot.get_me()
    if actor and await can_delete_messages(message.bot, message.chat.id, me.id):
        try:
            await message.delete()
            await message.answer("Blacklist word ပါလို့ message ကိုဖျက်လိုက်ပါတယ်။")
        except Exception:
            pass
