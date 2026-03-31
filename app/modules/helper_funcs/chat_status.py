from __future__ import annotations

from aiogram import Bot
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner


async def is_user_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return False
    return isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))


async def is_user_owner(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return False
    return isinstance(member, ChatMemberOwner)


async def is_bot_admin(bot: Bot, chat_id: int) -> bool:
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id, me.id)
    except Exception:
        return False
    return isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))


async def can_bot_delete_messages(bot: Bot, chat_id: int) -> bool:
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id, me.id)
    except Exception:
        return False

    if isinstance(member, ChatMemberOwner):
        return True
    if isinstance(member, ChatMemberAdministrator):
        return bool(member.can_delete_messages)
    return False


async def can_bot_restrict_members(bot: Bot, chat_id: int) -> bool:
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id, me.id)
    except Exception:
        return False

    if isinstance(member, ChatMemberOwner):
        return True
    if isinstance(member, ChatMemberAdministrator):
        return bool(member.can_restrict_members)
    return False
