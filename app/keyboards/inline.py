from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Help", callback_data="help:main")
    kb.button(text="Rules", callback_data="rules:show")
    kb.adjust(2)
    return kb.as_markup()


def close_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Close", callback_data="close")
    return kb.as_markup()
