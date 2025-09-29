"""
models.py
SQLAlchemy models for processed files.
"""

from sqlalchemy import Column, Integer, String, Text
from factory import Base


class ProcessedFile(Base):
    __tablename__ = "processed_files"

    id = Column(Integer, primary_key=True, index=True)
    file_type = Column(String, nullable=False, default="unknown")
    content = Column(Text, nullable=False, default="")
