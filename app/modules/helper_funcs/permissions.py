from __future__ import annotations

from aiogram.types import ChatMemberAdministrator, ChatMemberOwner, Message


async def bot_is_admin(message: Message) -> bool:
    me = await message.bot.get_me()
    member = await message.bot.get_chat_member(message.chat.id, me.id)
    return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
