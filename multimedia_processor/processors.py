import shutil
import asyncio

async def save_uploaded_file(upload_file, target_path):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _save_file_sync, upload_file, target_path)

def _save_file_sync(upload_file, target_path):
    with open(target_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f, length=1024*1024)  # 1MB chunks
