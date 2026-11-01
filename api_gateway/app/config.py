from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE: int = 86400
    CORS_ORIGINS: str = "*"
    TIMEZONE: str = "Europe/Moscow"

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/orion.db"

    DEMO_PHONE: str = "79000000001"
    DEMO_PASSWORD: str = "orion2026"

    CONCIERGE_PHONE: str = "79000000002"
    CONCIERGE_PASSWORD: str = "orion2026"

    UJIN_RESIDENT_PHONE: str = ""
    UJIN_RESIDENT_PASSWORD: str = ""

    UJIN_API_BASE: str = "https://api-uae-test.ujin.tech/api"
    UJIN_APARTMENT_ID: int = 2761
    UJIN_UST: str = ""
    UJIN_PUBLISH_CLASS: str = "integrations_devices"
    UJIN_PUBLISH_ENABLED: bool = False
    UJIN_PUBLISH_INTERVAL_S: float = 5.0

    EMULATOR_TICK_S: float = 5.0

    GIGACHAT_AUTH_KEY: str = ""


settings = Settings()
