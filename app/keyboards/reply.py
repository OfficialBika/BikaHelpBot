from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def simple_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/start"), KeyboardButton(text="/help")]],
        resize_keyboard=True,
    )
