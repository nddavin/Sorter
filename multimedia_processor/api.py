# multimedia_processor/api.py

import os
import logging
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

from .settings import UPLOAD_DIR  # Make sure this is defined in settings.py

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile):
    """
    Upload a file safely to the server.
    """
    logger.info(f"Starting upload for file: {file.filename}")

    # Sanitize filename
    import re, uuid
    raw = os.path.basename(file.filename or "")
    # allow alphanumeric, dot, dash, underscore; replace anything else with '_'
    filename: str = re.sub(r"[^A-Za-z0-9._-]", "_", raw).strip("._") or f"upload-{uuid.uuid4().hex}"

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Build safe path
    upload_path: str = os.path.join(UPLOAD_DIR, filename)
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
