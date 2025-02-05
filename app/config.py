from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str
    supabase_jwt_secret: str
    openai_api_key: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
