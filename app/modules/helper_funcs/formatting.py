from __future__ import annotations

from html import escape


def bold(text: str) -> str:
    return f"<b>{escape(text)}</b>"
