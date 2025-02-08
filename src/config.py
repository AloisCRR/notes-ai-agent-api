from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    notes_ai_agent_database_url: str
    notes_ai_agent_gemini_api_key: str
    notes_ai_agent_supabase_jwt_secret: str
    notes_ai_agent_openai_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        secrets_dir="/run/secrets",
    )


settings = Settings()
