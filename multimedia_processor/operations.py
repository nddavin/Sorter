# multimedia_processor/operations.py
from multimedia_processor.config import MediaProcessingConfig, ProcessingLevel, MediaType
import ffmpeg
import magic
import speech_recognition
from PyPDF2 import PdfReader
import docx
from typing import Dict

class AudioProcessor:
    def __init__(self, config: MediaProcessingConfig):
        self.config = config

    def process_audio(self) -> Dict[str, str]:
        if self.config.level == ProcessingLevel.ADVANCED:
            print("Advanced audio processing")
        else:
            print("Basic audio processing")

        recognizer = speech_recognition.Recognizer()
        with speech_recognition.AudioFile(self.config.file_path) as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio)
                print(text)
                return {'hash': self.get_hash(), 'text': text}
            except speech_recognition.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
                return {'hash': self.get_hash(), 'text': 'UnknownValueError'}
            except speech_recognition.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
                return {'hash': self.get_hash(), 'text': str(e)}

    def get_hash(self) -> str:
        # Example hash function using magic
        return magic.from_file(self.config.file_path)

    def process(self) -> Dict[str, str]:
        return self.process_audio()

class VideoProcessor:
    def __init__(self, config: MediaProcessingConfig):
        self.config = config

    def process_video(self) -> Dict[str, str]:
        if self.config.level == ProcessingLevel.ADVANCED:
            print("Advanced video processing")
        else:
            print("Basic video processing")

        video_stream = ffmpeg.probe(self.config.file_path)
        print(video_stream)
        return {'hash': self.get_hash(), 'video_stream': video_stream}

    def get_hash(self) -> str:
        # Example hash function using magic
        return magic.from_file(self.config.file_path)

    def process(self) -> Dict[str, str]:
        return self.process_video()

class DocumentProcessor:
    def __init__(self, config: MediaProcessingConfig):
        self.config = config

    def process_document(self) -> Dict[str, str]:
        if self.config.level == ProcessingLevel.ADVANCED:
            print("Advanced document processing")
        else:
            print("Basic document processing")

        if self.config.file_path.endswith('.pdf'):
            pdf_reader = PdfReader(self.config.file_path)
            pages = pdf_reader.pages
            text = "".join([page.extract_text() for page in pages])
            print(text)
            return {'hash': self.get_hash(), 'text': text}
        elif self.config.file_path.endswith('.docx'):
            doc = docx.Document(self.config.file_path)
            paragraphs = doc.paragraphs
            text = "\n".join([para.text for para in paragraphs])
            print(text)
            return {'hash': self.get_hash(), 'text': text}
        else:
            raise ValueError("Unsupported file format for document processing")

    def get_hash(self) -> str:
        # Example hash function using magic
        return magic.from_file(self.config.file_path)

    def process(self) -> Dict[str, str]:
        return self.process_document()
