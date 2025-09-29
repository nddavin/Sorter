# multimedia_processor/api.py

import os
from fastapi import FastAPI, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .database import SessionLocal  # Your SQLAlchemy session
from .settings import UPLOAD_DIR  # Make sure this is defined in settings.py

app = FastAPI()

# Dependency to get DB session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/upload")
async def upload_file(file: UploadFile, db: Session = Depends(get_db)):
    """
    Upload a file safely to the server.
    """

    # Sanitize filename
    import re, uuid
    raw = os.path.basename(file.filename or "")
    # allow alphanumeric, dot, dash, underscore; replace anything else with '_'
    filename: str = re.sub(r"[^A-Za-z0-9._-]", "_", raw).strip("._") or f"upload-{uuid.uuid4().hex}"
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Build safe path
    # generate a unique upload path to avoid overwriting existing files
    base, ext = os.path.splitext(filename)
    upload_path: str = os.path.join(UPLOAD_DIR, filename)
    counter = 1
        CHUNK_SIZE = 1024 * 1024  # 1 MiB
        with open(upload_path, "wb") as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
    try:
        # Save file
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    # Optional: save info to DB
    # db.add(...)
    # db.commit()

    return JSONResponse(content={"message": "File uploaded successfully", "filename": filename})
