# multimedia_processor/config.py
from enum import Enum

class MediaType(Enum):
    AUDIO = 1
    VIDEO = 2
    DOCUMENT = 3
    # Add more media types as needed

class ProcessingLevel(Enum):
    BASIC = 1
    ADVANCED = 2  # Add ADVANCED level

class MediaProcessingConfig:
    def __init__(self, media_type: MediaType, processing_level: ProcessingLevel, file_path: str):
        self.media_type = media_type
        self.processing_level = processing_level
        self.file_path = file_path

    @property
    def level(self):
        return self.processing_level
