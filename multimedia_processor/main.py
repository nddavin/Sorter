"""
main.py
Runs the FastAPI application.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .factory import Base, engine
from .api import router

# Create tables if not exist
Base.metadata.create_all(bind=engine)

# Configure allowed origins from environment variable
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5000").split(",")

app = FastAPI(title="Multimedia Processor API", docs_url="/docs", redoc_url="/redoc")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api", tags=["media"])
