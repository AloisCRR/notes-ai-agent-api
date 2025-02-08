from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


def read_file_or_value(value: Any) -> Any:
    """Read value from file if value ends with _FILE, otherwise return value."""
    if isinstance(value, str) and value.endswith("_FILE"):
        file_path = Path(value)
        if file_path.exists():
            return file_path.read_text().strip()
    return value


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str
    supabase_jwt_secret: str
    openai_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        secrets_dir="/run/secrets",
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Process each field to check for _FILE suffix
        for field in self.model_fields:
            value = getattr(self, field)
            setattr(self, field, read_file_or_value(value))


settings = Settings()
