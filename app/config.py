from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://aifixdb:aifixdb@localhost:5432/aifixdb"
    api_key_prefix: str = "afx_"

    model_config = {"env_file": ".env"}


settings = Settings()
