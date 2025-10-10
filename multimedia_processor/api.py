# multimedia_processor/api.py

import os
import logging
from fastapi import APIRouter, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Generator

logger = logging.getLogger(__name__)

from .database import SessionLocal  # Your SQLAlchemy session
from .settings import UPLOAD_DIR  # Make sure this is defined in settings.py

router = APIRouter()

# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload")
async def upload_file(file: UploadFile, db: Session = Depends(get_db)):
    """
    Upload a file safely to the server.
    """
    logger.info(f"Starting upload for file: {file.filename}")

    # Sanitize filename
    import re, uuid
    raw = os.path.basename(file.filename or "")
    # allow alphanumeric, dot, dash, underscore; replace anything else with '_'
    filename: str = re.sub(r"[^A-Za-z0-9._-]", "_", raw).strip("._") or f"upload-{uuid.uuid4().hex}"
    if not filename:
        logger.warning("Invalid filename provided")
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Build safe path
    # generate a unique upload path to avoid overwriting existing files
    upload_path: str = os.path.join(UPLOAD_DIR, filename)

    # Save file in chunks
    try:
        CHUNK_SIZE = 1024 * 1024  # 1 MiB
        with open(upload_path, "wb") as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
        logger.info(f"File uploaded successfully: {filename}")
    except Exception as e:
        logger.error(f"Failed to upload file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    # Optional: save info to DB
    # db.add(...)
    # db.commit()

    return JSONResponse(content={"message": "File uploaded successfully", "filename": filename})
