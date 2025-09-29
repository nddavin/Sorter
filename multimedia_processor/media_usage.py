from .database import SessionLocal
from .models import ProcessedFile
from .file_processor import process_file_auto

def process_files(file_paths):
    db = SessionLocal()
    try:
        for file_path in file_paths:
            result = process_file_auto(file_path)
            db.add(result)
        db.commit()
    except Exception as e:
        db.rollback()  # Preserve transactional integrity
        raise
    finally:
        db.close()  # Always close the session
