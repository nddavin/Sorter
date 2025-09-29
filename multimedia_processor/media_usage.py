from typing import Iterable
from .database import SessionLocal
from .models import ProcessedFile
from .processors import process_file_auto
