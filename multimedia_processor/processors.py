# multimedia_processor/processors.py
from .api import MediaProcessor, MediaProcessingConfig, FileMetadata, MediaType, ProcessingLevel
from typing import Any, List, Dict, Tuple, Optional
from pathlib import Path
import subprocess
import tempfile
import wave
import audioop
from PIL import Image, ImageOps
import PyPDF2
from docx import Document
import ebooklib
from ebooklib import epub
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import ffmpeg
import os
import hashlib
from datetime import datetime

class AudioProcessor(MediaProcessor):
    """Processor for audio files"""
    
    def extract_metadata(self, file_path: Path) -> FileMetadata:
        try:
            # Use ffprobe for audio metadata
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(file_path)
            ], capture_output=True, text=True)
            
            metadata = json.loads(result.stdout)
            
            return FileMetadata(
                file_path=file_path,
                file_size=file_path.stat().st_size,
                file_type=MediaType.AUDIO,
                mime_type=self._get_mime_type(file_path),
                extension=file_path.suffix.lower().lstrip('.'),
                created=datetime.fromtimestamp(file_path.stat().st_ctime),
                modified=datetime.fromtimestamp(file_path.stat().st_mtime),
                accessed=datetime.fromtimestamp(file_path.stat().st_atime),
                md5_hash=self._calculate_hash(file_path, 'md5'),
                sha256_hash=self._calculate_hash(file_path, 'sha256'),
                duration=float(metadata['format'].get('duration', 0)),
                bitrate=int(metadata['format'].get('bit_rate', 0)),
                sample_rate=int(metadata['streams'][0].get('sample_rate', 0)),
                channels=int(metadata['streams'][0].get('channels', 0)),
                codec=metadata['streams'][0].get('codec_name')
            )
        except Exception as e:
            logger.error(f"Error extracting audio metadata: {e}")
            return self._get_basic_metadata(file_path, MediaType.AUDIO)
    
    def analyze_content(self, file_path: Path, config: MediaProcessingConfig) -> Dict[str, Any]:
        analysis = {}
        
        if config.processing_level in [ProcessingLevel.STANDARD, ProcessingLevel.DEEP]:
            try:
                # Basic audio analysis
                with wave.open(str(file_path), 'rb') as wav_file:
                    analysis.update({
                        'sample_width': wav_file.getsampwidth(),
                        'frame_rate': wav_file.getframerate(),
                        'num_frames': wav_file.getnframes(),
                        'compression_type': wav_file.getcomptype()
                    })
                
                # Speech recognition for deep analysis
                if config.processing_level == ProcessingLevel.DEEP:
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(str(file_path)) as source:
                        audio_data = recognizer.record(source)
                        analysis['transcription'] = recognizer.recognize_google(audio_data)
                        
            except Exception as e:
                logger.warning(f"Audio analysis failed: {e}")
        
        return analysis
    
    def deduplicate(self, files: List[Path], config: MediaProcessingConfig) -> List[Path]:
        if config.deduplication_method == "content_hash":
            return self._deduplicate_by_content(files)
        elif config.deduplication_method == "metadata":
            return self._deduplicate_by_metadata(files)
        else:
            return self._deduplicate_by_filename(files)
    
    def convert_format(self, file_path: Path, output_format: str, config: MediaProcessingConfig) -> Path:
        output_path = config.target_directory / f"{file_path.stem}.{output_format}"
        
        try:
            subprocess.run([
                'ffmpeg', '-i', str(file_path), '-q:a', str(config.quality),
                str(output_path), '-y'
            ], check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio conversion failed: {e}")
            raise
    
    def validate_file(self, file_path: Path) -> bool:
        try:
            # Try to read the file as audio
            with wave.open(str(file_path), 'rb'):
                return True
        except:
            return False
    
    def _deduplicate_by_content(self, files: List[Path]) -> List[Path]:
        seen_hashes = set()
        unique_files = []
        
        for file_path in files:
            file_hash = self._calculate_hash(file_path, 'md5')
            if file_hash not in seen_hashes:
                seen_hashes.add(file_hash)
                unique_files.append(file_path)
        
        return unique_files

class VideoProcessor(MediaProcessor):
    """Processor for video files"""
    
    def extract_metadata(self, file_path: Path) -> FileMetadata:
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(file_path)
            ], capture_output=True, text=True)
            
            metadata = json.loads(result.stdout)
            video_stream = next((s for s in metadata['streams'] if s['codec_type'] == 'video'), {})
            
            return FileMetadata(
                file_path=file_path,
                file_size=file_path.stat().st_size,
                file_type=MediaType.VIDEO,
                mime_type=self._get_mime_type(file_path),
                extension=file_path.suffix.lower().lstrip('.'),
                created=datetime.fromtimestamp(file_path.stat().st_ctime),
                modified=datetime.fromtimestamp(file_path.stat().st_mtime),
                accessed=datetime.fromtimestamp(file_path.stat().st_atime),
                md5_hash=self._calculate_hash(file_path, 'md5'),
                sha256_hash=self._calculate_hash(file_path, 'sha256'),
                duration=float(metadata['format'].get('duration', 0)),
                dimensions=(
                    int(video_stream.get('width', 0)),
                    int(video_stream.get('height', 0))
                ),
                bitrate=int(metadata['format'].get('bit_rate', 0)),
                codec=video_stream.get('codec_name')
            )
        except Exception as e:
            logger.error(f"Error extracting video metadata: {e}")
            return self._get_basic_metadata(file_path, MediaType.VIDEO)
    
    def analyze_content(self, file_path: Path, config: MediaProcessingConfig) -> Dict[str, Any]:
        analysis = {}
        
        try:
            with VideoFileClip(str(file_path)) as video:
                analysis.update({
                    'duration': video.duration,
                    'fps': video.fps,
                    'size': video.size,
                    'rotation': video.rotation
                })
                
                if config.processing_level == ProcessingLevel.DEEP:
                    # Extract keyframes or perform scene detection
                    analysis['keyframes'] = self._extract_keyframes(file_path)
                    
        except Exception as e:
            logger.warning(f"Video analysis failed: {e}")
        
        return analysis
    
    def _extract_keyframes(self, file_path: Path) -> List[float]:
        # Simple keyframe extraction using ffmpeg
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-select_streams', 'v',
                '-show_entries', 'frame=pkt_pts_time,key_frame',
                '-of', 'csv=p=0', str(file_path)
            ], capture_output=True, text=True)
            
            keyframes = []
            for line in result.stdout.split('\n'):
                if line and ',1' in line:
                    keyframes.append(float(line.split(',')[0]))
            
            return keyframes
        except:
            return []

class DocumentProcessor(MediaProcessor):
    """Processor for document files"""
    
    def extract_metadata(self, file_path: Path) -> FileMetadata:
        basic_metadata = self._get_basic_metadata(file_path, MediaType.DOCUMENT)
        extension = file_path.suffix.lower().lstrip('.')
        
        try:
            if extension == 'pdf':
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    basic_metadata.author = pdf_reader.metadata.get('/Author')
                    basic_metadata.page_count = len(pdf_reader.pages)
                    
            elif extension in ['doc', 'docx']:
                doc = Document(file_path)
                basic_metadata.author = doc.core_properties.author
                basic_metadata.word_count = sum(len(para.text.split()) for para in doc.paragraphs)
                
        except Exception as e:
            logger.warning(f"Document metadata extraction partial: {e}")
        
        return basic_metadata
    
    def analyze_content(self, file_path: Path, config: MediaProcessingConfig) -> Dict[str, Any]:
        analysis = {}
        extension = file_path.suffix.lower().lstrip('.')
        
        try:
            if extension == 'pdf':
                analysis.update(self._analyze_pdf(file_path, config))
            elif extension in ['doc', 'docx']:
                analysis.update(self._analyze_docx(file_path, config))
            elif extension == 'txt':
                analysis.update(self._analyze_text(file_path, config))
                
        except Exception as e:
            logger.warning(f"Document analysis failed: {e}")
        
        return analysis
    
    def _analyze_pdf(self, file_path: Path, config: MediaProcessingConfig) -> Dict[str, Any]:
        analysis = {}
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            analysis['page_count'] = len(pdf_reader.pages)
            analysis['is_encrypted'] = pdf_reader.is_encrypted
            
            if config.processing_level == ProcessingLevel.DEEP:
                text_content = []
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())
                
                full_text = ' '.join(text_content)
                analysis.update(self._analyze_text_content(full_text))
        
        return analysis
    
    def _analyze_text_content(self, text: str) -> Dict[str, Any]:
        words = text.split()
        return {
            'word_count': len(words),
            'character_count': len(text),
            'line_count': text.count('\n') + 1,
            'unique_words': len(set(words)),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0
        }

class GenericMediaProcessor(MediaProcessor):
    """Generic processor for unknown file types"""
    
    def extract_metadata(self, file_path: Path) -> FileMetadata:
        return self._get_basic_metadata(file_path, MediaType.UNKNOWN)
    
    def analyze_content(self, file_path: Path, config: MediaProcessingConfig) -> Dict[str, Any]:
        return {'file_type': 'unknown', 'size': file_path.stat().st_size}
    
    def deduplicate(self, files: List[Path], config: MediaProcessingConfig) -> List[Path]:
        return self._deduplicate_by_content(files)
    
    def convert_format(self, file_path: Path, output_format: str, config: MediaProcessingConfig) -> Path:
        raise NotImplementedError("Format conversion not supported for unknown file types")
    
    def validate_file(self, file_path: Path) -> bool:
        return file_path.exists() and file_path.is_file()

# Utility methods for all processors
def _get_basic_metadata(self, file_path: Path, media_type: MediaType) -> FileMetadata:
    """Get basic file metadata"""
    stat = file_path.stat()
    return FileMetadata(
        file_path=file_path,
        file_size=stat.st_size,
        file_type=media_type,
        mime_type=self._get_mime_type(file_path),
        extension=file_path.suffix.lower().lstrip('.'),
        created=datetime.fromtimestamp(stat.st_ctime),
        modified=datetime.fromtimestamp(stat.st_mtime),
        accessed=datetime.fromtimestamp(stat.st_atime),
        md5_hash=self._calculate_hash(file_path, 'md5'),
        sha256_hash=self._calculate_hash(file_path, 'sha256')
    )

def _calculate_hash(self, file_path: Path, algorithm: str = 'md5') -> str:
    """Calculate file hash"""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def _get_mime_type(self, file_path: Path) -> str:
    """Get MIME type of file"""
    return magic.from_file(str(file_path), mime=True)