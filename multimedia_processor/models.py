"""
models.py
SQLAlchemy models for processed files.
"""

from sqlalchemy import Column, Integer, String, Text
from .factory import Base
from .encryption import encrypt_data, decrypt_data


class ProcessedFile(Base):
    __tablename__ = "processed_files"

    id = Column(Integer, primary_key=True, index=True)
    file_type = Column(String, nullable=False, default="unknown")
    _encrypted_content = Column("content", Text, nullable=False, default="")

    @property
    def content(self) -> str:
        """Decrypt and return the content."""
        return decrypt_data(self._encrypted_content)

    @content.setter
    def content(self, value: str):
        """Encrypt and store the content."""
        self._encrypted_content = encrypt_data(value)
