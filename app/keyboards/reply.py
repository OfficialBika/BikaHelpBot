from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def private_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/start"), KeyboardButton(text="/help")],
            [KeyboardButton(text="/about")],
        ],
        resize_keyboard=True,
        is_persistent=False,
        one_time_keyboard=False,
    )


def admin_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/help"), KeyboardButton(text="/notes")],
            [KeyboardButton(text="/warns"), KeyboardButton(text="/settings")],
        ],
        resize_keyboard=True,
        is_persistent=False,
        one_time_keyboard=False,
    )
