"""
encryption.py
Utilities for encrypting and decrypting data.
"""

from cryptography.fernet import Fernet
import os

# Load encryption key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError(
        "ENCRYPTION_KEY environment variable must be set. "
        "Generate a key using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
    )

cipher = Fernet(ENCRYPTION_KEY.encode())


def encrypt_data(data: str) -> str:
    """Encrypt a string."""
    return cipher.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt a string."""
    return cipher.decrypt(encrypted_data.encode()).decode()