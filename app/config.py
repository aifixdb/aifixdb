from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://aifixdb:aifixdb@localhost:5432/aifixdb"
    api_key_prefix: str = "afx_"
    admin_token: str = ""
    rate_limit_auth: int = 100  # per minute, with API key
    rate_limit_anon: int = 30  # per minute, without API key
    # SES email
    smtp_host: str = "email-smtp.eu-central-1.amazonaws.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_sender: str = "noreply@nocodework.io"
    # Public URL for verification links
    public_url: str = "https://aifixdb.nocodework.pl"

    model_config = {"env_file": ".env"}


settings = Settings()
