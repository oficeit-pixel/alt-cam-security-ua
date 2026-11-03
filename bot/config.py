from functools import lru_cache
from typing import Any, List

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    enable_bot_polling: bool = Field(True, alias="ENABLE_BOT_POLLING")
    bot_token: str | None = Field(None, alias="BOT_TOKEN")
    bot_username: str = Field("AltCamSecurityUaBot", alias="BOT_USERNAME")
    database_url: str = Field(..., alias="DATABASE_URL")
    admin_chat_id: int | None = Field(None, alias="ADMIN_CHAT_ID")
    managers_chat_id: int | None = Field(None, alias="MANAGERS_CHAT_ID")
    installer_group_id: int | None = Field(None, alias="INSTALLER_GROUP_ID")
    client_group_id: int | None = Field(None, alias="CLIENT_GROUP_ID")
    client_group_url: str | None = Field(None, alias="CLIENT_GROUP_URL")
    channel_id: int | str | None = Field(None, alias="CHANNEL_ID")
    site_lead_group_id: int | None = Field(None, alias="SITE_LEAD_GROUP_ID")
    site_public_origin: str = Field(
        "https://alt-cam.net.ua",
        alias="SITE_PUBLIC_ORIGIN",
    )
    http_host: str = Field("0.0.0.0", alias="HTTP_HOST")
    http_port: int = Field(8000, alias="PORT")
    site_url: str = Field(
        "https://alt-cam.net.ua/#top",
        alias="SITE_URL",
    )
    calculator_url: str = Field(
        "https://alt-cam.net.ua/#calculator",
        alias="CALCULATOR_URL",
    )
    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")
    terms_url: str = Field(
        "https://alt-cam.net.ua/terms-of-service.html",
        alias="TERMS_URL",
    )
    privacy_url: str = Field(
        "https://alt-cam.net.ua/privacy-policy.html",
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
    google_contacts_spreadsheet_id: str | None = Field(
        None, alias="GOOGLE_CONTACTS_SPREADSHEET_ID"
    )
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
    # Order pipeline (anti-loss): see docs/ORDER_PIPELINE.md
    pipeline_enabled: bool = Field(True, alias="PIPELINE_ENABLED")
    pipeline_scheduler_enabled: bool | None = Field(None, alias="PIPELINE_SCHEDULER_ENABLED")
    second_contact_chat_id: int | None = Field(None, alias="SECOND_CONTACT_CHAT_ID")
    reminder_minutes: str = Field("5,15,60", alias="REMINDER_MINUTES")
    work_hours: str = Field("09:00-19:00", alias="WORK_HOURS")
    work_days: str = Field("0,1,2,3,4,5", alias="WORK_DAYS")
    business_timezone: str = Field("Europe/Kyiv", alias="BUSINESS_TIMEZONE")
    followup_hours: int = Field(24, alias="FOLLOWUP_HOURS")
    ship_cutoff: str = Field("13:00", alias="SHIP_CUTOFF")
    reply_eta_text: str = Field("протягом 5–10 хвилин", alias="REPLY_ETA_TEXT")
    pipeline_link_secret: str | None = Field(None, alias="PIPELINE_LINK_SECRET")
    capture_before_terms: bool = Field(True, alias="PIPELINE_CAPTURE_BEFORE_TERMS")
    faq_payment_text: str | None = Field(None, alias="FAQ_PAYMENT_TEXT")
    faq_delivery_text: str | None = Field(None, alias="FAQ_DELIVERY_TEXT")
    faq_warranty_text: str | None = Field(None, alias="FAQ_WARRANTY_TEXT")
    yugtorg_api_key: str | None = Field(None, alias="YUGTORG_API_KEY")
    yugtorg_api_base: str = Field("https://b2b.yugtorg.com/apiservices/export", alias="YUGTORG_API_BASE")
    supplier_stock_ttl_minutes: int = Field(30, alias="SUPPLIER_STOCK_TTL_MINUTES")
    np_tracking_interval_minutes: int = Field(120, alias="NP_TRACKING_INTERVAL_MINUTES")
    # Auto-registration: these Telegram usernames become owner / second contact when they press /start
    owner_usernames: str = Field("OficeITHelp", alias="OWNER_USERNAMES")
    second_contact_usernames: str = Field("uniwar", alias="SECOND_CONTACT_USERNAMES")
    # Telegram Business (bot connected to the owner's personal account)
    business_enabled: bool = Field(True, alias="BUSINESS_ENABLED")
    business_autoreply_enabled: bool = Field(True, alias="BUSINESS_AUTOREPLY_ENABLED")
    business_autoreply_text: str | None = Field(None, alias="BUSINESS_AUTOREPLY_TEXT")
    business_ignore_chat_ids: str = Field("", alias="BUSINESS_IGNORE_CHAT_IDS")
    # AI consultant "помічник ALT-CAM" (OpenAI-compatible API; disabled without a key)
    llm_api_key: str | None = Field(None, validation_alias=AliasChoices("LLM_API_KEY", "GEMINI_API_KEY"))
    llm_base_url: str = Field("https://generativelanguage.googleapis.com/v1beta/openai/", alias="LLM_BASE_URL")
    llm_model: str = Field("gemini-3.5-flash-lite", alias="LLM_MODEL")
    ai_enabled: bool = Field(True, alias="AI_ENABLED")
    ai_business_enabled: bool = Field(True, alias="AI_BUSINESS_ENABLED")
    ai_counts_as_response: bool = Field(True, alias="AI_COUNTS_AS_RESPONSE")
    ai_pause_on_owner_reply: bool = Field(True, alias="AI_PAUSE_ON_OWNER_REPLY")
    ai_min_interval_seconds: float = Field(4.0, alias="AI_MIN_INTERVAL_SECONDS")
    ai_daily_request_limit: int = Field(200, alias="AI_DAILY_REQUEST_LIMIT")
    ai_timeout_seconds: float = Field(30.0, alias="AI_TIMEOUT_SECONDS")
    ai_max_tool_rounds: int = Field(4, alias="AI_MAX_TOOL_ROUNDS")

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
        "managers_chat_id",
        "installer_group_id",
        "client_group_id",
        "site_lead_group_id",
        "second_contact_chat_id",
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


    @property
    def reminder_thresholds(self) -> list[int]:
        values = sorted({int(item) for item in self.reminder_minutes.split(",") if item.strip().isdigit()})
        return [value for value in values if value > 0][:3] or [5, 15, 60]

    @property
    def owner_chat_id(self) -> int | None:
        if self.admin_chat_id or self.admin_ids:
            return self.admin_chat_id or self.admin_ids[0]
        from bot.pipeline import contacts  # auto-registered via /start (see OWNER_USERNAMES)

        return contacts.registered_chat_id("owner")

    @property
    def second_contact_target(self) -> int | None:
        if self.second_contact_chat_id:
            return self.second_contact_chat_id
        from bot.pipeline import contacts

        return contacts.registered_chat_id("second")

    @staticmethod
    def _usernames(raw: str) -> set[str]:
        return {item.strip().lstrip("@").lower() for item in (raw or "").split(",") if item.strip()}

    def contact_role_for_username(self, username: str | None) -> str | None:
        name = (username or "").lstrip("@").lower()
        if not name:
            return None
        if name in self._usernames(self.owner_usernames):
            return "owner"
        if name in self._usernames(self.second_contact_usernames):
            return "second"
        return None

    @property
    def business_ignored_ids(self) -> set[int]:
        return {int(x) for x in self.business_ignore_chat_ids.replace(" ", "").split(",") if x.lstrip("-").isdigit()}

    @property
    def ai_active(self) -> bool:
        return bool(self.ai_enabled and self.llm_api_key and self.pipeline_enabled)

    @property
    def scheduler_active(self) -> bool:
        if self.pipeline_scheduler_enabled is not None:
            return self.pipeline_scheduler_enabled
        return self.enable_bot_polling


@lru_cache
def get_settings() -> Settings:
    return Settings()
