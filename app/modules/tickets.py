from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import get_settings
from app.core.filters import IsSupportOrOwnerFilter
from app.keyboards.inline import ticket_admin_keyboard
from app.services.mongo import get_collection
from app.services.redis import clear_state, get_state, set_state
from app.utils.formatters import hcode, join_lines
from app.utils.helpers import schedule_delete
from app.utils.parser import remove_command, split_once

router = Router()
settings = get_settings()

STATE_REPLY_TICKET_PREFIX = "ticket:reply"


def tickets_collection():
    return get_collection("tickets")


def build_ticket_panel_text(doc: dict) -> str:
    ticket_id = str(doc["_id"])
    return join_lines(
        "<b>Ticket Panel</b>",
        f"Ticket ID: {hcode(ticket_id)}",
        f"User ID: {hcode(str(doc.get('user_id', '')))}",
        f"Name: {doc.get('full_name') or 'Unknown'}",
        f"Status: {hcode(str(doc.get('status', 'open')))}",
        "",
        "<b>User Message:</b>",
        doc.get("text", ""),
        "",
        f"<b>Admin Reply:</b> {doc.get('admin_reply') or '—'}",
    )


async def update_ticket_panel(bot, doc: dict) -> None:
    panel_chat_id = doc.get("panel_chat_id")
    panel_message_id = doc.get("panel_message_id")
    if not panel_chat_id or not panel_message_id:
        return
    ticket_id = str(doc["_id"])
    is_closed = str(doc.get("status", "")).lower() == "closed"
    try:
        await bot.edit_message_text(
            chat_id=int(panel_chat_id),
            message_id=int(panel_message_id),
            text=build_ticket_panel_text(doc),
            reply_markup=ticket_admin_keyboard(ticket_id=ticket_id, is_closed=is_closed),
        )
    except Exception:
        pass


async def get_ticket_doc(ticket_id: str) -> dict | None:
    col = tickets_collection()
    if col is None:
        return None
    from bson import ObjectId
    try:
        obj_id = ObjectId(ticket_id)
    except Exception:
        return None
    return await col.find_one({"_id": obj_id})


async def set_ticket_status(ticket_id: str, status: str, admin_reply: str | None = None) -> dict | None:
    col = tickets_collection()
    if col is None:
        return None
    from bson import ObjectId
    try:
        obj_id = ObjectId(ticket_id)
    except Exception:
        return None

    update_data = {"status": status, "updated_at": datetime.now(timezone.utc)}
    if admin_reply is not None:
        update_data["admin_reply"] = admin_reply
    await col.update_one({"_id": obj_id}, {"$set": update_data})
    return await col.find_one({"_id": obj_id})


@router.message(Command("ticket"))
async def create_ticket_cmd(message: Message) -> None:
    if message.chat.type != "private":
        await message.reply("Ticket command ကို private chat ထဲမှာသာသုံးပါ။")
        return
    user = message.from_user
    if not user:
        return

    text = remove_command(message.text)
    if not text:
        await message.reply("အသုံးပြုပုံ:\n<code>/ticket your issue here</code>")
        return

    col = tickets_collection()
    if col is None:
        await message.reply("MongoDB မချိတ်ထားသေးပါ။")
        return

    doc = {
        "user_id": user.id,
        "username": user.username,
        "full_name": " ".join(x for x in [user.first_name or "", user.last_name or ""] if x).strip(),
        "text": text,
        "status": "open",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "admin_reply": "",
        "panel_chat_id": None,
        "panel_message_id": None,
    }
    result = await col.insert_one(doc)
    ticket_id = str(result.inserted_id)

    await message.reply(join_lines("🎫 <b>Ticket created</b>", f"Ticket ID: {hcode(ticket_id)}", "Support team ကနောက်ပိုင်း follow up လုပ်နိုင်ပါတယ်။"))

    if settings.LOG_CHAT_ID:
        try:
            panel_doc = {**doc, "_id": result.inserted_id}
            sent = await message.bot.send_message(settings.LOG_CHAT_ID, build_ticket_panel_text(panel_doc), reply_markup=ticket_admin_keyboard(ticket_id=ticket_id, is_closed=False))
            await col.update_one({"_id": result.inserted_id}, {"$set": {"panel_chat_id": settings.LOG_CHAT_ID, "panel_message_id": sent.message_id}})
        except Exception:
            pass


@router.message(Command("tickets"))
async def list_my_tickets_cmd(message: Message) -> None:
    if message.chat.type != "private":
        await message.reply("ဒီ command ကို private chat ထဲမှာသာသုံးပါ။")
        return
    user = message.from_user
    if not user:
        return
    col = tickets_collection()
    if col is None:
        await message.reply("MongoDB မချိတ်ထားသေးပါ။")
        return
    docs = await col.find({"user_id": user.id}).sort("created_at", -1).to_list(length=20)
    if not docs:
        await message.reply("မင်းရဲ့ tickets မရှိသေးပါ။")
        return
    lines = [f"• <code>{doc['_id']}</code> - {doc.get('status', 'open')}" for doc in docs]
    await message.reply(join_lines("<b>Your Tickets</b>", "", "\n".join(lines)))


@router.message(Command("opentickets"), IsSupportOrOwnerFilter())
async def open_tickets_cmd(message: Message) -> None:
    col = tickets_collection()
    if col is None:
        await message.reply("MongoDB မချိတ်ထားသေးပါ။")
        return
    docs = await col.find({"status": "open"}).sort("created_at", -1).to_list(length=50)
    if not docs:
        await message.reply("Open tickets မရှိသေးပါ။")
        return
    lines = [f"• <code>{doc['_id']}</code> | user <code>{doc.get('user_id')}</code>" for doc in docs]
    await message.reply(join_lines("<b>Open Tickets</b>", "", "\n".join(lines)))


@router.message(Command("replyticket"), IsSupportOrOwnerFilter())
async def reply_ticket_cmd(message: Message) -> None:
    args = remove_command(message.text)
    if not args:
        await message.reply("အသုံးပြုပုံ:\n<code>/replyticket ticket_id your reply text</code>")
        return
    ticket_id, reply_text = split_once(args)
    if not ticket_id or not reply_text:
        await message.reply("အသုံးပြုပုံ:\n<code>/replyticket ticket_id your reply text</code>")
        return
    doc = await get_ticket_doc(ticket_id)
    if not doc:
        await message.reply("Ticket မတွေ့ပါ။")
        return
    updated = await set_ticket_status(ticket_id, "answered", admin_reply=reply_text)
    if not updated:
        await message.reply("Ticket update မအောင်မြင်ပါ။")
        return
    try:
        await message.bot.send_message(int(doc["user_id"]), join_lines("💬 <b>Ticket Reply</b>", f"Ticket ID: {hcode(ticket_id)}", "", reply_text))
    except Exception as exc:
        await message.reply(f"User ဆီ reply ပို့မရပါ: <code>{exc}</code>")
        return
    await update_ticket_panel(message.bot, updated)
    temp = await message.reply("Ticket reply ပို့ပြီးပါပြီ ✅")
    schedule_delete(temp, 12)


@router.message(Command("closeticket"), IsSupportOrOwnerFilter())
async def close_ticket_cmd(message: Message) -> None:
    ticket_id = remove_command(message.text).strip()
    if not ticket_id:
        await message.reply("အသုံးပြုပုံ:\n<code>/closeticket ticket_id</code>")
        return
    doc = await get_ticket_doc(ticket_id)
    if not doc:
        await message.reply("Ticket မတွေ့ပါ။")
        return
    updated = await set_ticket_status(ticket_id, "closed")
    if not updated:
        await message.reply("Ticket update မအောင်မြင်ပါ။")
        return
    try:
        await message.bot.send_message(int(doc["user_id"]), join_lines("✅ <b>Ticket Closed</b>", f"Ticket ID: {hcode(ticket_id)}", "ဒီ ticket ကို close လုပ်ပြီးပါပြီ။"))
    except Exception:
        pass
    await update_ticket_panel(message.bot, updated)
    temp = await message.reply("Ticket ကို close လုပ်ပြီးပါပြီ ✅")
    schedule_delete(temp, 12)


@router.callback_query(F.data.startswith("ticket:reply:"), IsSupportOrOwnerFilter())
async def ticket_reply_button_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    ticket_id = query.data.split(":")[-1]
    await set_state(query.message.chat.id, query.from_user.id, f"{STATE_REPLY_TICKET_PREFIX}:{ticket_id}", expire=600)
    await query.answer("Reply mode started.")
    temp = await query.message.reply(join_lines("<b>Ticket Reply Mode</b>", f"Ticket ID: {hcode(ticket_id)}", "", "အခု reply text ကို ပို့ပါ။", "cancel လုပ်ချင်ရင် <code>cancel</code> ပို့ပါ။"))
    schedule_delete(temp, 30)


@router.callback_query(F.data.startswith("ticket:close:"), IsSupportOrOwnerFilter())
async def ticket_close_button_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    ticket_id = query.data.split(":")[-1]
    doc = await get_ticket_doc(ticket_id)
    if not doc:
        await query.answer("Ticket not found.", show_alert=True); return
    updated = await set_ticket_status(ticket_id, "closed")
    if not updated:
        await query.answer("Update failed.", show_alert=True); return
    try:
        await query.bot.send_message(int(doc["user_id"]), join_lines("✅ <b>Ticket Closed</b>", f"Ticket ID: {hcode(ticket_id)}", "ဒီ ticket ကို close လုပ်ပြီးပါပြီ။"))
    except Exception:
        pass
    await update_ticket_panel(query.bot, updated)
    await query.answer("Ticket closed.")


@router.callback_query(F.data.startswith("ticket:refresh:"), IsSupportOrOwnerFilter())
async def ticket_refresh_button_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    ticket_id = query.data.split(":")[-1]
    doc = await get_ticket_doc(ticket_id)
    if not doc:
        await query.answer("Ticket not found.", show_alert=True); return
    await update_ticket_panel(query.bot, doc)
    await query.answer("Refreshed.")


@router.message(F.text, IsSupportOrOwnerFilter())
async def ticket_reply_state_listener(message: Message) -> None:
    if not message.from_user:
        return
    state = await get_state(message.chat.id, message.from_user.id)
    if not state or not state.startswith(f"{STATE_REPLY_TICKET_PREFIX}:"):
        return
    if (message.text or "").strip().lower() == "cancel":
        await clear_state(message.chat.id, message.from_user.id)
        temp = await message.reply("Ticket reply mode ကို ပိတ်လိုက်ပါပြီ။")
        schedule_delete(temp, 10)
        return
    reply_text = (message.text or "").strip()
    if not reply_text:
        temp = await message.reply("Reply text ကိုပို့ပါ။")
        schedule_delete(temp, 10)
        return
    ticket_id = state.split(":", 2)[-1]
    doc = await get_ticket_doc(ticket_id)
    if not doc:
        await clear_state(message.chat.id, message.from_user.id)
        temp = await message.reply("Ticket မတွေ့ပါ။")
        schedule_delete(temp, 10)
        return
    updated = await set_ticket_status(ticket_id, "answered", admin_reply=reply_text)
    if not updated:
        temp = await message.reply("Ticket update မအောင်မြင်ပါ။")
        schedule_delete(temp, 10)
        return
    try:
        await message.bot.send_message(int(doc["user_id"]), join_lines("💬 <b>Ticket Reply</b>", f"Ticket ID: {hcode(ticket_id)}", "", reply_text))
    except Exception as exc:
        temp = await message.reply(f"User ဆီ reply ပို့မရပါ: <code>{exc}</code>")
        schedule_delete(temp, 12)
        return
    await clear_state(message.chat.id, message.from_user.id)
    await update_ticket_panel(message.bot, updated)
    temp = await message.reply("Ticket reply ပို့ပြီးပါပြီ ✅")
    schedule_delete(temp, 12)
