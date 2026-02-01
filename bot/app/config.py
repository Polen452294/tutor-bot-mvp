from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(...)

    ADMIN_IDS: str = Field(default="")

    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "tutor"
    POSTGRES_USER: str = "tutor"
    POSTGRES_PASSWORD: str = "tutor"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        # asyncpg driver
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def admin_ids(self) -> set[int]:
        raw = [x.strip() for x in self.ADMIN_IDS.split(",") if x.strip()]
        ids: set[int] = set()
        for x in raw:
            try:
                ids.add(int(x))
            except ValueError:
                pass
        return ids


settings = Settings()
