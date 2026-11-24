"""Application configuration using pydantic-settings."""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    app_secret_key: str = "dev-secret-key-change-in-production"
    app_cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    # Database (Prisma Postgres / SQLite fallback)
    database_url: str = "sqlite:///./journal_hunter.db"
    sqlite_fallback_url: str = "sqlite:///./journal_hunter.db"

    # AI Provider & Models
    ai_provider: str = "gemini"
    default_model: str = "gemini-3-flash-preview"

    # Google Gemini Keys (Multi-key load balancing / failover)
    gemini_api_key: str = ""
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""

    # DeepSeek API
    deepseek_api_key: str = ""

    # Scopus API
    scopus_api_key: str = ""
    scopus_inst_token: str = ""

    # Academic Search APIs
    crossref_email: str = "user@journalhunter.app"
    semantic_scholar_api_key: str = ""
    doaj_api_key: str = ""

    # Rate Limiting & Defaults
    max_requests_per_minute: int = 60
    max_results_per_search: int = 200
    default_max_results: int = 50
    default_year_from: int = 2020
    default_year_to: int = 2026

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def gemini_keys(self) -> List[str]:
        keys = [self.gemini_api_key, self.gemini_api_key_2, self.gemini_api_key_3]
        return [k.strip() for k in keys if k and k.strip()]

    @property
    def normalized_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"


settings = Settings()
