from __future__ import annotations

from html import escape
from typing import Optional

from aiogram.types import Chat, User


def mention_html(user: Optional[User]) -> str:
    if user is None:
        return "User"
    name = full_name(user)
    return f'<a href="tg://user?id={user.id}">{escape(name)}</a>'


def full_name(user: Optional[User]) -> str:
    if user is None:
        return "User"
    parts = [user.first_name or "", user.last_name or ""]
    name = " ".join(part for part in parts if part).strip()
    return name or user.username or "User"


def chat_title(chat: Optional[Chat]) -> str:
    if chat is None:
        return "Chat"
    if getattr(chat, "title", None):
        return str(chat.title)
    first_name = getattr(chat, "first_name", None)
    last_name = getattr(chat, "last_name", None)
    parts = [first_name or "", last_name or ""]
    name = " ".join(part for part in parts if part).strip()
    return name or "Chat"


def id_html(value: int | str) -> str:
    return f"<code>{escape(str(value))}</code>"


def as_bool_emoji(value: bool) -> str:
    return "✅" if value else "❌"
