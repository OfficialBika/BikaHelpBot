from __future__ import annotations

import asyncio
from typing import Optional

from aiogram.types import CallbackQuery, Message, User


def get_full_name(user: Optional[User]) -> str:
    if user is None:
        return "User"

    parts = [user.first_name or "", user.last_name or ""]
    full_name = " ".join(part for part in parts if part).strip()
    return full_name or user.username or "User"


def get_display_name(user: Optional[User]) -> str:
    if user is None:
        return "User"
    return user.first_name or get_full_name(user)


def extract_chat_id(event: Message | CallbackQuery) -> Optional[int]:
    if isinstance(event, CallbackQuery):
        if event.message:
            return event.message.chat.id
        return None
    return event.chat.id if event.chat else None


def extract_user_id(event: Message | CallbackQuery) -> Optional[int]:
    user = getattr(event, "from_user", None)
    return user.id if user else None


def is_command_text(text: str | None) -> bool:
    return bool(text and text.strip().startswith("/"))


def chunk_text(text: str, limit: int = 4000) -> list[str]:
    text = text or ""
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""

    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= limit:
            current = paragraph
            continue

        for line in paragraph.split("\n"):
            candidate = f"{current}\n{line}".strip() if current else line
            if len(candidate) <= limit:
                current = candidate
                continue

            if current:
                chunks.append(current)
                current = ""

            if len(line) <= limit:
                current = line
                continue

            words = line.split(" ")
            temp = ""
            for word in words:
                candidate = f"{temp} {word}".strip() if temp else word
                if len(candidate) <= limit:
                    temp = candidate
                else:
                    if temp:
                        chunks.append(temp)
                    temp = word
            if temp:
                current = temp

    if current:
        chunks.append(current)

    return chunks or [text]


async def delete_message_after(message: Optional[Message], delay: int = 15) -> None:
    if message is None:
        return

    await asyncio.sleep(delay)

    try:
        await message.delete()
    except Exception:
        pass


def schedule_delete(message: Optional[Message], delay: int = 15) -> None:
    if message is None:
        return
    asyncio.create_task(delete_message_after(message, delay))
