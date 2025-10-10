"""
encryption.py
Utilities for encrypting and decrypting data.
"""

from cryptography.fernet import Fernet
import os
from .config import settings

# Generate or load encryption key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # In production, this should be set via environment variable
    # For development, generate a key (but warn)
    print("WARNING: ENCRYPTION_KEY not set, generating a temporary key. Set ENCRYPTION_KEY in production.")
    ENCRYPTION_KEY = Fernet.generate_key().decode()

cipher = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)


def encrypt_data(data: str) -> str:
    """Encrypt a string."""
    return cipher.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt a string."""
    return cipher.decrypt(encrypted_data.encode()).decode()