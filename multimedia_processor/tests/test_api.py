"""
tests/test_api.py
End-to-end tests for the Multimedia Processor API.
"""

import os
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from multimedia_processor.main import app
from multimedia_processor.factory import Base, get_db
from multimedia_processor.config import settings
from multimedia_processor.models import ProcessedFile


# --- Setup a Test Database ---
TEST_DB_URL = "sqlite:///./test_app.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Recreate tables for testing
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    # Override get_db to use test DB
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_process_file_pdf(client):
    # Create a sample PDF file in memory
    sample_pdf = io.BytesIO(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF")
    response = client.post(
        "/api/process-file/",
        files={"file": ("sample.pdf", sample_pdf, "application/pdf")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "pdf"
    assert isinstance(data["content"], str)


def test_process_file_audio(client):
    # Minimal WAV header (won't actually transcribe but should be processed)
    import wave

    fake_audio = io.BytesIO()
    with wave.open(fake_audio, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 160)  # ~10 ms of silence
    fake_audio.seek(0)
    response = client.post(
        "/api/process-file/",
        files={"file": ("sample.wav", fake_audio, "audio/wav")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "audio"
    assert "content" in data


def test_get_processed_files(client):
    response = client.get("/api/processed-files/")
    assert response.status_code == 200
    files = response.json()
    assert isinstance(files, list)
    assert len(files) > 0


def test_get_single_file(client):
    response = client.get("/api/processed-files/1")
    assert response.status_code == 200
    file_data = response.json()
    assert "file_type" in file_data
    assert "content" in file_data
