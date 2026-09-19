import os
from typing import List, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True

    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://srmap_sage:srmap_sage_dev_secret@localhost:5432/srmap_sage_db"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://srmap_sage:srmap_sage_dev_secret@localhost:5432/srmap_sage_db"

    # Model Provider: 'gemini', 'ollama', 'openai_compatible', 'mock'
    LLM_PROVIDER: Literal["gemini", "ollama", "openai_compatible", "mock"] = "gemini"
    EMBEDDING_PROVIDER: Literal["gemini", "ollama", "mock"] = "gemini"

    # Gemini
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # GitHub Feedback
    GITHUB_REPO_OWNER: str = ""
    GITHUB_REPO_NAME: str = ""
    GITHUB_FEEDBACK_TOKEN: str = ""


settings = Settings()
