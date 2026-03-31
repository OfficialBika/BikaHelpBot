from __future__ import annotations

import re
from typing import Optional


def extract_args(text: str | None) -> str:
    if not text:
        return ""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return ""
    return parts[1].strip()


def extract_command(text: str | None) -> str:
    if not text:
        return ""
    first = text.strip().split(maxsplit=1)[0]
    return first.strip().lower()


def clean_note_name(name: str | None) -> str:
    if not name:
        return ""
    return re.sub(r"\s+", "", name.strip().lower())


def split_note(text: str | None) -> tuple[Optional[str], Optional[str]]:
    args = extract_args(text)
    if not args:
        return None, None
    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        return None, None
    return clean_note_name(parts[0]), parts[1].strip()


def human_join(items: list[str], sep: str = ", ", last_sep: str = " and ") -> str:
    clean = [item for item in items if item and item.strip()]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]}{last_sep}{clean[1]}"
    return f"{sep.join(clean[:-1])}{last_sep}{clean[-1]}"
