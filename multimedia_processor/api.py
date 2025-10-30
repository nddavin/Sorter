# multimedia_processor/api.py

import os
import logging
from fastapi import APIRouter, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import mimetypes

logger = logging.getLogger(__name__)

from .settings import UPLOAD_DIR
from .auth import get_current_active_user, get_db
from .models import User, ProcessedFile
from .processors import save_uploaded_file

router = APIRouter()

# Allowed file types
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".jpg", ".png", ".mp4", ".mp3"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def get_file_type(filename: str) -> str:
    """Determine file type from filename."""
    ext = Path(filename).suffix.lower()
    if ext in [".txt"]:
        return "text"
    elif ext in [".pdf"]:
        return "document"
    elif ext in [".docx"]:
        return "document"
    elif ext in [".jpg", ".png"]:
        return "image"
    elif ext in [".mp4"]:
        return "video"
    elif ext in [".mp3"]:
        return "audio"
    else:
        return "unknown"


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file safely to the server with user authentication.
    """
    logger.info(f"Starting upload for file: {file.filename} by user: {current_user.username}")

    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check file size by streaming
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    chunks = []
    while chunk := await file.read(chunk_size):
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        chunks.append(chunk)
    content = b''.join(chunks)

    # Sanitize filename
    import re, uuid
    raw = os.path.basename(file.filename or "")
    filename: str = re.sub(r"[^A-Za-z0-9._-]", "_", raw).strip("._") or f"upload-{uuid.uuid4().hex}"

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Build safe path
    upload_path: str = os.path.join(UPLOAD_DIR, filename)

    try:
        # Save file
        with open(upload_path, "wb") as f:
            f.write(content)

        # Create database record
        file_type = get_file_type(filename)
        db_file = ProcessedFile(
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            owner_id=current_user.id,
            content=""  # Will be processed later if needed
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        logger.info(f"File uploaded successfully: {filename} by user: {current_user.username}")

    except Exception as e:
        logger.error(f"Failed to upload file {filename}: {str(e)}")
        # Clean up file if database operation failed
        if os.path.exists(upload_path):
            os.unlink(upload_path)
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    return JSONResponse(content={
        "message": "File uploaded successfully",
        "filename": filename,
        "file_id": db_file.id,
        "file_type": file_type,
        "file_size": file_size
    })


@router.get("/files")
def get_user_files(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's uploaded files."""
    files = db.query(ProcessedFile).filter(
        ProcessedFile.owner_id == current_user.id
    ).offset(skip).limit(limit).all()

    return [
        {
            "id": f.id,
            "filename": f.filename,
            "file_type": f.file_type,
            "file_size": f.file_size,
            "upload_date": f.upload_date.isoformat(),
        }
        for f in files
    ]


@router.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a user's file."""
    file_record = db.query(ProcessedFile).filter(
        ProcessedFile.id == file_id,
        ProcessedFile.owner_id == current_user.id
    ).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete physical file
    file_path = os.path.join(UPLOAD_DIR, file_record.filename)
    if os.path.exists(file_path):
        os.unlink(file_path)

    # Delete database record
    db.delete(file_record)
    db.commit()

    logger.info(f"File deleted: {file_record.filename} by user: {current_user.username}")

    return {"message": "File deleted successfully"}
