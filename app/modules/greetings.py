from __future__ import annotations

from pathlib import Path
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message, User

from app.config import get_settings
from app.core.permissions import is_user_admin
from app.modules.helper_funcs.formatting import mention_html
from app.services.mongo import get_chat_setting, set_chat_setting
from app.utils.formatters import join_lines
from app.utils.parser import remove_command
from app.utils.welcome_card import fetch_user_profile_image, render_card

router = Router()
settings = get_settings()

DEFAULT_WELCOME_TEXT = "ဟယ်လို {mention} 👋\n{chat_title} မှာ ကြိုဆိုပါတယ်။"
DEFAULT_CARD_TEXT = (
    "{fullname} ရေ\n\n"
    "{group_name} မှ\n"
    "လှိုက်လှဲစွာ ကြိုဆိုပါတယ်။\n\n"
    "Group ထဲမှာ စကားတွေပြောရင်း\n"
    "ဘဝရဲ့ ပျော်စရာအချိန်လေးတွေအဖြစ်\n"
    "အတူတူ ဖန်တီးလိုက်ကြရအောင်။"
)
SUPPORTED_WELCOME_TYPES = {"text", "photo", "video", "animation", "sticker", "document", "audio", "voice"}


async def admin_only(message: Message) -> bool:
    user = message.from_user
    if not user or message.chat.type not in {"group", "supergroup"}:
        return False
    return await is_user_admin(message.bot, message.chat.id, user.id)


def render_welcome_text(template: str, user: User, chat_title: str) -> str:
    fullname = " ".join(x for x in [user.first_name or "", user.last_name or ""] if x).strip() or (user.first_name or "User")
    username = user.username or user.first_name or "user"
    return (
        (template or DEFAULT_WELCOME_TEXT)
        .replace("{mention}", mention_html(user))
        .replace("{first}", user.first_name or "User")
        .replace("{fullname}", fullname)
        .replace("{group_name}", chat_title or "this chat")
        .replace("{chat_title}", chat_title or "this chat")
        .replace("{username}", username)
        .replace("{id}", str(user.id))
    )


def parse_welcome_buttons(raw: str) -> list[list[dict[str, str]]]:
    buttons: list[dict[str, str]] = []
    for part in [x.strip() for x in raw.split(";") if x.strip()]:
        if "|" not in part:
            continue
        label, url = part.split("|", 1)
        label = label.strip()
        url = url.strip()
        if not label or not url:
            continue
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("tg://") or url.startswith("https://t.me/")):
            continue
        buttons.append({"text": label[:64], "url": url})
    rows: list[list[dict[str, str]]] = []
    for i in range(0, len(buttons), 2):
        rows.append(buttons[i:i + 2])
    return rows[:5]


def build_welcome_keyboard(button_rows: list[list[dict[str, str]]] | None) -> InlineKeyboardMarkup | None:
    if not button_rows:
        return None
    inline_keyboard: list[list[InlineKeyboardButton]] = []
    for row in button_rows:
        btn_row: list[InlineKeyboardButton] = []
        for btn in row:
            text = str(btn.get("text", "")).strip()
            url = str(btn.get("url", "")).strip()
            if text and url:
                btn_row.append(InlineKeyboardButton(text=text, url=url))
        if btn_row:
            inline_keyboard.append(btn_row)
    if not inline_keyboard:
        return None
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_welcome_button_rows(chat_id: int) -> list[list[dict[str, str]]]:
    data = await get_chat_setting(chat_id, "welcome_buttons", [])
    return data if isinstance(data, list) else []


def build_welcome_payload(message: Message, fallback_text: str = "") -> dict[str, Any]:
    replied = message.reply_to_message
    base = {
        "welcome_enabled": True,
        "welcome_text": fallback_text or DEFAULT_WELCOME_TEXT,
    }

    if not replied:
        return {**base, "welcome_type": "text", "welcome_file_id": "", "welcome_use_card": True}

    if replied.photo:
        return {**base, "welcome_type": "photo", "welcome_file_id": replied.photo[-1].file_id, "welcome_text": fallback_text or replied.caption or DEFAULT_WELCOME_TEXT, "welcome_use_card": False}
    if replied.video:
        return {**base, "welcome_type": "video", "welcome_file_id": replied.video.file_id, "welcome_text": fallback_text or replied.caption or DEFAULT_WELCOME_TEXT, "welcome_use_card": False}
    if replied.animation:
        return {**base, "welcome_type": "animation", "welcome_file_id": replied.animation.file_id, "welcome_text": fallback_text or replied.caption or DEFAULT_WELCOME_TEXT, "welcome_use_card": False}
    if replied.sticker:
        return {**base, "welcome_type": "sticker", "welcome_file_id": replied.sticker.file_id, "welcome_text": fallback_text or DEFAULT_WELCOME_TEXT, "welcome_use_card": False}
    if replied.document:
        return {**base, "welcome_type": "document", "welcome_file_id": replied.document.file_id, "welcome_text": fallback_text or replied.caption or DEFAULT_WELCOME_TEXT, "welcome_use_card": False}
    if replied.audio:
        return {**base, "welcome_type": "audio", "welcome_file_id": replied.audio.file_id, "welcome_text": fallback_text or replied.caption or DEFAULT_WELCOME_TEXT, "welcome_use_card": False}
    if replied.voice:
        return {**base, "welcome_type": "voice", "welcome_file_id": replied.voice.file_id, "welcome_text": fallback_text or replied.caption or DEFAULT_WELCOME_TEXT, "welcome_use_card": False}
    if replied.text or replied.caption:
        return {**base, "welcome_type": "text", "welcome_file_id": "", "welcome_text": fallback_text or replied.text or replied.caption or DEFAULT_WELCOME_TEXT, "welcome_use_card": True}

    return {**base, "welcome_type": "text", "welcome_file_id": "", "welcome_use_card": True}


async def send_media_or_text_welcome(message: Message, user: User) -> Message:
    welcome_type = str(await get_chat_setting(message.chat.id, "welcome_type", "text") or "text").lower()
    if welcome_type not in SUPPORTED_WELCOME_TYPES:
        welcome_type = "text"
    template = await get_chat_setting(message.chat.id, "welcome_text", DEFAULT_WELCOME_TEXT)
    file_id = await get_chat_setting(message.chat.id, "welcome_file_id", "")
    caption = render_welcome_text(template, user, message.chat.title or "this chat")
    keyboard = build_welcome_keyboard(await get_welcome_button_rows(message.chat.id))

    if welcome_type == "photo" and file_id:
        return await message.reply_photo(file_id, caption=caption, reply_markup=keyboard)
    if welcome_type == "video" and file_id:
        return await message.reply_video(file_id, caption=caption, reply_markup=keyboard)
    if welcome_type == "animation" and file_id:
        return await message.reply_animation(file_id, caption=caption, reply_markup=keyboard)
    if welcome_type == "document" and file_id:
        return await message.reply_document(file_id, caption=caption, reply_markup=keyboard)
    if welcome_type == "audio" and file_id:
        return await message.reply_audio(file_id, caption=caption, reply_markup=keyboard)
    if welcome_type == "voice" and file_id:
        return await message.reply_voice(file_id, caption=caption, reply_markup=keyboard)
    if welcome_type == "sticker" and file_id:
        sent = await message.reply_sticker(file_id, reply_markup=keyboard)
        if caption:
            await message.reply(caption, reply_markup=keyboard)
        return sent
    return await message.reply(caption, reply_markup=keyboard)


async def send_card_welcome(message: Message, user: User) -> Message | None:
    if not settings.WELCOME_CARD_ENABLED:
        return None
    template_path = Path(settings.WELCOME_CARD_TEMPLATE)
    if not template_path.exists():
        return None

    fullname = " ".join(x for x in [user.first_name or "", user.last_name or ""] if x).strip() or (user.first_name or "User")
    card_text = await get_chat_setting(message.chat.id, "welcome_card_text", DEFAULT_CARD_TEXT)
    caption_template = await get_chat_setting(message.chat.id, "welcome_text", DEFAULT_WELCOME_TEXT)
    caption = render_welcome_text(caption_template, user, message.chat.title or "this chat")
    keyboard = build_welcome_keyboard(await get_welcome_button_rows(message.chat.id))

    try:
        profile_image = await fetch_user_profile_image(message.bot, user.id)
        card_path = render_card(fullname=fullname, group_name=message.chat.title or "this chat", profile_image=profile_image, custom_text=card_text)
        return await message.reply_photo(FSInputFile(card_path), caption=caption, reply_markup=keyboard)
    except Exception:
        return None


async def send_welcome_message(message: Message, user: User) -> Message:
    use_card = bool(await get_chat_setting(message.chat.id, "welcome_use_card", True))
    if use_card:
        sent = await send_card_welcome(message, user)
        if sent is not None:
            return sent
    return await send_media_or_text_welcome(message, user)


@router.message(Command("welcome"))
async def welcome_status_cmd(message: Message) -> None:
    if message.chat.type == "private":
        await message.reply("ဒီ command ကို group ထဲမှာသာသုံးပါ။")
        return

    enabled = await get_chat_setting(message.chat.id, "welcome_enabled", False)
    text = await get_chat_setting(message.chat.id, "welcome_text", DEFAULT_WELCOME_TEXT)
    clean = await get_chat_setting(message.chat.id, "clean_welcome", False)
    welcome_type = await get_chat_setting(message.chat.id, "welcome_type", "text")
    file_id = await get_chat_setting(message.chat.id, "welcome_file_id", "")
    use_card = await get_chat_setting(message.chat.id, "welcome_use_card", True)
    button_rows = await get_welcome_button_rows(message.chat.id)
    button_count = sum(len(row) for row in button_rows)

    await message.reply(
        join_lines(
            "<b>Welcome Settings</b>",
            "",
            f"Enabled: {'✅' if enabled else '❌'}",
            f"Default Card: {'✅' if use_card else '❌'}",
            f"Fallback Type: <code>{welcome_type}</code>",
            f"Media Saved: {'✅' if file_id else '❌'}",
            f"Clean Welcome: {'✅' if clean else '❌'}",
            f"Buttons: <code>{button_count}</code>",
            "",
            "<b>Current Caption/Text:</b>",
            text,
        )
    )


@router.message(Command("setwelcome"))
async def setwelcome_cmd(message: Message) -> None:
    if not await admin_only(message):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return

    if message.reply_to_message:
        args = remove_command(message.text)
        parts = args.split(maxsplit=1) if args else []
        fallback_text = parts[1].strip() if len(parts) > 1 else ""
        payload = build_welcome_payload(message, fallback_text=fallback_text)
        await set_chat_setting(message.chat.id, "welcome_type", payload["welcome_type"])
        await set_chat_setting(message.chat.id, "welcome_file_id", payload["welcome_file_id"])
        await set_chat_setting(message.chat.id, "welcome_text", payload["welcome_text"])
        await set_chat_setting(message.chat.id, "welcome_enabled", True)
        await set_chat_setting(message.chat.id, "welcome_use_card", payload["welcome_use_card"])
        await message.reply(
            "Welcome media message သိမ်းပြီးပါပြီ ✅\n"
            "Template card ကို ဒီ chat အတွက် auto ပိတ်လိုက်ပါတယ်။ card ပြန်သုံးချင်ရင် <code>/usecardwelcome</code> သုံးပါ။"
        )
        return

    text = remove_command(message.text)
    if not text:
        await message.reply(
            "အသုံးပြုပုံ:\n"
            "<code>/setwelcome welcome text</code>\n\n"
            "သို့ media ကို reply လုပ်ပြီး\n"
            "<code>/setwelcome</code>\n"
            "<code>/setwelcome custom caption</code>\n\n"
            "Variables: <code>{mention}</code> <code>{first}</code> <code>{fullname}</code> <code>{group_name}</code> <code>{chat_title}</code>"
        )
        return

    await set_chat_setting(message.chat.id, "welcome_type", "text")
    await set_chat_setting(message.chat.id, "welcome_file_id", "")
    await set_chat_setting(message.chat.id, "welcome_text", text)
    await set_chat_setting(message.chat.id, "welcome_enabled", True)
    await set_chat_setting(message.chat.id, "welcome_use_card", True)
    await message.reply("Template card + welcome text ကို default welcome အဖြစ်သိမ်းပြီးပါပြီ ✅")


@router.message(Command("usecardwelcome"))
async def usecardwelcome_cmd(message: Message) -> None:
    if not await admin_only(message):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return
    await set_chat_setting(message.chat.id, "welcome_use_card", True)
    await message.reply("Template card welcome ကို ပြန်ဖွင့်ပြီးပါပြီ ✅")


@router.message(Command("setwelcomecardtext"))
async def setwelcomecardtext_cmd(message: Message) -> None:
    if not await admin_only(message):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return
    text = remove_command(message.text)
    if not text:
        await message.reply("အသုံးပြုပုံ:\n<code>/setwelcomecardtext your card body text</code>")
        return
    await set_chat_setting(message.chat.id, "welcome_card_text", text)
    await message.reply("Welcome card body text သိမ်းပြီးပါပြီ ✅")


@router.message(Command("setwelcomebuttons"))
async def setwelcomebuttons_cmd(message: Message) -> None:
    if not await admin_only(message):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return
    raw = remove_command(message.text)
    if not raw:
        await message.reply(
            "အသုံးပြုပုံ:\n"
            "<code>/setwelcomebuttons Join Channel|https://t.me/yourchannel ; Rules|https://example.com/rules</code>"
        )
        return
    rows = parse_welcome_buttons(raw)
    if not rows:
        await message.reply("Button format မမှန်ပါ။ <code>Text|URL ; Text2|URL2</code> ပုံစံနဲ့ပို့ပါ။")
        return
    await set_chat_setting(message.chat.id, "welcome_buttons", rows)
    button_count = sum(len(row) for row in rows)
    await message.reply(f"Welcome buttons {button_count} ခု သိမ်းပြီးပါပြီ ✅")


@router.message(Command("clearwelcomebuttons"))
async def clearwelcomebuttons_cmd(message: Message) -> None:
    if not await admin_only(message):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return
    await set_chat_setting(message.chat.id, "welcome_buttons", [])
    await message.reply("Welcome buttons ကို ဖျက်ပြီးပါပြီ ✅")


@router.message(Command("cleanwelcome"))
async def cleanwelcome_cmd(message: Message) -> None:
    if not await admin_only(message):
        await message.reply("ဒီ command ကို admin တွေပဲသုံးလို့ရပါတယ်။")
        return
    arg = remove_command(message.text).lower()
    if arg not in {"on", "off"}:
        await message.reply("အသုံးပြုပုံ: <code>/cleanwelcome on</code> သို့ <code>/cleanwelcome off</code>")
        return
    enabled = arg == "on"
    await set_chat_setting(message.chat.id, "clean_welcome", enabled)
    await message.reply(f"Clean welcome ကို {'ဖွင့်' if enabled else 'ပိတ်'}ပြီးပါပြီ။")


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
        sent = await send_welcome_message(message, user)
        if clean_welcome and sent:
            await set_chat_setting(message.chat.id, "last_welcome_message_id", sent.message_id)
