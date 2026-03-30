from __future__ import annotations

from aiogram.types import User


def mention_html(user: User) -> str:
    name = user.full_name or user.first_name or "User"
    return f'<a href="tg://user?id={user.id}">{name}</a>'
