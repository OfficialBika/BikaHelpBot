from __future__ import annotations

from html import escape
from typing import Iterable


def hbold(text: str) -> str:
    return f"<b>{escape(text)}</b>"


def hitalic(text: str) -> str:
    return f"<i>{escape(text)}</i>"


def hcode(text: str) -> str:
    return f"<code>{escape(text)}</code>"


def hpre(text: str) -> str:
    return f"<pre>{escape(text)}</pre>"


def hlink(label: str, url: str) -> str:
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def hmention(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{escape(name)}</a>'


def join_lines(*lines: str, sep: str = "\n") -> str:
    return sep.join(line for line in lines if line and line.strip())


def bullet_list(items: Iterable[str], bullet: str = "•") -> str:
    clean = [item.strip() for item in items if item and item.strip()]
    return "\n".join(f"{bullet} {item}" for item in clean)


def as_bool_emoji(value: bool) -> str:
    return "✅" if value else "❌"
