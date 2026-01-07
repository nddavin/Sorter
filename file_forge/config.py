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
    revisions_dir: str = "/app/revisions"
    backup_dir: str = "/app/backups"
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

    # Cloud Storage
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_bucket_name: Optional[str] = None
    google_credentials_file: Optional[str] = None
    google_token_file: Optional[str] = None
    azure_account_name: Optional[str] = None
    azure_account_key: Optional[str] = None
    azure_container: str = "default"

    # Notifications
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    teams_webhook_url: Optional[str] = None

    # AI/ML
    ocr_enabled: bool = True
    classification_enabled: bool = True
    auto_tagging_enabled: bool = True

    # Backups
    backup_enabled: bool = False
    backup_retention_days: int = 30
    backup_max_count: int = 100
    backup_interval_hours: int = 24

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()