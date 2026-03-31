from __future__ import annotations

import asyncio
import importlib
import logging
from contextlib import suppress
from typing import Iterable

from aiohttp import web
from aiogram import Router
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from app.config import get_settings
from app.core.middlewares import RateLimitMiddleware, UserContextMiddleware
from app.loader import close_services, create_bot, create_dispatcher, init_services, setup_logging

MODULES: tuple[str, ...] = (
    "app.modules.start",
    "app.modules.help",
    "app.modules.misc",
    "app.modules.settings",
    "app.modules.greetings",
    "app.modules.admin",
    "app.modules.bans",
    "app.modules.blacklists",
    "app.modules.filters",
    "app.modules.forcejoin",
    "app.modules.notes",
    "app.modules.tickets",
    "app.modules.warns",
)

logger = logging.getLogger(__name__)


def iter_routers(module_paths: Iterable[str]) -> Iterable[Router]:
    for module_path in module_paths:
        try:
            module = importlib.import_module(module_path)
        except Exception as exc:
            logger.warning("Failed to import %s: %s", module_path, exc)
            continue

        router = getattr(module, "router", None)
        if isinstance(router, Router):
            yield router
        else:
            logger.warning("No router found in %s", module_path)


def build_dispatcher():
    dp = create_dispatcher()

    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())

    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())

    for router in iter_routers(MODULES):
        dp.include_router(router)

    return dp


async def on_startup(bot) -> None:
    settings = get_settings()

    if settings.USE_WEBHOOK and settings.webhook_url:
        await bot.set_webhook(
            url=settings.webhook_url,
            secret_token=settings.WEBHOOK_SECRET or None,
            drop_pending_updates=True,
        )
        logger.info("Webhook set to %s", settings.webhook_url)


async def on_shutdown(bot) -> None:
    settings = get_settings()

    if settings.USE_WEBHOOK:
        with suppress(Exception):
            await bot.delete_webhook(drop_pending_updates=False)
            logger.info("Webhook removed")


async def health_http_handler(request: web.Request) -> web.Response:
    settings = get_settings()
    return web.json_response(
        {
            "ok": True,
            "service": settings.BOT_NAME,
            "mode": "webhook" if settings.USE_WEBHOOK else "polling",
        }
    )


async def run_polling() -> None:
    bot = create_bot()
    dp = build_dispatcher()

    await init_services()

    try:
        me = await bot.get_me()
        logger.info("Bot authorized as @%s (%s)", me.username, me.id)
        logger.info("Running in polling mode")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_services()
        await bot.session.close()
        logger.info("Bot stopped")


async def run_webhook() -> None:
    settings = get_settings()

    bot = create_bot()
    dp = build_dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await init_services()

    app = web.Application()
    app.router.add_get("/healthz", health_http_handler)

    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET or None,
    )
    handler.register(app, path=settings.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        host=settings.WEB_SERVER_HOST,
        port=settings.WEB_SERVER_PORT,
    )

    me = await bot.get_me()
    logger.info("Bot authorized as @%s (%s)", me.username, me.id)
    logger.info(
        "Running in webhook mode on %s:%s%s",
        settings.WEB_SERVER_HOST,
        settings.WEB_SERVER_PORT,
        settings.WEBHOOK_PATH,
    )

    try:
        await site.start()
        while True:
            await asyncio.sleep(3600)
    finally:
        with suppress(Exception):
            await runner.cleanup()
        await close_services()
        await bot.session.close()
        logger.info("Bot stopped")


async def main() -> None:
    settings = get_settings()
    setup_logging()

    logger.info("Starting %s ...", settings.BOT_NAME)

    if settings.USE_WEBHOOK:
        await run_webhook()
    else:
        await run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
