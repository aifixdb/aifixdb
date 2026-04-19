from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://aifixdb:aifixdb@localhost:5432/aifixdb"
    api_key_prefix: str = "afx_"
    admin_token: str = ""
    rate_limit_auth: int = 100  # per minute, with API key
    rate_limit_anon: int = 30  # per minute, without API key

    model_config = {"env_file": ".env"}


settings = Settings()
