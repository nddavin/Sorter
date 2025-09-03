# multimedia_processor/api.py
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Set, Tuple, Union, Optional, TypeVar, Generic, Callable
from enum import Enum
import json
import csv
import pandas as pd
import numpy as np
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
import logging
from dataclasses import dataclass, asdict, field
from functools import wraps
import magic
import hashlib
import mimetypes

# Type variables
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediaType(Enum):
    """Supported multimedia types"""
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    IMAGE = "image"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"

class FileCategory(Enum):
    """File categories"""
    AUDIO = {
        'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'aiff'
    }
    VIDEO = {
        'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'mpeg', 'mpg'
    }
    DOCUMENT = {
        'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'xls', 'xlsx', 'ppt', 'pptx',
        'csv', 'html', 'htm', 'xml', 'json'
    }
    IMAGE = {
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg'
    }
    ARCHIVE = {
        'zip', 'rar', '7z', 'tar', 'gz'
    }

class ProcessingStrategy(Enum):
    """Processing strategies for multimedia"""
    METADATA_EXTRACTION = "metadata_extraction"
    CONTENT_ANALYSIS = "content_analysis"
    DEDUPLICATION = "deduplication"
    TRANSCODING = "transcoding"
    COMPRESSION = "compression"
    BATCH_PROCESSING = "batch_processing"

class ProcessingLevel(Enum):
    """Processing depth levels"""
    BASIC = "basic"       # File metadata only
    STANDARD = "standard" # Metadata + content analysis
    DEEP = "deep"         # Full content processing
    CUSTOM = "custom"     # Custom processing

@dataclass
class MediaProcessingConfig:
    """Configuration for multimedia processing"""
    strategy: ProcessingStrategy = ProcessingStrategy.METADATA_EXTRACTION
    processing_level: ProcessingLevel = ProcessingLevel.STANDARD
    chunk_size: int = 1024 * 1024  # 1MB chunks
    max_file_size: int = 1024 * 1024 * 500  # 500MB
    output_format: Optional[str] = None
    quality: int = 85  # For compression/transcoding
    deduplication_method: str = "content_hash"  # content_hash, metadata, filename
    preserve_metadata: bool = True
    target_directory: Optional[Path] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    parallel_processing: bool = False
    max_workers: int = 4

@dataclass
class FileMetadata:
    """Standardized file metadata"""
    file_path: Path
    file_size: int
    file_type: MediaType
    mime_type: str
    extension: str
    created: datetime
    modified: datetime
    accessed: datetime
    md5_hash: str
    sha256_hash: str
    duration: Optional[float] = None  # For audio/video
    dimensions: Optional[Tuple[int, int]] = None  # For video/images
    bitrate: Optional[int] = None  # For audio/video
    sample_rate: Optional[int] = None  # For audio
    channels: Optional[int] = None  # For audio
    codec: Optional[str] = None  # For audio/video
    author: Optional[str] = None  # For documents
    page_count: Optional[int] = None  # For documents
    word_count: Optional[int] = None  # For documents

class MediaProcessor(ABC, Generic[T]):
    """Abstract base class for media processors"""
    
    @abstractmethod
    def extract_metadata(self, file_path: Path) -> FileMetadata:
        pass
    
    @abstractmethod
    def analyze_content(self, file_path: Path, config: MediaProcessingConfig) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def deduplicate(self, files: List[Path], config: MediaProcessingConfig) -> List[Path]:
        pass
    
    @abstractmethod
    def convert_format(self, file_path: Path, output_format: str, config: MediaProcessingConfig) -> Path:
        pass
    
    @abstractmethod
    def validate_file(self, file_path: Path) -> bool:
        pass

class MediaProcessorFactory:
    """Factory for creating appropriate media processors"""
    
    @staticmethod
    def create_processor(file_path: Path) -> MediaProcessor:
        media_type = MediaProcessorFactory.detect_media_type(file_path)
        
        processors = {
            MediaType.AUDIO: AudioProcessor(),
            MediaType.VIDEO: VideoProcessor(),
            MediaType.DOCUMENT: DocumentProcessor(),
            MediaType.IMAGE: ImageProcessor(),
            MediaType.ARCHIVE: ArchiveProcessor(),
            MediaType.UNKNOWN: GenericMediaProcessor()
        }
        
        return processors.get(media_type, GenericMediaProcessor())
    
    @staticmethod
    def detect_media_type(file_path: Path) -> MediaType:
        """Detect media type from file extension"""
        extension = file_path.suffix.lower().lstrip('.')
        
        for media_type, extensions in FileCategory.__members__.items():
            if extension in extensions.value:
                return MediaType(media_type.lower())
        
        return MediaType.UNKNOWN