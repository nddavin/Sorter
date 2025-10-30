"""
Encryption utilities for file content and sensitive data.
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Optional

from .config import settings


class EncryptionManager:
    """Manages encryption/decryption operations."""

    def __init__(self, key: Optional[str] = None):
        """Initialize with encryption key."""
        if key:
            self.key = key.encode()
        else:
            self.key = settings.encryption_key.encode()

        # Ensure key is 32 bytes for Fernet
        if len(self.key) != 32:
            # Derive key if not 32 bytes
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'static_salt_for_key_derivation',
                iterations=100000,
            )
            self.key = base64.urlsafe_b64encode(kdf.derive(self.key))

        self.fernet = Fernet(self.key)

    def encrypt_data(self, data: str) -> str:
        """Encrypt string data."""
        if not data:
            return ""
        encrypted = self.fernet.encrypt(data.encode())
        return encrypted.decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        if not encrypted_data:
            return ""
        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {e}")

    def encrypt_bytes(self, data: bytes) -> bytes:
        """Encrypt bytes data."""
        return self.fernet.encrypt(data)

    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """Decrypt bytes data."""
        try:
            return self.fernet.decrypt(encrypted_data)
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {e}")


# Global encryption manager instance
encryption_manager = EncryptionManager()


def encrypt_data(data: str) -> str:
    """Convenience function to encrypt data."""
    return encryption_manager.encrypt_data(data)


def decrypt_data(encrypted_data: str) -> str:
    """Convenience function to decrypt data."""
    return encryption_manager.decrypt_data(encrypted_data)


def generate_encryption_key() -> str:
    """Generate a new encryption key."""
    return Fernet.generate_key().decode()


def validate_encryption_key(key: str) -> bool:
    """Validate if a key is a valid Fernet key."""
    try:
        Fernet(key.encode())
        return True
    except Exception:
        return False