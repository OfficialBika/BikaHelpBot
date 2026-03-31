from __future__ import annotations

from typing import Optional

from app.config import get_settings
from app.loader import redis

settings = get_settings()


def is_redis_available() -> bool:
    return redis is not None


def make_key(*parts: object) -> str:
    clean_parts = [str(part).strip() for part in parts if str(part).strip()]
    return f"{settings.REDIS_PREFIX}{':'.join(clean_parts)}"


async def ping_redis() -> bool:
    if redis is None:
        return False
    try:
        await redis.ping()
        return True
    except Exception:
        return False


async def set_value(key: str, value: str, expire: Optional[int] = None) -> bool:
    if redis is None:
        return False
    await redis.set(key, value, ex=expire)
    return True


async def get_value(key: str) -> Optional[str]:
    if redis is None:
        return None
    value = await redis.get(key)
    return None if value is None else str(value)


async def delete_value(key: str) -> bool:
    if redis is None:
        return False
    result = await redis.delete(key)
    return result > 0


async def increment_value(key: str, expire: Optional[int] = None) -> int:
    if redis is None:
        return 0
    value = await redis.incr(key)
    if expire:
        ttl = await redis.ttl(key)
        if ttl == -1:
            await redis.expire(key, expire)
    return int(value)


async def is_flooded(chat_id: int, user_id: int, limit: int = 8, window: int = 12) -> bool:
    if redis is None:
        return False

    key = make_key("flood", chat_id, user_id)
    current = await increment_value(key, expire=window)
    return current > limit


async def acquire_lock(name: str, expire: int = 30) -> bool:
    if redis is None:
        return True
    key = make_key("lock", name)
    return bool(await redis.set(key, "1", ex=expire, nx=True))


async def release_lock(name: str) -> bool:
    if redis is None:
        return True
    key = make_key("lock", name)
    return await delete_value(key)


async def set_state(chat_id: int, user_id: int, state: str, expire: int = 300) -> bool:
    if redis is None:
        return False
    key = make_key("state", chat_id, user_id)
    return await set_value(key, state, expire=expire)


async def get_state(chat_id: int, user_id: int) -> Optional[str]:
    if redis is None:
        return None
    key = make_key("state", chat_id, user_id)
    return await get_value(key)


async def clear_state(chat_id: int, user_id: int) -> bool:
    if redis is None:
        return False
    key = make_key("state", chat_id, user_id)
    return await delete_value(key)
