# examples/media_usage.py
from multimedia_processor.main import UniversalMediaProcessor, process_media, process_directory_media
from multimedia_processor.api import MediaProcessingConfig, ProcessingLevel, ProcessingStrategy
from pathlib import Path
from datetime import datetime

# Initialize processor
processor = UniversalMediaProcessor()

# Example 1: Process a single audio file
audio_file = Path("music/song.mp3")
result = processor.process_file(audio_file)
print("Audio file processed:", result['metadata']['duration'])

# Example 2: Process with deep analysis
config = MediaProcessingConfig(
    processing_level=ProcessingLevel.DEEP,
    preserve_metadata=True
)
deep_result = processor.process_file(audio_file, config)
print("Deep analysis:", deep_result['content_analysis'])

# Example 3: Process entire directory
music_dir = Path("music/")
results = processor.process_directory(music_dir)
print(f"Processed {len(results)} files")

# Example 4: Find duplicates
duplicates = processor.find_duplicates(music_dir)
print("Found duplicates:", duplicates)

# Example 5: Convert audio files
mp3_files = list(music_dir.glob("*.mp3"))
converted = processor.convert_files(mp3_files, "flac")
print("Converted files:", converted)

# Example 6: Generate comprehensive report
report_file = Path(f"media_report_{datetime.now():%Y%m%d}.json")
processor.generate_report(music_dir, report_file)
print(f"Report generated: {report_file}")

# Example 7: Using shortcut functions
quick_result = process_media(audio_file, processing_level="standard")
print("Quick processing result:", quick_result)

# Example 8: Process video files
video_file = Path("videos/movie.mp4")
video_result = processor.process_file(video_file)
print("Video dimensions:", video_result['metadata']['dimensions'])

# Example 9: Process documents
doc_file = Path("documents/report.pdf")
doc_result = processor.process_file(doc_file)
print("Document page count:", doc_result['metadata']['page_count'])