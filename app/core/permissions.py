from __future__ import annotations

from aiogram.types import ChatMemberAdministrator, ChatMemberOwner, Message


async def is_user_admin(message: Message) -> bool:
    if not message.chat or not message.from_user:
        return False
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
