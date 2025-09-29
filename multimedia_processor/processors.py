"""
processors.py

Handles multimedia file processing: audio transcription, PDF text extraction,
DOCX text extraction, MIME type detection, and video metadata retrieval.
"""

from typing import List, Dict, Union
import ffmpeg
import magic
import speech_recognition as sr
from PyPDF2 import PdfReader
from docx import Document


def process_audio_file(audio_path: str) -> str:
    recognizer: sr.Recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data: sr.AudioData = recognizer.record(source)
            text: str = recognizer.recognize_google(audio_data)
            print(f"[INFO] Transcription successful: {text[:50]}...")
            return text
    except sr.UnknownValueError:
        print("[WARNING] Could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"[ERROR] Speech Recognition API unavailable: {e}")
        return ""


def extract_pdf_text(pdf_path: str) -> str:
    reader: PdfReader = PdfReader(pdf_path)
    pages: List = reader.pages
    text: str = "\n".join(page.extract_text() or "" for page in pages)
    print(f"[INFO] Extracted {len(pages)} page(s) from PDF.")
    return text


def extract_docx_text(docx_path: str) -> str:
    doc: Document = Document(docx_path)
    paragraphs: List = doc.paragraphs
    text: str = "\n".join(para.text for para in paragraphs)
    print(f"[INFO] Extracted {len(paragraphs)} paragraph(s) from DOCX.")
    return text


def get_file_mime_type(file_path: str) -> str:
    mime = magic.Magic(mime=True)
    mime_type: str = mime.from_file(file_path)
    print(f"[INFO] Detected MIME type: {mime_type}")
    return mime_type


def get_video_info(video_path: str) -> Dict:
    try:
        info: Dict = ffmpeg.probe(video_path)
        print(f"[INFO] Video metadata retrieved for {video_path}")
        return info
    except ffmpeg.Error as e:
        print(f"[ERROR] Could not retrieve video info: {e}")
        return {}


def process_file_auto(file_path: str) -> Dict[str, Union[str, Dict]]:
    """
    Automatically detects file type and processes it using the correct function.

    Returns a standardized dictionary for API / DB use.
    """
    mime_type = get_file_mime_type(file_path)

    if mime_type.startswith("audio"):
        return {"type": "audio", "content": process_audio_file(file_path)}

    if mime_type.startswith("video"):
        return {"type": "video", "content": get_video_info(file_path)}

    if mime_type == "application/pdf":
        return {"type": "pdf", "content": extract_pdf_text(file_path)}

    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return {"type": "docx", "content": extract_docx_text(file_path)}

    if mime_type == "application/msword":
        print("[WARNING] Legacy .doc files are not supported.")
        return {"type": "unknown", "content": ""}

    return {"type": "unknown", "content": ""}
