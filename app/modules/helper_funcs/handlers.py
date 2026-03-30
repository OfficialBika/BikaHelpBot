from __future__ import annotations

from aiogram import Router


def make_router(name: str) -> Router:
    router = Router(name=name)
    return router
