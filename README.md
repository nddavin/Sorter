# Multimedia Processor

The Multimedia Processor is a Python-based application designed to handle various types of multimedia files including audio, video, and documents. It allows for basic and advanced processing levels and can generate metadata, find duplicates, and convert files to specified qualities.

## Features

- **Audio Processing**: Transcribes audio files using Google Speech Recognition and provides basic or advanced processing.
- **Video Processing**: Extracts video stream information and provides basic or advanced processing.
- **Document Processing**: Extracts text from PDF and DOCX files and provides basic or advanced processing.
- **Metadata Generation**: Generates metadata for processed files.
- **Duplicate Detection**: Identifies duplicate files based on metadata.
- **File Conversion**: Converts files to a specified quality and saves them to a target directory.

## Installation

To install the necessary dependencies, you can use the following command:

```bash
pip install -r requirements.txt

Usage

Processing a Single Media File
from multimedia_processor.config import MediaProcessingConfig, ProcessingLevel, MediaType
from multimedia_processor.main import process_media

config = MediaProcessingConfig(media_type=MediaType.AUDIO, processing_level=ProcessingLevel.ADVANCED, file_path='path/to/audio/file.wav')
process_media(config)

Processing All Media Files in a Directory
from multimedia_processor.config import MediaProcessingConfig, ProcessingLevel, MediaType
from multimedia_processor.media_usage import process_directory_media

config = MediaProcessingConfig(media_type=MediaType.AUDIO, processing_level=ProcessingLevel.ADVANCED, file_path='path/to/audio/file.wav')
directory_path = Path("/path/to/media/directory")
results = process_directory_media(directory_path, config)
print("Results:", results)

Finding Duplicates
from multimedia_processor.media_usage import find_duplicates

duplicates = find_duplicates(results)
print("Duplicates:", duplicates)

Converting Files
from multimedia_processor.media_usage import convert_files

converted = convert_files(results, Path("/path/to/target/directory"), 75)
print("Converted:", converted)

Generating a Report
from multimedia_processor.media_usage import generate_report

report = generate_report(results)
print("Report:", report)

Project Structure
* config.py: Defines configuration classes for media types and processing levels.
* processors.py: Contains classes for audio, video, and document processing.
* operations.py: Similar to processors.py, contains classes for processing operations.
* main.py: Main entry point for processing a single media file.
* factory.py: Factory class to create the appropriate processor based on the media type and processing level.
* api.py: Provides a basic API for processing media.
* media_usage.py: Contains functions for processing directories, finding duplicates, converting files, and generating reports.
* requirements.txt: Lists all required dependencies for the project.

Dependencies
* python-magic
* Pillow
* PyPDF2
* python-docx
* SpeechRecognition
* moviepy
* ffmpeg-python
* tqdm
* numpy
* pandas
* ebooklib (optional)
* pydub (optional)
* imageio (optional)
* scikit-image (optional)
* concurrent futures backport (for Python <3.8)

Contributing
Contributions are welcome! Please ensure your code adheres to the project’s coding standards and includes appropriate tests.

License
This project is licensed under the MIT License. See the LICENSE file for details.
