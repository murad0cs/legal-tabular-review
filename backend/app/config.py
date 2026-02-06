from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "Legal Tabular Review"
    app_version: str = "1.0.0"
    debug: bool = False
    
    database_url: str = "sqlite:///./legal_review.db"
    
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    
    upload_dir: Path = Path("./uploads")
    export_dir: Path = Path("./exports")
    max_file_size_mb: int = 50
    allowed_extensions: list[str] = ["pdf", "docx", "txt"]
    
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    return settings
