# multimedia_processor/factory.py
from multimedia_processor.config import MediaProcessingConfig, ProcessingLevel, MediaType
from multimedia_processor.processors import AudioProcessor, VideoProcessor, DocumentProcessor

class MediaProcessorFactory:
    def create_processor(self, media_type: MediaType, processing_level: ProcessingLevel, file_path: str):
        config = MediaProcessingConfig(media_type=media_type, processing_level=processing_level, file_path=file_path)
        if media_type == MediaType.AUDIO:
            return AudioProcessor(config)
        elif media_type == MediaType.VIDEO:
            return VideoProcessor(config)
        elif media_type == MediaType.DOCUMENT:
            return DocumentProcessor(config)
        else:
            raise ValueError(f"Unsupported media type: {media_type}")
