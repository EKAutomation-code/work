from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ПлюсБаллы"
    api_prefix: str = "/api"
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24

    admin_login: str
    admin_password: str

    s3_endpoint_url: str | None = None
    s3_region: str = "ru-central1"
    s3_bucket: str
    s3_access_key_id: str
    s3_secret_access_key: str

    yookassa_shop_id: str | None = None
    yookassa_secret_key: str | None = None
    cloudpayments_public_id: str | None = None
    cloudpayments_api_secret: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
