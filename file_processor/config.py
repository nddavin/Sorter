"""
Configuration settings for the File Processor application.
"""

from typing import List, Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # File Storage
    upload_dir: str = "/app/uploads"
    processed_dir: str = "/app/processed"
    temp_dir: str = "/app/temp"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: List[str] = [
        ".txt", ".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png",
        ".gif", ".bmp", ".tiff", ".mp4", ".avi", ".mov", ".wmv",
        ".mp3", ".wav", ".flac", ".aac"
    ]

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "files"

    # RabbitMQ
    rabbitmq_url: str = "amqp://localhost:5672/"

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:5000"]
    allowed_credentials: bool = True
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]

    # Security
    encryption_key: str
    bcrypt_rounds: int = 12

    # Application
    app_name: str = "File Processor API"
    debug: bool = False
    version: str = "1.0.0"

    # Audit & Logging
    log_level: str = "INFO"
    enable_audit_log: bool = True
    audit_log_retention_days: int = 365

    # Performance
    max_workers: int = 4
    chunk_size: int = 8192
    cache_enabled: bool = True

    # External Services
    sentry_dsn: Optional[str] = None
    cdn_url: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()