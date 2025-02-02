from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str
    supabase_jwt_secret: str

    model_config = SettingsConfigDict(env_file=".env")


# Instantiate settings so it can be imported elsewhere
settings = Settings()
