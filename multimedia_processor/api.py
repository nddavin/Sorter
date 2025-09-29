import os
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from . import settings
from .database import SessionLocal
from .models import ProcessedFile

app = FastAPI()

def save_uploaded_file(file: UploadFile) -> str:
    """Save an uploaded file safely, preventing path traversal."""
    filename = os.path.basename(file.filename)
    if not filename or filename in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid file name.")
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    upload_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    with open(upload_path, "wb") as f:
        f.write(file.file.read())
    
    return upload_path

@app.post("/upload/")
async def upload_file(file: UploadFile):
    """Upload a file and save it in the database."""
    file_path = save_uploaded_file(file)
    
    # Record in the database
    db = SessionLocal()
    try:
        processed_file = ProcessedFile(filename=file.filename, path=file_path)
        db.add(processed_file)
        db.commit()
        db.refresh(processed_file)
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
    
    return {"filename": file.filename, "path": file_path}

@app.get("/processed-files/")
async def get_processed_files():
    """Retrieve all processed files."""
    db = SessionLocal()
    try:
        files = db.query(ProcessedFile).all()
        result = [{"id": f.id, "filename": f.filename, "path": f.path} for f in files]
        return JSONResponse(content=result)
    finally:
        db.close()
