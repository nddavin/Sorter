"""
config.py
App configuration and database setup.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure upload folder exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
