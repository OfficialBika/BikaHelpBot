from __future__ import annotations

from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import get_settings
from app.core.permissions import is_user_admin
from app.services.mongo import get_chat_setting, set_chat_setting
from app.utils.formatters import join_lines
from app.utils.welcome_card import fetch_user_profile_image, render_card

router = Router()
settings = get_settings()


def build_welcome_buttons(raw_buttons: list[dict] | None):
    if not raw_buttons:
        return None

    rows = []
    for item in raw_buttons:
        text = str(item.get("text", "")).strip()
        url = str(item.get("url", "")).strip()
        if text and url:
            rows.append([InlineKeyboardButton(text=text, url=url)])

    if not rows:
        return None

    return InlineKeyboardMarkup(inline_keyboard=rows)


def parse_buttons(raw: str) -> list[dict]:
    items: list[dict] = []
    if not raw:
        return items

    for part in raw.split(";"):
        piece = part.strip()
        if not piece or "|" not in piece:
            continue
        text, url = piece.split("|", 1)
        text = text.strip()
        url = url.strip()
        if text and url:
            items.append({"text": text, "url": url})
    return items


def build_welcome_payload(message: Message, fallback_text: str = "") -> dict:
    replied = message.reply_to_message

    if replied:
        if replied.photo:
            return {
                "welcome_type": "photo",
                "file_id": replied.photo[-1].file_id,
                "welcome_text": fallback_text or replied.caption or "",
                "welcome_use_card": False,
            }

        if replied.video:
            return {
                "welcome_type": "video",
                "file_id": replied.video.file_id,
                "welcome_text": fallback_text or replied.caption or "",
                "welcome_use_card": False,
            }

        if replied.animation:
            return {
                "welcome_type": "animation",
                "file_id": replied.animation.file_id,
                "welcome_text": fallback_text or replied.caption or "",
                "welcome_use_card": False,
            }

        if replied.document:
            return {
                "welcome_type": "document",
                "file_id": replied.document.file_id,
                "welcome_text": fallback_text or replied.caption or "",
                "welcome_use_card": False,
            }

        if replied.audio:
            return {
                "welcome_type": "audio",
                "file_id": replied.audio.file_id,
                "welcome_text": fallback_text or replied.caption or "",
                "welcome_use_card": False,
            }

        if replied.voice:
            return {
                "welcome_type": "voice",
                "file_id": replied.voice.file_id,
                "welcome_text": fallback_text or replied.caption or "",
                "welcome_use_card": False,
            }

        if replied.sticker:
            return {
                "welcome_type": "sticker",
                "file_id": replied.sticker.file_id,
                "welcome_text": fallback_text or "",
                "welcome_use_card": False,
            }

        if replied.text or replied.caption:
            return {
                "welcome_type": "text",
                "file_id": "",
                "welcome_text": fallback_text or replied.text or replied.caption or "",
                "welcome_use_card": True,
            }

    return {
        "welcome_type": "text",
        "file_id": "",
        "welcome_text": fallback_text or "ဟယ်လို {mention} 👋\n{chat_title} မှာ ကြိုဆိုပါတယ်။",
        "welcome_use_card": True,
    }


def render_text_template(
    template: str,
    user_id: int,
    first_name: str,
    fullname: str,
    chat_title: str,
) -> str:
    username = first_name
    return (
        template.replace("{mention}", f'<a href="tg://user?id={user_id}">{first_name}</a>')
        .replace("{first}", first_name)
        .replace("{fullname}", fullname)
        .replace("{group_name}", chat_title)
        .replace("{chat_title}", chat_title)
        .replace("{username}", username)
        .replace("{id}", str(user_id))
    )


async def admin_only(message: Message) -> bool:
    user = message.from_user
    if not user or message.chat.type not in {"group", "supergroup"}:
        return False
    return await is_user_admin(message.bot, message.chat.id, user.id)


@router.message(Command("welcome"))
async def welcome_status_cmd(message: Message) -> None:
    if message.chat.type == "private":
        await message.reply("ဒီ command ကို group ထဲမှာသာသုံးပါ။")
        return

    enabled = await get_chat_setting(message.chat.id, "welcome_enabled", False)
    welcome_type = await get_chat_setting(message.chat.id, "welcome_type", "text")
    welcome_use_card = await get_chat_setting(message.chat.id, "welcome_use_card", True)
    text = await get_chat_setting(
        message.chat.id,
        "welcome_text",
        "ဟယ်လို {mention} 👋\n{chat_title} မှာ ကြိုဆိုပါတယ်။",
    )
    clean = await get_chat_setting(message.chat.id, "clean_welcome", False)
    buttons = await get_chat_setting(message.chat.id, "welcome_buttons", [])

    button_info = "None"
    if buttons:
        button_info = ", ".join(item.get("text", "") for item in buttons if item.get("text"))

    await message.reply(
        join_lines(
            "<b>Welcome Settings</b>",
            "",
            f"Enabled: {'✅' if enabled else '❌'}",
            f"Use Card: {'✅' if welcome_use_card else '❌'}",
            f"Type: <code>{welcome_type}</code>",
            f"Clean Welcome: {'✅' if clean else '❌'}",
            f"Buttons: <code>{button_info}</code>",
            "",
            "<b>Current Text:</b>",
            text,
        )
    )


@router.message(Command("setwelcome"))
async def setwelcome_cmd(message: Message) -> None:
    if not await admin_only(message):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    text = ""
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) > 1:
        text = parts[1].strip()

    payload = build_welcome_payload(message, fallback_text=text)

    await set_chat_setting(message.chat.id, "welcome_type", payload["welcome_type"])
    await set_chat_setting(message.chat.id, "welcome_text", payload.get("welcome_text", ""))
    await set_chat_setting(message.chat.id, "file_id", payload.get("file_id", ""))
    await set_chat_setting(message.chat.id, "welcome_use_card", payload.get("welcome_use_card", True))
    await set_chat_setting(message.chat.id, "welcome_enabled", True)

    mode_text = "card mode" if payload.get("welcome_use_card", True) else "media mode"
    await message.reply(f"Welcome {payload['welcome_type']} ကို သိမ်းပြီးပါပြီ ✅ ({mode_text})")


@router.message(Command("usecardwelcome"))
async def usecardwelcome_cmd(message: Message) -> None:
    if not await admin_only(message):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    await set_chat_setting(message.chat.id, "welcome_use_card", True)
    await set_chat_setting(message.chat.id, "welcome_enabled", True)
    await message.reply("Template card + welcome text ကို default welcome အဖြစ် ပြန်ဖွင့်ပြီးပါပြီ ✅")


@router.message(Command("setwelcomebuttons"))
async def setwelcome_buttons_cmd(message: Message) -> None:
    if not await admin_only(message):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    parts = (message.text or "").split(maxsplit=1)
    raw = parts[1].strip() if len(parts) > 1 else ""
    buttons = parse_buttons(raw)

    if not buttons:
        await message.reply(
            "အသုံးပြုပုံ:\n"
            "<code>/setwelcomebuttons Join Channel|https://t.me/yourchannel ; Rules|https://example.com</code>"
        )
        return

    await set_chat_setting(message.chat.id, "welcome_buttons", buttons)
    await message.reply("Welcome buttons သိမ်းပြီးပါပြီ ✅")


@router.message(Command("clearwelcomebuttons"))
async def clearwelcome_buttons_cmd(message: Message) -> None:
    if not await admin_only(message):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    await set_chat_setting(message.chat.id, "welcome_buttons", [])
    await message.reply("Welcome buttons ဖျက်ပြီးပါပြီ ✅")


@router.message(Command("cleanwelcome"))
async def cleanwelcome_cmd(message: Message) -> None:
    if not await admin_only(message):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    parts = (message.text or "").split(maxsplit=1)
    arg = parts[1].strip().lower() if len(parts) > 1 else ""
    if arg not in {"on", "off"}:
        await message.reply("အသုံးပြုပုံ: <code>/cleanwelcome on</code> သို့ <code>/cleanwelcome off</code>")
        return

    enabled = arg == "on"
    await set_chat_setting(message.chat.id, "clean_welcome", enabled)
    await message.reply(f"Clean welcome ကို {'ဖွင့်' if enabled else 'ပိတ်'}ပြီးပါပြီ။")


async def send_media_or_text_welcome(
    message: Message,
    welcome_type: str,
    file_id: str,
    rendered_text: str,
    markup,
):
    if welcome_type == "photo" and file_id:
        return await message.reply_photo(file_id, caption=rendered_text or None, reply_markup=markup)

    if welcome_type == "video" and file_id:
        return await message.reply_video(file_id, caption=rendered_text or None, reply_markup=markup)

    if welcome_type == "animation" and file_id:
        return await message.reply_animation(file_id, caption=rendered_text or None, reply_markup=markup)

    if welcome_type == "document" and file_id:
        return await message.reply_document(file_id, caption=rendered_text or None, reply_markup=markup)

    if welcome_type == "audio" and file_id:
        return await message.reply_audio(file_id, caption=rendered_text or None, reply_markup=markup)

    if welcome_type == "voice" and file_id:
        return await message.reply_voice(file_id, caption=rendered_text or None, reply_markup=markup)

    if welcome_type == "sticker" and file_id:
        sent = await message.reply_sticker(file_id)
        if rendered_text:
            await message.reply(rendered_text, reply_markup=markup)
        return sent

    return await message.reply(rendered_text, reply_markup=markup)


async def send_welcome(message: Message, user, chat_title: str):
    welcome_type = await get_chat_setting(message.chat.id, "welcome_type", "text")
    welcome_use_card = await get_chat_setting(message.chat.id, "welcome_use_card", True)
    template = await get_chat_setting(
        message.chat.id,
        "welcome_text",
        "ဟယ်လို {mention} 👋\n{chat_title} မှာ ကြိုဆိုပါတယ်။",
    )
    file_id = await get_chat_setting(message.chat.id, "file_id", "")
    buttons = await get_chat_setting(message.chat.id, "welcome_buttons", [])
    markup = build_welcome_buttons(buttons)

    fullname = " ".join(
        x for x in [user.first_name or "", user.last_name or ""] if x
    ).strip() or (user.first_name or "User")

    rendered_text = render_text_template(
        template=template,
        user_id=user.id,
        first_name=user.first_name or "User",
        fullname=fullname,
        chat_title=chat_title,
    )

    if welcome_use_card and settings.WELCOME_CARD_ENABLED and Path(settings.WELCOME_CARD_TEMPLATE).exists():
        try:
            profile_image = await fetch_user_profile_image(message.bot, user.id)
            card_path = render_card(
                fullname=fullname,
                group_name=chat_title,
                profile_image=profile_image,
            )
            return await message.reply_photo(
                FSInputFile(card_path),
                caption=rendered_text,
                reply_markup=markup,
            )
        except Exception:
            pass

    return await send_media_or_text_welcome(
        message=message,
        welcome_type=welcome_type,
        file_id=file_id,
        rendered_text=rendered_text,
        markup=markup,
    )


@router.message(F.new_chat_members)
async def welcome_new_members(message: Message) -> None:
    if message.chat.type not in {"group", "supergroup"}:
        return

    enabled = await get_chat_setting(message.chat.id, "welcome_enabled", False)
    if not enabled:
        return

    clean_welcome = await get_chat_setting(message.chat.id, "clean_welcome", False)
    last_welcome_id = await get_chat_setting(message.chat.id, "last_welcome_message_id", None)

    if clean_welcome and last_welcome_id:
        try:
            await message.bot.delete_message(message.chat.id, int(last_welcome_id))
        except Exception:
            pass

    for user in message.new_chat_members:
        sent = await send_welcome(message, user, message.chat.title or "this chat")
        if clean_welcome and sent:
            await set_chat_setting(message.chat.id, "last_welcome_message_id", sent.message_id)
