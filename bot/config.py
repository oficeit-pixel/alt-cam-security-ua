from functools import lru_cache
from typing import Any, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str | None = Field(None, alias="BOT_TOKEN")
    bot_username: str = Field("AltCamSecurityUaBot", alias="BOT_USERNAME")
    database_url: str = Field(..., alias="DATABASE_URL")
    admin_chat_id: int | None = Field(None, alias="ADMIN_CHAT_ID")
    installer_group_id: int | None = Field(None, alias="INSTALLER_GROUP_ID")
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
    google_service_account_file: str = Field(
        "/etc/secrets/google-service-account.json",
        alias="GOOGLE_SERVICE_ACCOUNT_FILE",
    )
    google_drive_folder_id: str | None = Field(None, alias="GOOGLE_DRIVE_FOLDER_ID")
    ukrposhta_api_url: str = Field("https://www.ukrposhta.ua/ecom/0.0.1", alias="UKRPOSHTA_API_URL")
    ukrposhta_tracking_token: str | None = Field(None, alias="UKRPOSHTA_TRACKING_TOKEN")
    imap_host: str = Field("imap.gmail.com", alias="IMAP_HOST")
    imap_port: int = Field(993, alias="IMAP_PORT")
    imap_user: str | None = Field(None, alias="IMAP_USER")
    imap_password: str | None = Field(None, alias="IMAP_PASSWORD")
    imap_folder: str = Field("INBOX", alias="IMAP_FOLDER")
    supplier_email_senders: str | None = Field(None, alias="SUPPLIER_EMAIL_SENDERS")
    media_retention_days: int = Field(14, alias="MEDIA_RETENTION_DAYS")
    auto_create_db: bool = Field(True, alias="AUTO_CREATE_DB")
    admin_web_email: str = Field("altcam777@gmail.com", alias="ADMIN_WEB_EMAIL")
    admin_web_password: str | None = Field(None, alias="ADMIN_WEB_PASSWORD")
    admin_session_secret: str | None = Field(None, alias="ADMIN_SESSION_SECRET")
    admin_site_url: str = Field("https://alt-cam.net.ua/admin/", alias="ADMIN_SITE_URL")
    smtp_host: str = Field("smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(587, alias="SMTP_PORT")
    smtp_user: str = Field("altcam.ua@gmail.com", alias="SMTP_USER")
    smtp_password: str | None = Field(None, alias="SMTP_PASSWORD")
    smtp_from: str = Field("ALT-CAM Security UA <altcam.ua@gmail.com>", alias="SMTP_FROM")
    email_relay_url: str | None = Field(None, alias="EMAIL_RELAY_URL")
    email_relay_secret: str | None = Field(None, alias="EMAIL_RELAY_SECRET")
    nova_poshta_api_key: str | None = Field(None, alias="NOVA_POSHTA_API_KEY")

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

    @field_validator(
        "admin_chat_id",
        "installer_group_id",
        "client_group_id",
        "site_lead_group_id",
        mode="before",
    )
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
