from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import get_settings
from app.core.filters import IsOwnerFilter, IsSupportOrOwnerFilter
from app.loader import validate_startup_config
from app.services.mongo import add_support_admin, get_collection, is_support_admin, list_support_admins, ping_mongo, remove_support_admin
from app.services.redis import ping_redis
from app.services.telethon_client import get_me as telethon_get_me
from app.utils.formatters import as_bool_emoji, hcode, join_lines
from app.utils.parser import parse_int, remove_command

router = Router()
settings = get_settings()


async def count_documents(name: str, query: dict | None = None) -> int:
    collection = get_collection(name)
    if collection is None:
        return 0
    return await collection.count_documents(query or {})


@router.message(Command("admin"), IsSupportOrOwnerFilter())
async def admin_cmd(message: Message) -> None:
    mongo_ok = await ping_mongo()
    redis_ok = await ping_redis()
    telethon_me = await telethon_get_me()

    note_count = await count_documents("notes") if mongo_ok else 0
    filter_count = await count_documents("filters") if mongo_ok else 0
    warn_count = await count_documents("warns") if mongo_ok else 0
    ticket_count = await count_documents("tickets") if mongo_ok else 0
    open_ticket_count = await count_documents("tickets", {"status": "open"}) if mongo_ok else 0
    support_count = await count_documents("support_admins") if mongo_ok else 0

    role = "owner"
    if message.from_user and message.from_user.id != settings.OWNER_ID:
        role = "support_admin"

    await message.reply(
        join_lines(
            "<b>Admin Dashboard</b>",
            "",
            f"Bot Name: <code>{settings.BOT_NAME}</code>",
            f"Your Role: <code>{role}</code>",
            f"Owner ID: {hcode(str(settings.OWNER_ID))}",
            "",
            f"MongoDB: {as_bool_emoji(mongo_ok)}",
            f"Redis: {as_bool_emoji(redis_ok)}",
            f"Telethon: {as_bool_emoji(telethon_me is not None)}",
            "",
            f"Support Admins: {hcode(str(support_count))}",
            f"Notes: {hcode(str(note_count))}",
            f"Filters: {hcode(str(filter_count))}",
            f"Warns: {hcode(str(warn_count))}",
            f"Tickets: {hcode(str(ticket_count))}",
            f"Open Tickets: {hcode(str(open_ticket_count))}",
        )
    )


@router.message(Command("health"), IsSupportOrOwnerFilter())
async def health_cmd(message: Message) -> None:
    mongo_ok = await ping_mongo()
    redis_ok = await ping_redis()
    telethon_me = await telethon_get_me()
    startup_issues = validate_startup_config()

    status = "healthy"
    if not mongo_ok or not redis_ok:
        status = "degraded"
    if not mongo_ok:
        status = "critical"

    issue_lines = startup_issues[:10] if startup_issues else []

    text = join_lines(
        "<b>Health Check</b>",
        "",
        f"Overall Status: <code>{status}</code>",
        f"MongoDB: {as_bool_emoji(mongo_ok)}",
        f"Redis: {as_bool_emoji(redis_ok)}",
        f"Telethon: {as_bool_emoji(telethon_me is not None)}",
        f"Webhook Mode: <code>{settings.USE_WEBHOOK}</code>",
        f"Log Chat: <code>{settings.LOG_CHAT_ID or 'not set'}</code>",
        "",
        "<b>Startup Validation</b>",
        "\n".join(f"• {line}" for line in issue_lines) if issue_lines else "• No major config issues found",
    )

    await message.reply(text)


@router.message(Command("addsupport"), IsOwnerFilter())
async def add_support_cmd(message: Message) -> None:
    if not message.from_user:
        return

    target_id = message.reply_to_message.from_user.id if message.reply_to_message and message.reply_to_message.from_user else parse_int(remove_command(message.text))
    if not target_id:
        await message.reply("အသုံးပြုပုံ:\n<code>/addsupport user_id</code>\nသို့ reply လုပ်ပြီးသုံးပါ။")
        return
    if target_id == settings.OWNER_ID:
        await message.reply("Owner ကို support admin ထပ်မထည့်ပါနဲ့။")
        return

    await add_support_admin(target_id, message.from_user.id)
    await message.reply(f"User {hcode(str(target_id))} ကို support admin အဖြစ်ထည့်ပြီးပါပြီ ✅")


@router.message(Command("remsupport"), IsOwnerFilter())
async def remove_support_cmd(message: Message) -> None:
    target_id = message.reply_to_message.from_user.id if message.reply_to_message and message.reply_to_message.from_user else parse_int(remove_command(message.text))
    if not target_id:
        await message.reply("အသုံးပြုပုံ:\n<code>/remsupport user_id</code>\nသို့ reply လုပ်ပြီးသုံးပါ။")
        return

    ok = await remove_support_admin(target_id)
    await message.reply(
        f"User {hcode(str(target_id))} ကို support admin list ကဖျက်ပြီးပါပြီ ✅" if ok else "ဒီ user က support admin list ထဲမှာမရှိပါ။"
    )


@router.message(Command("supports"), IsOwnerFilter())
async def supports_cmd(message: Message) -> None:
    docs = await list_support_admins()
    if not docs:
        await message.reply("Support admins မရှိသေးပါ။")
        return
    lines = [f"• <code>{doc.get('user_id')}</code>" for doc in docs if doc.get("user_id")]
    await message.reply(join_lines("<b>Support Admins</b>", "", "\n".join(lines)))


@router.message(Command("issupport"), IsOwnerFilter())
async def is_support_cmd(message: Message) -> None:
    target_id = message.reply_to_message.from_user.id if message.reply_to_message and message.reply_to_message.from_user else parse_int(remove_command(message.text))
    if not target_id:
        await message.reply("အသုံးပြုပုံ:\n<code>/issupport user_id</code>\nသို့ reply လုပ်ပြီးသုံးပါ။")
        return

    ok = await is_support_admin(target_id)
    await message.reply(f"User {hcode(str(target_id))} is {'a' if ok else 'not a'} support admin.")
