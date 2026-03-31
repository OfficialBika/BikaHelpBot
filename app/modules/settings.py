from __future__ import annotations

from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.config import get_settings
from app.core.permissions import is_user_admin
from app.keyboards.inline import settings_greetings_keyboard, settings_main_keyboard, settings_moderation_keyboard
from app.modules.greetings import DEFAULT_CARD_TEXT, DEFAULT_WELCOME_TEXT, build_welcome_keyboard, get_welcome_button_rows, render_welcome_text
from app.services.mongo import get_chat_setting, get_warn_settings, set_chat_setting, set_warn_action, set_warn_limit
from app.services.redis import clear_state, get_state, set_state
from app.utils.formatters import join_lines
from app.utils.helpers import schedule_delete
from app.utils.welcome_card import fetch_user_profile_image, render_card

router = Router()
settings = get_settings()

STATE_SET_FORCEJOIN = "settings:set_forcejoin_channel"
STATE_SET_WELCOME_TEXT = "settings:set_welcome_text"


async def can_manage_settings(message_or_query: Message | CallbackQuery) -> bool:
    user = getattr(message_or_query, "from_user", None)
    if user is None:
        return False
    if isinstance(message_or_query, Message):
        chat = message_or_query.chat
        bot = message_or_query.bot
    else:
        chat = message_or_query.message.chat if message_or_query.message else None
        bot = message_or_query.bot
    if chat is None or bot is None or chat.type not in {"group", "supergroup"}:
        return False
    return await is_user_admin(bot, chat.id, user.id)


async def build_settings_text(chat_id: int, page: str = "main") -> str:
    welcome_enabled = await get_chat_setting(chat_id, "welcome_enabled", False)
    clean_welcome = await get_chat_setting(chat_id, "clean_welcome", False)
    welcome_text = await get_chat_setting(chat_id, "welcome_text", DEFAULT_WELCOME_TEXT)
    welcome_type = await get_chat_setting(chat_id, "welcome_type", "text")
    use_card = await get_chat_setting(chat_id, "welcome_use_card", True)
    has_media = bool(await get_chat_setting(chat_id, "welcome_file_id", ""))
    forcejoin_enabled = await get_chat_setting(chat_id, "force_join_enabled", False)
    forcejoin_channel = await get_chat_setting(chat_id, "force_join_channel", "")
    warn_settings = await get_warn_settings(chat_id)
    warn_limit = int(warn_settings.get("warn_limit", 3))
    warn_action = str(warn_settings.get("warn_action", "mute")).lower()

    if page == "greetings":
        return join_lines(
            "<b>Settings • Greetings</b>",
            "",
            f"Welcome: {'✅ Enabled' if welcome_enabled else '❌ Disabled'}",
            f"Default Card: {'✅ On' if use_card else '❌ Off'}",
            f"Fallback Type: <code>{welcome_type}</code>",
            f"Media Saved: {'✅' if has_media else '❌'}",
            f"Clean Welcome: {'✅ Enabled' if clean_welcome else '❌ Disabled'}",
            "",
            "<b>Welcome Caption/Text:</b>",
            welcome_text,
            "",
            "Variables: <code>{mention}</code> <code>{first}</code> <code>{fullname}</code> <code>{group_name}</code> <code>{chat_title}</code>",
        )

    if page == "moderation":
        return join_lines(
            "<b>Settings • Moderation</b>",
            "",
            f"Force Join: {'✅ Enabled' if forcejoin_enabled else '❌ Disabled'}",
            f"Force Join Channel: <code>{forcejoin_channel or 'not set'}</code>",
            f"Warn Action: <code>{warn_action}</code>",
            f"Warn Limit: <code>{warn_limit}</code>",
        )

    return join_lines(
        "<b>Group Settings Panel</b>",
        "",
        "• Greetings: welcome / clean welcome / preview",
        "• Moderation: forcejoin / warns",
    )


async def build_settings_markup(chat_id: int, page: str = "main"):
    welcome_enabled = await get_chat_setting(chat_id, "welcome_enabled", False)
    clean_welcome = await get_chat_setting(chat_id, "clean_welcome", False)
    forcejoin_enabled = await get_chat_setting(chat_id, "force_join_enabled", False)
    warn_settings = await get_warn_settings(chat_id)
    warn_limit = int(warn_settings.get("warn_limit", 3))
    warn_action = str(warn_settings.get("warn_action", "mute")).lower()
    if page == "greetings":
        return settings_greetings_keyboard(welcome_enabled=welcome_enabled, clean_welcome=clean_welcome)
    if page == "moderation":
        return settings_moderation_keyboard(forcejoin_enabled=forcejoin_enabled, warn_action=warn_action, warn_limit=warn_limit)
    return settings_main_keyboard()


async def render_settings(query: CallbackQuery | Message, page: str = "main") -> None:
    chat_id = query.message.chat.id if isinstance(query, CallbackQuery) and query.message else query.chat.id
    text = await build_settings_text(chat_id, page=page)
    markup = await build_settings_markup(chat_id, page=page)
    if isinstance(query, CallbackQuery):
        if query.message:
            await query.message.edit_text(text, reply_markup=markup)
    else:
        await query.reply(text, reply_markup=markup)


@router.message(Command("settings"))
async def settings_cmd(message: Message) -> None:
    if message.chat.type == "private":
        temp = await message.reply("ဒီ settings panel ကို group ထဲမှာ admin တွေအတွက်သုံးရပါတယ်။")
        schedule_delete(temp, 12)
        return
    if not await can_manage_settings(message):
        temp = await message.reply("ဒီ panel ကို admin တွေပဲဖွင့်လို့ရပါတယ်။")
        schedule_delete(temp, 12)
        return
    await render_settings(message, page="main")


@router.callback_query(F.data == "settings:open:main")
@router.callback_query(F.data == "settings:page:main")
async def settings_main_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return
    await render_settings(query, page="main")
    await query.answer()


@router.callback_query(F.data == "settings:page:greetings")
async def settings_greetings_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return
    await render_settings(query, page="greetings")
    await query.answer()


@router.callback_query(F.data == "settings:page:moderation")
async def settings_moderation_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return
    await render_settings(query, page="moderation")
    await query.answer()


@router.callback_query(F.data == "settings:toggle_welcome")
async def toggle_welcome_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return
    chat_id = query.message.chat.id
    current = await get_chat_setting(chat_id, "welcome_enabled", False)
    await set_chat_setting(chat_id, "welcome_enabled", not current)
    await render_settings(query, page="greetings")
    await query.answer("Welcome updated.")


@router.callback_query(F.data == "settings:toggle_cleanwelcome")
async def toggle_cleanwelcome_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return
    chat_id = query.message.chat.id
    current = await get_chat_setting(chat_id, "clean_welcome", False)
    await set_chat_setting(chat_id, "clean_welcome", not current)
    await render_settings(query, page="greetings")
    await query.answer("Clean welcome updated.")


@router.callback_query(F.data == "settings:set_welcome_text")
async def set_welcome_text_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return
    await set_state(query.message.chat.id, query.from_user.id, STATE_SET_WELCOME_TEXT, expire=600)
    await query.answer("Waiting for welcome text...")
    temp = await query.message.reply(
        "Welcome text set mode ဝင်သွားပါပြီ။\n\n"
        "အခု welcome caption/text အသစ်ကို ပို့ပါ။\n"
        "ဒီ mode မှာ text save လုပ်ရင် template card default mode ကို ဆက်သုံးမယ်။\n"
        "cancel လုပ်ချင်ရင် <code>cancel</code> ပို့ပါ။"
    )
    schedule_delete(temp, 30)


@router.callback_query(F.data == "settings:preview_welcome")
async def preview_welcome_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return

    use_card = bool(await get_chat_setting(query.message.chat.id, "welcome_use_card", True))
    template = await get_chat_setting(query.message.chat.id, "welcome_text", DEFAULT_WELCOME_TEXT)
    button_rows = await get_welcome_button_rows(query.message.chat.id)
    markup = build_welcome_keyboard(button_rows)
    caption = render_welcome_text(template, query.from_user, query.message.chat.title or "this chat")

    if use_card and settings.WELCOME_CARD_ENABLED and Path(settings.WELCOME_CARD_TEMPLATE).exists():
        try:
            fullname = " ".join(x for x in [query.from_user.first_name or "", query.from_user.last_name or ""] if x).strip() or (query.from_user.first_name or "User")
            card_text = await get_chat_setting(query.message.chat.id, "welcome_card_text", DEFAULT_CARD_TEXT)
            profile_image = await fetch_user_profile_image(query.bot, query.from_user.id)
            card_path = render_card(fullname=fullname, group_name=query.message.chat.title or "this chat", profile_image=profile_image, custom_text=card_text)
            sent = await query.message.reply_photo(FSInputFile(card_path), caption=caption, reply_markup=markup)
            schedule_delete(sent, 25)
            await query.answer("Card preview sent.")
            return
        except Exception:
            pass

    from app.modules.greetings import send_media_or_text_welcome
    sent = await send_media_or_text_welcome(query.message, query.from_user)
    schedule_delete(sent, 25)
    await query.answer("Preview sent.")


@router.callback_query(F.data == "settings:toggle_forcejoin")
async def toggle_forcejoin_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return
    chat_id = query.message.chat.id
    current = await get_chat_setting(chat_id, "force_join_enabled", False)
    await set_chat_setting(chat_id, "force_join_enabled", not current)
    await render_settings(query, page="moderation")
    await query.answer("Force join updated.")


@router.callback_query(F.data == "settings:set_forcejoin_channel")
async def set_forcejoin_channel_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return
    await set_state(query.message.chat.id, query.from_user.id, STATE_SET_FORCEJOIN, expire=300)
    await query.answer("Waiting for channel username...")
    temp = await query.message.reply("အခု <code>@channelusername</code> ကို ပို့ပါ။ ပိတ်ချင်ရင် <code>off</code> ပို့ပါ။")
    schedule_delete(temp, 30)


@router.callback_query(F.data == "settings:cycle_warnaction")
async def cycle_warnaction_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return
    chat_id = query.message.chat.id
    current = str((await get_warn_settings(chat_id)).get("warn_action", "mute")).lower()
    cycle = ["mute", "ban", "off"]
    next_action = cycle[(cycle.index(current) + 1) % len(cycle)] if current in cycle else "mute"
    await set_warn_action(chat_id, next_action)
    await render_settings(query, page="moderation")
    await query.answer(f"Warn action: {next_action}")


@router.callback_query(F.data == "settings:cycle_warnlimit")
async def cycle_warnlimit_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return
    chat_id = query.message.chat.id
    current = int((await get_warn_settings(chat_id)).get("warn_limit", 3))
    cycle = [3, 5, 10]
    next_limit = cycle[(cycle.index(current) + 1) % len(cycle)] if current in cycle else 3
    await set_warn_limit(chat_id, next_limit)
    await render_settings(query, page="moderation")
    await query.answer(f"Warn limit: {next_limit}")


@router.callback_query(F.data.startswith("settings:refresh:"))
async def settings_refresh_cb(query: CallbackQuery) -> None:
    if not query.message:
        await query.answer(); return
    if not await can_manage_settings(query):
        await query.answer("Admin only.", show_alert=True); return
    page = query.data.rsplit(":", 1)[-1]
    if page not in {"main", "greetings", "moderation"}:
        page = "main"
    await render_settings(query, page=page)
    await query.answer("Refreshed.")


@router.callback_query(F.data == "settings:close")
async def settings_close_cb(query: CallbackQuery) -> None:
    if query.message:
        try:
            await query.message.delete()
        except Exception:
            pass
    await query.answer("ပိတ်လိုက်ပါပြီ။")


@router.message(F.text)
async def settings_state_listener(message: Message) -> None:
    if message.chat.type not in {"group", "supergroup"}:
        return
    if not message.from_user:
        return
    if not await can_manage_settings(message):
        return
    state = await get_state(message.chat.id, message.from_user.id)
    if not state:
        return
    text = (message.text or "").strip()
    if not text:
        temp = await message.reply("လိုအပ်တဲ့ text ကိုပို့ပါ။")
        schedule_delete(temp, 10)
        return
    if text.lower() == "cancel":
        await clear_state(message.chat.id, message.from_user.id)
        temp = await message.reply("Settings input mode ကို ပိတ်လိုက်ပါပြီ။")
        schedule_delete(temp, 10)
        return
    if state == STATE_SET_FORCEJOIN:
        if text.lower() == "off":
            await set_chat_setting(message.chat.id, "force_join_channel", "")
            await set_chat_setting(message.chat.id, "force_join_enabled", False)
            await clear_state(message.chat.id, message.from_user.id)
            temp = await message.reply("ForceJoin channel ကိုပိတ်ပြီးပါပြီ ✅")
            schedule_delete(temp, 12)
            return
        if not text.startswith("@") or len(text) < 5:
            temp = await message.reply("မှန်ကန်တဲ့ format နဲ့ပို့ပါ။ ဥပမာ: <code>@yourchannel</code>")
            schedule_delete(temp, 12)
            return
        await set_chat_setting(message.chat.id, "force_join_channel", text)
        await set_chat_setting(message.chat.id, "force_join_enabled", True)
        await clear_state(message.chat.id, message.from_user.id)
        temp = await message.reply(join_lines("✅ <b>ForceJoin channel updated</b>", f"Channel: <code>{text}</code>", "ForceJoin ကို auto enabled လုပ်ပြီးပါပြီ။"))
        schedule_delete(temp, 15)
        return
    if state == STATE_SET_WELCOME_TEXT:
        await set_chat_setting(message.chat.id, "welcome_text", text)
        await set_chat_setting(message.chat.id, "welcome_enabled", True)
        await set_chat_setting(message.chat.id, "welcome_use_card", True)
        await clear_state(message.chat.id, message.from_user.id)
        temp = await message.reply(join_lines("✅ <b>Welcome text updated</b>", "Template card + welcome text default mode ကို သိမ်းပြီးပါပြီ။", "", "<b>Saved Text:</b>", text))
        schedule_delete(temp, 20)
