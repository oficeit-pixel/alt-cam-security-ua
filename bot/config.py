from functools import lru_cache
from typing import Any, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    bot_username: str = Field("AltCamSecurityUaBot", alias="BOT_USERNAME")
    database_url: str = Field(..., alias="DATABASE_URL")
    admin_chat_id: int = Field(..., alias="ADMIN_CHAT_ID")
    installer_group_id: int = Field(..., alias="INSTALLER_GROUP_ID")
    client_group_id: int | None = Field(None, alias="CLIENT_GROUP_ID")
    client_group_url: str | None = Field(None, alias="CLIENT_GROUP_URL")
    channel_id: int | str | None = Field(None, alias="CHANNEL_ID")
    site_lead_group_id: int | None = Field(None, alias="SITE_LEAD_GROUP_ID")
    site_public_origin: str = Field(
        "https://oficeit-pixel.github.io",
        alias="SITE_PUBLIC_ORIGIN",
    )
    http_host: str = Field("0.0.0.0", alias="HTTP_HOST")
    http_port: int = Field(8000, alias="PORT")
    site_url: str = Field(
        "https://oficeit-pixel.github.io/alt-cam-security-ua/#top",
        alias="SITE_URL",
    )
    calculator_url: str = Field(
        "https://oficeit-pixel.github.io/alt-cam-security-ua/#calculator",
        alias="CALCULATOR_URL",
    )
    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")
    terms_url: str = Field(
        "https://oficeit-pixel.github.io/alt-cam-security-ua/terms-of-service.html",
        alias="TERMS_URL",
    )
    privacy_url: str = Field(
        "https://oficeit-pixel.github.io/alt-cam-security-ua/privacy-policy.html",
        alias="PRIVACY_URL",
    )
    google_service_account_json: str | None = Field(
        None, alias="GOOGLE_SERVICE_ACCOUNT_JSON"
    )
    google_drive_folder_id: str | None = Field(None, alias="GOOGLE_DRIVE_FOLDER_ID")
    media_retention_days: int = Field(14, alias="MEDIA_RETENTION_DAYS")
    auto_create_db: bool = Field(False, alias="AUTO_CREATE_DB")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: str | int | list[int] | None) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, int):
            return [value]
        if isinstance(value, list):
            return value
        return [int(item.strip()) for item in value.split(",") if item.strip()]

    @field_validator("client_group_id", "site_lead_group_id", mode="before")
    @classmethod
    def parse_optional_int(cls, value: Any) -> int | None:
        if value is None or value == "":
            return None
        return int(value)

    @field_validator("channel_id", mode="before")
    @classmethod
    def parse_optional_channel_id(cls, value: Any) -> int | str | None:
        if value is None or value == "":
            return None
        if isinstance(value, int):
            return value
        text = str(value).strip()
        if text.lstrip("-").isdigit():
            return int(text)
        return text


@lru_cache
def get_settings() -> Settings:
    return Settings()
