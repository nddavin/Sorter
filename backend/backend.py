import os
import shutil
from uuid import uuid4
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

# Directories
UPLOAD_FOLDER = Path(os.environ.get("UPLOAD_FOLDER", "uploads"))
SORTED_FOLDER = Path(os.environ.get("SORTED_FOLDER", "sorted"))
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
SORTED_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".txt"}


def is_allowed_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


def secure_unique_filename(filename: str) -> str:
    # Strip directory components and append unique suffix
    base = Path(filename).stem
    ext = Path(filename).suffix
    return f"{base}_{uuid4().hex}{ext}"


@app.post("/sort")
async def sort_file(file: UploadFile = File(...)):
    if not is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    safe_filename = secure_unique_filename(file.filename)
    upload_path = UPLOAD_FOLDER / safe_filename

    # Save uploaded file safely
    try:
        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        await file.close()

    # Sort file contents
    sorted_filename = f"sorted_{safe_filename}"
    sorted_path = SORTED_FOLDER / sorted_filename

    try:
        with upload_path.open("r") as f:
            lines = f.readlines()
        lines.sort()
        with sorted_path.open("w") as f:
            f.writelines(lines)
        
        # Clean up uploaded file after successful sorting
        upload_path.unlink()
    except Exception as e:
        # Clean up any partial files if sorting failed
        if sorted_path.exists():
            sorted_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to sort file: {str(e)}")

    return {"sorted_file": sorted_filename}


@app.get("/download/{filename}")
def download_file(filename: str):
    # Resolve and validate path to prevent traversal
    sorted_path = (SORTED_FOLDER / filename).resolve()
    if not sorted_path.exists() or SORTED_FOLDER.resolve() not in sorted_path.parents:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(sorted_path)
