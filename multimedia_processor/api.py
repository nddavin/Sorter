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
    filename: str = os.path.basename(file.filename)
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Build safe path
    upload_path: str = os.path.join(UPLOAD_DIR, filename)

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
