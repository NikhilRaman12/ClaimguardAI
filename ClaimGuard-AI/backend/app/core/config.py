from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ClaimGuard AI"
    environment: str = "production"
    api_prefix: str = "/api"
    secret_key: str = Field(default="change-this-secret-in-env", min_length=16)
    algorithm: str = "HS256"
    access_token_minutes: int = 480
    auth_required: bool = False
    demo_actor_email: str = "operations@claimguard.ai"
    demo_actor_name: str = "ClaimGuard Operations"
    demo_actor_role: str = "admin"
    mongodb_uri: str = "mongodb://mongodb:27017"
    mongodb_database: str = "claimguard"
    cors_origins: str = "*"
    rate_limit_per_minute: int = 120
    use_mongo: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cors_allow_credentials(self) -> bool:
        return self.cors_origins != "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()
