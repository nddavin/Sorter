from .database import SessionLocal
from .models import ProcessedFile
++ b/multimedia_processor/media_usage.py
@@ -1,5 +1,5 @@
from typing import Iterable
from .database import SessionLocal
from .models import ProcessedFile
from .processors import process_file_auto

def process_files(file_paths: Iterable[str]) -> int:
    db = SessionLocal()
    processed = 0
    try:
        for file_path in file_paths:
            result = process_file_auto(file_path)  # {'type': ..., 'content': ...}
            record = ProcessedFile(
                file_type=result.get("type", "unknown"),
                content=result.get("content", ""),
            )
            db.add(record)
            processed += 1
        db.commit()
        return processed
    except Exception:
        db.rollback()  # Preserve transactional integrity
        raise
    finally:
        db.close()  # Always close the session
        db.rollback()  # Preserve transactional integrity
        raise
    finally:
        db.close()  # Always close the session
