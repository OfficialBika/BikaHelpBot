from __future__ import annotations

import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from telethon import TelegramClient

from app.config import Settings, get_settings

settings: Settings = get_settings()

bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None

mongo_client: Optional[AsyncIOMotorClient] = None
mongo_db = None

redis: Optional[Redis] = None
telethon_client: Optional[TelegramClient] = None


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def create_bot() -> Bot:
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    return Dispatcher()


def validate_startup_config() -> list[str]:
    issues: list[str] = []

    if not settings.BOT_TOKEN.strip():
        issues.append("BOT_TOKEN is missing")

    if settings.USE_WEBHOOK and not settings.WEBHOOK_HOST.strip():
        issues.append("USE_WEBHOOK=true but WEBHOOK_HOST is missing")

    if settings.USE_WEBHOOK and not settings.WEBHOOK_PATH.strip():
        issues.append("USE_WEBHOOK=true but WEBHOOK_PATH is missing")

    if settings.LOG_CHAT_ID is None:
        issues.append("LOG_CHAT_ID is not set (ticket panel logs will be disabled)")

    if not settings.has_mongo:
        issues.append("MONGODB_URI is not set")

    if not settings.has_redis:
        issues.append("REDIS_URI is not set (state/flood features may not work)")

    if not settings.has_telethon:
        issues.append("Telethon credentials missing (API_ID/API_HASH)")

    return issues


async def init_services() -> None:
    global mongo_client, mongo_db, redis, telethon_client

    logger = logging.getLogger(__name__)

    startup_issues = validate_startup_config()
    if startup_issues:
        for issue in startup_issues:
            logger.warning("Startup validation: %s", issue)

    if settings.has_mongo:
        mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
        mongo_db = mongo_client[settings.MONGODB_DB_NAME]

        from app.services.mongo import init_mongo_indexes
        await init_mongo_indexes()

        logger.info("MongoDB connected")

    if settings.has_redis:
        redis = Redis.from_url(settings.REDIS_URI, decode_responses=True)
        await redis.ping()
        logger.info("Redis connected")

    if settings.has_telethon:
        telethon_client = TelegramClient(
            settings.TELETHON_SESSION,
            settings.API_ID,
            settings.API_HASH,
        )
        await telethon_client.connect()
        logger.info("Telethon client connected")


async def close_services() -> None:
    global mongo_client, redis, telethon_client

    logger = logging.getLogger(__name__)

    if telethon_client is not None:
        await telethon_client.disconnect()
        logger.info("Telethon client disconnected")

    if redis is not None:
        await redis.aclose()
        logger.info("Redis disconnected")

    if mongo_client is not None:
        mongo_client.close()
        logger.info("MongoDB disconnected")
