"""
main.py
Runs the FastAPI application.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .factory import Base, engine
from .api import router
from .auth_router import router as auth_router

# Create tables if not exist
Base.metadata.create_all(bind=engine)

# Configure allowed origins from environment variable
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5000").split(",")
    if origin.strip()
]

app = FastAPI(title="Multimedia Processor API", docs_url="/docs", redoc_url="/redoc")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api", tags=["authentication"])
app.include_router(router, prefix="/api", tags=["files"])
