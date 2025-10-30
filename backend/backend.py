from uuid import uuid4
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

app = FastAPI()

# Directories - Use absolute paths and validate them
UPLOAD_FOLDER = Path("uploads").resolve()
SORTED_FOLDER = Path("sorted").resolve()

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
SORTED_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".txt"}

# Import auth dependencies (will be added when multimedia_processor is integrated)
# from multimedia_processor.auth import get_current_active_user, get_db
# from multimedia_processor.models import User


@app.get("/health")
def health_check():
    return JSONResponse(content={"status": "healthy"})


def is_allowed_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


def secure_unique_filename(filename: str) -> str:
    # Strip directory components and append unique suffix
    base = Path(filename).stem
    ext = Path(filename).suffix
    return f"{base}_{uuid4().hex}{ext}"


@app.post("/sort")
async def sort_file(file: UploadFile = File(...)):
    if not file.filename or not is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    safe_filename = secure_unique_filename(file.filename)
    upload_path = (UPLOAD_FOLDER / safe_filename).resolve()
    sorted_filename = f"sorted_{safe_filename}"
    sorted_path = (SORTED_FOLDER / sorted_filename).resolve()

    # Validate paths are within allowed directories
    if not str(upload_path).startswith(str(UPLOAD_FOLDER)):
        raise HTTPException(status_code=400, detail="Invalid upload path")
    if not str(sorted_path).startswith(str(SORTED_FOLDER)):
        raise HTTPException(status_code=400, detail="Invalid sorted path")

    try:
        # Save file in chunks (1MB at a time)
        with upload_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                buffer.write(chunk)

        # Sort file contents
        with upload_path.open("r") as f:
            lines = f.readlines()
        lines.sort()
        with sorted_path.open("w") as f:
            f.writelines(lines)

        return {"sorted_file": sorted_filename}

    except Exception as e:
        # Clean up files if error occurs
        if upload_path.exists():
            upload_path.unlink()
        if sorted_path.exists():
            sorted_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )
    finally:
        await file.close()


@app.get("/download/{filename}")
def download_file(filename: str):
    # Validate filename to prevent path traversal - strict validation
    import re
    if not filename or not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Additional checks for path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Resolve and validate path to prevent traversal
    sorted_path = (SORTED_FOLDER / filename).resolve()
    if not sorted_path.exists() or not str(sorted_path).startswith(str(SORTED_FOLDER)):
        raise HTTPException(status_code=404, detail="File not found")

    # Additional security: ensure the file is actually within the sorted folder
    try:
        sorted_path.relative_to(SORTED_FOLDER)
    except ValueError:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(sorted_path)
