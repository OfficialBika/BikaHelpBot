from __future__ import annotations

from typing import Any, Optional

from telethon import functions

from app.loader import telethon_client


def is_telethon_available() -> bool:
    return telethon_client is not None


async def get_me() -> Optional[Any]:
    if telethon_client is None:
        return None
    try:
        return await telethon_client.get_me()
    except Exception:
        return None


async def is_user_in_chat(chat: Any, user_id: int) -> bool:
    if telethon_client is None:
        return False

    try:
        participant = await telethon_client(
            functions.channels.GetParticipantRequest(channel=chat, participant=user_id)
        )
        return participant is not None
    except Exception:
        return False


async def get_chat_member(chat: Any, user_id: int) -> Optional[Any]:
    if telethon_client is None:
        return None

    try:
        return await telethon_client(
            functions.channels.GetParticipantRequest(channel=chat, participant=user_id)
        )
    except Exception:
        return None


async def export_invite_link(chat: Any) -> Optional[str]:
    if telethon_client is None:
        return None

    try:
        result = await telethon_client(functions.messages.ExportChatInviteRequest(peer=chat))
        return getattr(result, "link", None)
    except Exception:
        return None


async def resolve_entity(entity: Any) -> Optional[Any]:
    if telethon_client is None:
        return None

    try:
        return await telethon_client.get_entity(entity)
    except Exception:
        return None
