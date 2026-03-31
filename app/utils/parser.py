from __future__ import annotations

from typing import Optional


def remove_command(text: str | None) -> str:
    if not text:
        return ""
    parts = text.strip().split(maxsplit=1)
    if not parts or len(parts) == 1:
        return ""
    return parts[1].strip()


def split_once(text: str | None, sep: str = " ") -> tuple[str, str]:
    if not text:
        return "", ""
    parts = text.split(sep, 1)
    if len(parts) == 1:
        return parts[0].strip(), ""
    return parts[0].strip(), parts[1].strip()


def parse_note_name_and_text(text: str | None) -> tuple[Optional[str], Optional[str]]:
    body = remove_command(text)
    if not body:
        return None, None

    head, tail = split_once(body)
    if not head or not tail:
        return None, None

    return head.strip().lower(), tail.strip()


def parse_int(value: str | None) -> Optional[int]:
    if not value:
        return None
    value = value.strip()
    if not value.lstrip("-").isdigit():
        return None
    return int(value)
