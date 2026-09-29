from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import ClassVar

class Settings(BaseSettings):
    DEVELOPMENT_SECRET_KEY: ClassVar[str] = "dev_secret_key_super_secure_and_long_enough_for_jwt_sha256_cine_random"

    ENVIRONMENT: str = "development"
    ALLOW_DEMO_AUTH: bool = False
    SECRET_KEY: str = DEVELOPMENT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    DATABASE_URL: str = "sqlite:///./cine_random.db"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://cine-random.vercel.app",
        "https://cinerandomseven.vercel.app",
    ]
    CORS_ORIGIN_REGEX: str = r"^https:\/\/.*\.vercel\.app$"
    GOOGLE_CLIENT_ID: str = ""
    UPSTASH_REDIS_REST_URL: str | None = None
    UPSTASH_REDIS_REST_TOKEN: str | None = None

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.ENVIRONMENT.strip().lower() != "production":
            return self

        if len(self.SECRET_KEY.encode("utf-8")) < 32 or self.SECRET_KEY == self.DEVELOPMENT_SECRET_KEY:
            raise ValueError("SECRET_KEY must be a strong, production-specific secret")
        if not self.GOOGLE_CLIENT_ID.strip():
            raise ValueError("GOOGLE_CLIENT_ID is required in production")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()


