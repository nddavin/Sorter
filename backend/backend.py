from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import shutil

app = FastAPI()

UPLOAD_FOLDER = "uploads"
SORTED_FOLDER = "sorted"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SORTED_FOLDER, exist_ok=True)

def sort_file(input_path: str, output_path: str):
    """Reads a text file, sorts lines, writes to output_path."""
    try:
        with open(input_path, "r") as f:
            lines = f.readlines()
        lines.sort()
        with open(output_path, "w") as f:
            f.writelines(lines)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sorting failed: {e}")

@app.post("/sort")
async def sort_upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    # Save uploaded file
    upload_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Sort file
    sorted_filename = f"sorted_{file.filename}"
    sorted_path = os.path.join(SORTED_FOLDER, sorted_filename)
    sort_file(upload_path, sorted_path)

    return {"sorted_file": sorted_filename}

@app.get("/download/{filename}")
def download_file(filename: str):
    sorted_path = os.path.join(SORTED_FOLDER, filename)
    if not os.path.exists(sorted_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(sorted_path, media_type="text/plain", filename=filename)

@app.get("/")
def root():
    return {"message": "Backend is running"}
