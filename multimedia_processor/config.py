"""Configuration module for multimedia processor."""
from enum import Enum
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


class MediaType(Enum):
    """Supported media types."""
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    IMAGE = "image"


class ProcessingLevel(Enum):
    """Processing complexity levels."""
    BASIC = "basic"
    ADVANCED = "advanced"


@dataclass
class MediaProcessingConfig:
    """Configuration for media processing operations."""
    media_type: MediaType
    processing_level: ProcessingLevel
    file_path: str
    output_dir: Optional[str] = None
    quality: int = 75
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not Path(self.file_path).exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if self.quality < 1 or self.quality > 100:
            raise ValueError("Quality must be between 1 and 100")
    
    @property
    def level(self) -> ProcessingLevel:
        """Backward compatibility property."""
        return self.processing_level
