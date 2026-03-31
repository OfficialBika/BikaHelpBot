from __future__ import annotations

from aiogram import Bot

from app.core.permissions import (
    can_delete_messages,
    can_promote_members,
    can_restrict_members,
    is_user_admin,
    is_user_creator,
)


async def user_can_delete(bot: Bot, chat_id: int, user_id: int) -> bool:
    return await can_delete_messages(bot, chat_id, user_id)


async def user_can_restrict(bot: Bot, chat_id: int, user_id: int) -> bool:
    return await can_restrict_members(bot, chat_id, user_id)


async def user_can_promote(bot: Bot, chat_id: int, user_id: int) -> bool:
    return await can_promote_members(bot, chat_id, user_id)


async def user_is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    return await is_user_admin(bot, chat_id, user_id)


async def user_is_owner(bot: Bot, chat_id: int, user_id: int) -> bool:
    return await is_user_creator(bot, chat_id, user_id)
