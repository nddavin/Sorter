"""
media_usage.py
CLI tool to process a folder of media files and store results in the DB.
"""

import os
from processors import process_file_auto
from factory import SessionLocal
from models import ProcessedFile
from config import settings


def bulk_process(folder_path: str = settings.UPLOAD_DIR):
    db = SessionLocal()
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if not os.path.isfile(file_path):
            continue
        result = process_file_auto(file_path)
        db_obj = ProcessedFile(file_type=result["type"], content=str(result["content"]))
        db.add(db_obj)
    db.commit()
    db.close()
    print("[INFO] Bulk processing complete.")


if __name__ == "__main__":
    bulk_process()
