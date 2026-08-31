"""Centralised, environment-driven configuration.

All configuration is read from environment variables (or a local `.env`).
Nothing here is secret by default — real secrets are injected at deploy time.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    # ── App ────────────────────────────────────────────────
    project_name: str = Field("Kaushal AI", alias="KAUSHAI_PROJECT_NAME")
    env: str = Field("development", alias="KAUSHAI_ENV")
    debug: bool = Field(True, alias="KAUSHAI_DEBUG")
    api_prefix: str = Field("/api/v1", alias="KAUSHAI_API_PREFIX")
    log_level: str = Field("INFO", alias="KAUSHAI_LOG_LEVEL")

    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8000, alias="PORT")

    # ── Database ───────────────────────────────────────────
    database_url: Optional[str] = Field(None, alias="DATABASE_URL")

    # ── Security ───────────────────────────────────────────
    secret_key: str = Field("dev-insecure-secret-key-change-me", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(14, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")

    # NoDecode: keep pydantic-settings from JSON-decoding the raw env value so a
    # plain comma-separated string works (parsed by the validator below).
    cors_origins: Annotated[List[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="CORS_ORIGINS",
    )

    # ── Supabase ───────────────────────────────────────────
    supabase_url: Optional[str] = Field(None, alias="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(None, alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(None, alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_secret: Optional[str] = Field(None, alias="SUPABASE_JWT_SECRET")
    supabase_storage_bucket: str = Field("kaushai-media", alias="SUPABASE_STORAGE_BUCKET")

    # ── Redis ──────────────────────────────────────────────
    redis_url: Optional[str] = Field(None, alias="REDIS_URL")

    # ── AI providers ───────────────────────────────────────
    ai_stt_provider: str = Field("mock", alias="AI_STT_PROVIDER")
    ai_llm_provider: str = Field("mock", alias="AI_LLM_PROVIDER")
    ai_tts_provider: str = Field("mock", alias="AI_TTS_PROVIDER")
    ai_translate_provider: str = Field("mock", alias="AI_TRANSLATE_PROVIDER")

    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    sarvam_api_key: Optional[str] = Field(None, alias="SARVAM_API_KEY")
    groq_api_key: Optional[str] = Field(None, alias="GROQ_API_KEY")
    bhashini_api_key: Optional[str] = Field(None, alias="BHASHINI_API_KEY")
    bhashini_user_id: Optional[str] = Field(None, alias="BHASHINI_USER_ID")

    recommendation_weights_file: Optional[str] = Field(None, alias="RECOMMENDATION_WEIGHTS_FILE")

    seed_admin_email: str = Field("admin@kaushai.gov.in", alias="SEED_ADMIN_EMAIL")
    seed_admin_password: str = Field("Admin@2026", alias="SEED_ADMIN_PASSWORD")

    # ── Validators ─────────────────────────────────────────
    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            if v.strip().startswith("["):
                return json.loads(v)
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # ── Derived ────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            url = self.database_url
            # normalise the common "postgres://" style to the psycopg2 driver
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://") and "+psycopg2" not in url:
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url
        # Local dev fallback — zero-config SQLite
        return f"sqlite:///{BASE_DIR / 'kaushai_dev.db'}"

    @property
    def using_sqlite(self) -> bool:
        return self.sqlalchemy_database_uri.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
