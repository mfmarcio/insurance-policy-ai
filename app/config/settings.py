from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"
    llm_mode: str = "ollama"
    database_path: Path = Path("data/policies.db")
    upload_dir: Path = Path("data/uploads")
    processed_dir: Path = Path("data/processed")
    ocr_language: str = "por"
    max_chars_per_chunk: int = 6000
    chunk_overlap: int = 500
    top_k_chunks: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def ensure_directories(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
