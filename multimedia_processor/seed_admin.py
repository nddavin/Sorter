"""
seed_admin.py
Populates DB with sample processed files for testing after migration.
"""

import os
from .config import settings

# Copy some sample files to uploads folder
# (You can manually drop test files: sample.pdf, sample.mp3, sample.docx, sample.mp4)

if not os.listdir(settings.UPLOAD_DIR):
    print("[INFO] Please add test files to the uploads folder before seeding.")
else:
    print("[INFO] Processing sample files...")
    # bulk_process(settings.UPLOAD_DIR)  # TODO: Implement bulk processing
