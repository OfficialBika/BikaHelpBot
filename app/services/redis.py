from __future__ import annotations

from typing import Optional

from redis.asyncio import Redis

from app.config import settings


class RedisService:
    def __init__(self) -> None:
        self.client: Optional[Redis] = None

    async def connect(self) -> None:
        if not settings.redis_url:
            return
        self.client = Redis.from_url(settings.redis_url, decode_responses=True)
        await self.client.ping()

    async def close(self) -> None:
        if self.client is not None:
            await self.client.close()
            self.client = None


redis_service = RedisService()
