from __future__ import annotations

from typing import Optional

from aiogram.types import Message

from app.utils.helpers import chunk_text


async def reply_long_text(message: Message, text: str, disable_web_page_preview: bool = True) -> None:
    chunks = chunk_text(text, limit=4000)
    for chunk in chunks:
        await message.reply(chunk, disable_web_page_preview=disable_web_page_preview)


async def safe_edit_or_answer(message: Message, text: str, disable_web_page_preview: bool = True) -> None:
    try:
        await message.edit_text(text, disable_web_page_preview=disable_web_page_preview)
    except Exception:
        await message.answer(text, disable_web_page_preview=disable_web_page_preview)


async def delete_message_safely(message: Optional[Message]) -> bool:
    if message is None:
        return False
    try:
        await message.delete()
        return True
    except Exception:
        return False
