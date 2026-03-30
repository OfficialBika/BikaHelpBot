from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from fastapi import FastAPI, Request
import uvicorn

from app.config import settings
from app.loader import create_bot, create_dispatcher
from app.services.mongo import mongo
from app.services.redis import redis_service
from app.services.telethon_client import telethon_service
from app.utils.logger import setup_logging


async def on_startup() -> None:
    await mongo.connect()
    with suppress(Exception):
        await redis_service.connect()
    with suppress(Exception):
        await telethon_service.connect()


async def on_shutdown(bot) -> None:
    with suppress(Exception):
        await bot.session.close()
    with suppress(Exception):
        await telethon_service.close()
    with suppress(Exception):
        await redis_service.close()
    with suppress(Exception):
        await mongo.close()


async def run_polling() -> None:
    bot = create_bot()
    dp = create_dispatcher()
    await on_startup()
    try:
        me = await bot.get_me()
        logging.info("Bot started as @%s", me.username)
        await dp.start_polling(bot)
    finally:
        await on_shutdown(bot)


app = FastAPI(title="Rose Bika Bot")


@app.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post(settings.webhook_path)
async def telegram_webhook(request: Request) -> dict[str, bool]:
    # Minimal placeholder so the structure is webhook-ready.
    await request.body()
    return {"ok": True}


def main() -> None:
    setup_logging(settings.log_level)
    if settings.webhook_enabled:
        uvicorn.run(app, host=settings.webhook_host, port=settings.webhook_port)
        return
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()
