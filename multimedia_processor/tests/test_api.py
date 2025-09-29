import pytest
from io import BytesIO
from PyPDF2 import PdfWriter
from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def create_minimal_pdf_bytes():
    """Generate a minimal valid PDF as BytesIO."""
    pdf_bytes = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes

def test_upload_valid_pdf():
    """Test uploading a valid PDF file."""
    pdf_file = create_minimal_pdf_bytes()
    files = {"file": ("test.pdf", pdf_file, "application/pdf")}
    
    response = client.post("/upload/", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert data["filename"] == "test.pdf"
    assert "path" in data

def test_get_processed_files():
    """Test retrieving processed files using a seeded POST request."""
    # Seed the database by uploading a file
    pdf_file = create_minimal_pdf_bytes()
    files = {"file": ("seed.pdf", pdf_file, "application/pdf")}
    upload_response = client.post("/upload/", files=files)
    assert upload_response.status_code == 200
    
    # Now GET processed-files
    response = client.get("/processed-files/")
