# multimedia_processor/main.py
from multimedia_processor.factory import MediaProcessorFactory
from multimedia_processor.config import MediaProcessingConfig, ProcessingLevel, MediaType

def process_media(config: MediaProcessingConfig) -> None:
    factory = MediaProcessorFactory()
    processor = factory.create_processor(media_type=config.media_type, processing_level=config.processing_level, file_path=config.file_path)
    result = processor.process()
    print(result)

def main():
    # Example usage of MediaProcessorFactory
    config = MediaProcessingConfig(media_type=MediaType.AUDIO, processing_level=ProcessingLevel.ADVANCED, file_path='path/to/audio/file.wav')
    process_media(config)

if __name__ == "__main__":
    main()
