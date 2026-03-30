from __future__ import annotations

from typing import Optional

from telethon import TelegramClient

from app.config import settings


class TelethonService:
    def __init__(self) -> None:
        self.client: Optional[TelegramClient] = None

    async def connect(self) -> None:
        if not settings.use_telethon:
            return
        if not settings.api_id or not settings.api_hash:
            return
        self.client = TelegramClient(settings.session_name, settings.api_id, settings.api_hash)
        await self.client.start(bot_token=settings.bot_token)

    async def close(self) -> None:
        if self.client is not None:
            await self.client.disconnect()
            self.client = None


telethon_service = TelethonService()
