"""
File Processor - Comprehensive file processing system with advanced security and automation.
"""

__version__ = "1.0.0"
__author__ = "File Processor Team"

# Import main components for easy access
from .main import app
from .config import settings
from .workflow_engine import workflow_engine, initialize_workflow_engine, shutdown_workflow_engine

__all__ = [
    "app",
    "settings",
    "workflow_engine",
    "initialize_workflow_engine",
    "shutdown_workflow_engine"
]