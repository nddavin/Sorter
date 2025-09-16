# multimedia_processor/api.py
from multimedia_processor.config import MediaProcessingConfig, MediaType, ProcessingLevel

class MediaProcessor:
    def __init__(self, config: MediaProcessingConfig):
        self.config = config

    def process_media(self):
        if self.config.media_type == MediaType.AUDIO:
            print("Processing audio")
        elif self.config.media_type == MediaType.VIDEO:
            print("Processing video")
        elif self.config.media_type == MediaType.DOCUMENT:
            print("Processing document")
