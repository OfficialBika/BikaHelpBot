from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import get_settings

settings = get_settings()


def start_keyboard() -> InlineKeyboardMarkup:
    bot_link = (
        f"https://t.me/{settings.BOT_USERNAME}?startgroup=true"
        if settings.BOT_USERNAME
        else "https://t.me"
    )
    updates_link = (
        f"https://t.me/{settings.UPDATE_CHANNEL.lstrip('@')}"
        if settings.UPDATE_CHANNEL
        else "https://t.me"
    )
    owner_link = (
        f"https://t.me/{settings.OWNER_USERNAME.lstrip('@')}"
        if settings.OWNER_USERNAME
        else "https://t.me/Official_Bika"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Add Me", url=bot_link),
                InlineKeyboardButton(text="ℹ️ Help", callback_data="help:open"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Settings", callback_data="settings:open:main"),
                InlineKeyboardButton(text="📢 Updates", url=updates_link),
            ],
            [InlineKeyboardButton(text="👤 Owner", url=owner_link)],
        ]
    )


def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👮 Admin", callback_data="help:admin"),
                InlineKeyboardButton(text="👋 Greetings", callback_data="help:greetings"),
            ],
            [
                InlineKeyboardButton(text="📝 Notes", callback_data="help:notes"),
                InlineKeyboardButton(text="⚠️ Warns", callback_data="help:warns"),
            ],
            [
                InlineKeyboardButton(text="🔙 Back", callback_data="help:back"),
                InlineKeyboardButton(text="❌ Close", callback_data="help:close"),
            ],
        ]
    )


def close_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Close", callback_data="close")]])


def settings_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👋 Greetings", callback_data="settings:page:greetings"),
                InlineKeyboardButton(text="🛡 Moderation", callback_data="settings:page:moderation"),
            ],
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data="settings:refresh:main"),
                InlineKeyboardButton(text="❌ Close", callback_data="settings:close"),
            ],
        ]
    )


def settings_greetings_keyboard(welcome_enabled: bool, clean_welcome: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Welcome {'✅' if welcome_enabled else '❌'}",
                    callback_data="settings:toggle_welcome",
                ),
                InlineKeyboardButton(
                    text=f"Clean {'✅' if clean_welcome else '❌'}",
                    callback_data="settings:toggle_cleanwelcome",
                ),
            ],
            [
                InlineKeyboardButton(text="Set Welcome Text", callback_data="settings:set_welcome_text"),
                InlineKeyboardButton(text="Preview Welcome", callback_data="settings:preview_welcome"),
            ],
            [
                InlineKeyboardButton(text="🔙 Back", callback_data="settings:page:main"),
                InlineKeyboardButton(text="🔄 Refresh", callback_data="settings:refresh:greetings"),
            ],
            [InlineKeyboardButton(text="❌ Close", callback_data="settings:close")],
        ]
    )


def settings_moderation_keyboard(forcejoin_enabled: bool, warn_action: str, warn_limit: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"ForceJoin {'✅' if forcejoin_enabled else '❌'}",
                    callback_data="settings:toggle_forcejoin",
                ),
            ],
            [
                InlineKeyboardButton(text="Set ForceJoin Channel", callback_data="settings:set_forcejoin_channel"),
            ],
            [
                InlineKeyboardButton(
                    text=f"Warn Action: {warn_action.upper()}",
                    callback_data="settings:cycle_warnaction",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"Warn Limit: {warn_limit}",
                    callback_data="settings:cycle_warnlimit",
                ),
            ],
            [
                InlineKeyboardButton(text="🔙 Back", callback_data="settings:page:main"),
                InlineKeyboardButton(text="🔄 Refresh", callback_data="settings:refresh:moderation"),
            ],
            [InlineKeyboardButton(text="❌ Close", callback_data="settings:close")],
        ]
    )


def ticket_admin_keyboard(ticket_id: str, is_closed: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if not is_closed:
        rows.append(
            [
                InlineKeyboardButton(text="💬 Reply", callback_data=f"ticket:reply:{ticket_id}"),
                InlineKeyboardButton(text="✅ Close", callback_data=f"ticket:close:{ticket_id}"),
            ]
        )

    rows.append([InlineKeyboardButton(text="🔄 Refresh", callback_data=f"ticket:refresh:{ticket_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
