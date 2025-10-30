"""
models.py
SQLAlchemy models for processed files and users.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .factory import Base
from .encryption import encrypt_data, decrypt_data


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="user")  # admin, user, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to processed files
    processed_files = relationship("ProcessedFile", back_populates="owner")


class ProcessedFile(Base):
    __tablename__ = "processed_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False, default="unknown")
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    _encrypted_content = Column("content", Text, nullable=True, default=None)

    # Relationship to user
    owner = relationship("User", back_populates="processed_files")

    @property
    def content(self) -> str:
        """Decrypt and return the content."""
        if self._encrypted_content is None:
            return ""
        try:
            return decrypt_data(self._encrypted_content)
        except Exception as e:
            raise ValueError(f"Failed to decrypt content for file {self.id}: {e}")

    @content.setter
    def content(self, value: str | None):
        """Encrypt and store the content."""
        if value is None or value == "":
            self._encrypted_content = None
        else:
            try:
                self._encrypted_content = encrypt_data(value)
            except Exception as e:
                raise ValueError(f"Failed to encrypt content: {e}")
