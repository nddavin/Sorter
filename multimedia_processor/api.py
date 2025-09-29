"""
api.py
Defines routes for file upload and retrieval.
"""

import shutil
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from processors import process_file_auto
from multimedia_processor.models import ProcessedFile
from factory import get_db
from config import settings

router = APIRouter()


@router.post("/process-file/")
async def process_file(file: UploadFile, db: Session = Depends(get_db)):
    # Save uploaded file to disk
    file_path = f"{settings.UPLOAD_DIR}/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = process_file_auto(file_path)

    # Save result to DB
    db_obj = ProcessedFile(file_type=result["type"], content=str(result["content"]))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    return {"id": db_obj.id, "file_type": db_obj.file_type, "content": db_obj.content}


@router.get("/processed-files/")
def list_processed_files(db: Session = Depends(get_db)):
    files = db.query(ProcessedFile).all()
    return files


@router.get("/processed-files/{file_id}")
def get_processed_file(file_id: int, db: Session = Depends(get_db)):
    obj = db.query(ProcessedFile).filter(ProcessedFile.id == file_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="File not found")
    return obj
