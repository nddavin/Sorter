"""
main.py
Runs the FastAPI application.
"""

from fastapi import FastAPI
-from factory import Base, engine
from .factory import Base, engine
from .api import router

# Create tables if not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multimedia Processor API")
app.include_router(router, prefix="/api", tags=["media"])
