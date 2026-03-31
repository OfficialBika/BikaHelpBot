from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    BOT_TOKEN: str = Field(..., min_length=10)
    BOT_USERNAME: str = ""
    BOT_NAME: str = "Bika Help Bot"
    OWNER_ID: int = 0
    OWNER_USERNAME: str = ""

    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    USE_WEBHOOK: bool = False
    WEBHOOK_HOST: str = ""
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_SECRET: str = ""
    WEB_SERVER_HOST: str = "0.0.0.0"
    WEB_SERVER_PORT: int = 8080

    MONGODB_URI: str = ""
    MONGODB_DB_NAME: str = "bika_help_bot"

    REDIS_URI: str = ""
    REDIS_PREFIX: str = "bikahelp:"

    API_ID: Optional[int] = None
    API_HASH: str = ""
    TELETHON_SESSION: str = "bikahelpbot"

    SUPPORT_CHAT_ID: Optional[int] = None
    LOG_CHAT_ID: Optional[int] = None
    UPDATE_CHANNEL: str = ""
    FORCE_JOIN_CHANNEL: str = ""
    START_PHOTO_URL: str = ""
    TIMEZONE: str = "Asia/Bangkok"

    WELCOME_CARD_ENABLED: bool = True
    WELCOME_CARD_TEMPLATE: str = "assets/welcome_card_template.png"
    WELCOME_CARD_FONT_MYANMAR: str = "/usr/share/fonts/truetype/noto/NotoSansMyanmar-Regular.ttf"
    WELCOME_CARD_FONT_LATIN: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    WELCOME_CARD_OUTPUT_DIR: str = "tmp/welcome_cards"

    @field_validator("WEBHOOK_PATH")
    @classmethod
    def validate_webhook_path(cls, value: str) -> str:
        if not value:
            return "/webhook"
        return value if value.startswith("/") else f"/{value}"

    @field_validator("LOG_LEVEL")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper().strip()

    @property
    def webhook_url(self) -> str:
        if not self.WEBHOOK_HOST:
            return ""
        return f"{self.WEBHOOK_HOST.rstrip('/')}{self.WEBHOOK_PATH}"

    @property
    def has_mongo(self) -> bool:
        return bool(self.MONGODB_URI.strip())

    @property
    def has_redis(self) -> bool:
        return bool(self.REDIS_URI.strip())

    @property
    def has_telethon(self) -> bool:
        return bool(self.API_ID and self.API_HASH.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
