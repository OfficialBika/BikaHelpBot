from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(default="", alias="BOT_USERNAME")
    owner_id: int = Field(default=0, alias="OWNER_ID")

    mongo_uri: str = Field(default="", alias="MONGO_URI")
    mongo_db_name: str = Field(default="rose_bika", alias="MONGO_DB_NAME")
    redis_url: str = Field(default="", alias="REDIS_URL")

    api_id: int = Field(default=0, alias="API_ID")
    api_hash: str = Field(default="", alias="API_HASH")
    session_name: str = Field(default="rose_bika_raw", alias="SESSION_NAME")
    use_telethon: bool = Field(default=False, alias="USE_TELETHON")

    start_img: str = Field(default="", alias="START_IMG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    tz: str = Field(default="Asia/Bangkok", alias="TZ")

    webhook_enabled: bool = Field(default=False, alias="WEBHOOK_ENABLED")
    webhook_host: str = Field(default="0.0.0.0", alias="WEBHOOK_HOST")
    webhook_port: int = Field(default=8080, alias="WEBHOOK_PORT")
    webhook_path: str = Field(default="/webhook", alias="WEBHOOK_PATH")
    webhook_domain: str = Field(default="", alias="WEBHOOK_DOMAIN")

    channel_username: str = Field(default="", alias="CHANNEL_USERNAME")
    owner_username: str = Field(default="", alias="OWNER_USERNAME")


settings = Settings()
