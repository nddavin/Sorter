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
    _encrypted_content = Column("content", Text, nullable=True, default=None)

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
