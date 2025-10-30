"""
Security utilities for file upload and processing.
"""

import os
import re
import uuid
import hashlib
import magic
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from functools import wraps

from .config import settings

logger = logging.getLogger(__name__)


class SecurityManager:
    """Comprehensive security manager for file operations."""

    def __init__(self):
        """Initialize security manager."""
        self.allowed_extensions = set(settings.allowed_extensions)
        self.max_file_size = settings.max_file_size

        # Dangerous file signatures (file magic bytes)
        self.dangerous_signatures = {
            b'\\x4d\\x5a': 'Windows executable',  # MZ
            b'\\x7f\\x45\\x4c\\x46': 'ELF executable',  # ELF
            b'\\x23\\x21': 'Script file',  # #!
            b'\\x3c\\x3f\\x70\\x68\\x70': 'PHP file',  # <?php
            b'\\x3c\\x73\\x63\\x72\\x69\\x70\\x74': 'JavaScript/VBScript',  # <script
        }

    def validate_file_upload(self, filename: str, file_content: bytes, user_id: int) -> Dict[str, Any]:
        """
        Comprehensive file validation.

        Returns:
            Dict with validation results and sanitized filename
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'sanitized_filename': '',
            'file_info': {}
        }

        # 1. Filename validation and sanitization
        sanitized_name = self.sanitize_filename(filename)
        if not sanitized_name:
            validation_result['is_valid'] = False
            validation_result['errors'].append('Invalid filename')
            return validation_result

        validation_result['sanitized_filename'] = sanitized_name

        # 2. File extension validation
        if not self.is_allowed_extension(sanitized_name):
            validation_result['is_valid'] = False
            validation_result['errors'].append(f'File extension not allowed: {Path(sanitized_name).suffix}')
            return validation_result

        # 3. File size validation
        file_size = len(file_content)
        if file_size > self.max_file_size:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f'File too large: {file_size} bytes (max: {self.max_file_size})')
            return validation_result

        if file_size == 0:
            validation_result['is_valid'] = False
            validation_result['errors'].append('Empty file not allowed')
            return validation_result

        # 4. MIME type validation
        detected_mime = self.detect_mime_type(file_content)
        expected_mime = self.get_expected_mime_type(sanitized_name)

        if detected_mime != expected_mime:
            validation_result['warnings'].append(f'MIME type mismatch: detected {detected_mime}, expected {expected_mime}')

        # 5. Content signature validation
        if self.has_dangerous_signature(file_content):
            validation_result['is_valid'] = False
            validation_result['errors'].append('File contains potentially dangerous content')
            return validation_result

        # 6. Content analysis
        content_analysis = self.analyze_content(file_content, sanitized_name)
        validation_result['warnings'].extend(content_analysis.get('warnings', []))
        validation_result['file_info'] = content_analysis.get('info', {})

        return validation_result

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and injection."""
        if not filename or len(filename) > 255:
            return ''

        # Remove path components
        filename = os.path.basename(filename)

        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)

        # Remove leading/trailing dots and spaces
        filename = filename.strip(' .')

        # Ensure filename is not empty and doesn't start with dot
        if not filename or filename.startswith('.'):
            return ''

        # Convert to lowercase for consistency
        name_part, ext_part = os.path.splitext(filename)
        return f"{name_part.lower()}{ext_part.lower()}"

    def is_allowed_extension(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        ext = Path(filename).suffix.lower()
        return ext in self.allowed_extensions

    def detect_mime_type(self, file_content: bytes) -> str:
        """Detect MIME type from file content."""
        try:
            # Use python-magic for accurate detection
            mime = magic.Magic(mime=True)
            return mime.from_buffer(file_content)
        except Exception:
            # Fallback to mimetypes
            return 'application/octet-stream'

    def get_expected_mime_type(self, filename: str) -> str:
        """Get expected MIME type for filename."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'

    def has_dangerous_signature(self, file_content: bytes) -> bool:
        """Check for dangerous file signatures."""
        for signature, description in self.dangerous_signatures.items():
            if file_content.startswith(signature.encode().decode('unicode_escape').encode('latin1')):
                logger.warning(f"Dangerous signature detected: {description}")
                return True
        return False

    def analyze_content(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Analyze file content for additional security checks."""
        analysis = {'warnings': [], 'info': {}}

        # Check for embedded scripts in text files
        if filename.lower().endswith(('.txt', '.csv', '.json', '.xml')):
            try:
                content_str = file_content.decode('utf-8', errors='ignore')
                if '<script' in content_str.lower():
                    analysis['warnings'].append('Content contains script tags')
                if 'javascript:' in content_str.lower():
                    analysis['warnings'].append('Content contains JavaScript URLs')
            except UnicodeDecodeError:
                analysis['warnings'].append('Binary content in text file')

        # Check for suspicious patterns
        suspicious_patterns = [
            b'<iframe', b'onload=', b'onerror=', b'eval(', b'document.cookie',
            b'window.location', b'XMLHttpRequest', b'fetch('
        ]

        for pattern in suspicious_patterns:
            if pattern in file_content:
                analysis['warnings'].append(f'Potentially suspicious content detected: {pattern.decode()}')

        return analysis

    def generate_secure_filename(self, original_filename: str) -> str:
        """Generate a secure, unique filename."""
        ext = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{ext}"

    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()

    def validate_file_path(self, file_path: str, base_dir: str) -> bool:
        """Validate that file path is within allowed directory."""
        try:
            resolved_path = Path(file_path).resolve()
            base_path = Path(base_dir).resolve()
            return str(resolved_path).startswith(str(base_path))
        except Exception:
            return False


class RateLimiter:
    """Rate limiting for file uploads."""

    def __init__(self, max_uploads_per_hour: int = 100, max_size_per_hour: int = 100 * 1024 * 1024):
        """Initialize rate limiter."""
        self.max_uploads_per_hour = max_uploads_per_hour
        self.max_size_per_hour = max_size_per_hour
        self.user_stats = {}  # In production, use Redis

    def check_rate_limit(self, user_id: int, file_size: int) -> bool:
        """Check if user is within rate limits."""
        # Simplified implementation - in production, use Redis with TTL
        current_time = int(os.time() // 3600)  # Current hour

        if user_id not in self.user_stats:
            self.user_stats[user_id] = {'hour': current_time, 'uploads': 0, 'size': 0}

        stats = self.user_stats[user_id]

        # Reset stats if hour changed
        if stats['hour'] != current_time:
            stats.update({'hour': current_time, 'uploads': 0, 'size': 0})

        # Check limits
        if stats['uploads'] >= self.max_uploads_per_hour:
            return False
        if stats['size'] + file_size >= self.max_size_per_hour:
            return False

        # Update stats
        stats['uploads'] += 1
        stats['size'] += file_size

        return True


# Global instances
security_manager = SecurityManager()
rate_limiter = RateLimiter()


def require_auth(roles: Optional[List[str]] = None):
    """Decorator to require authentication and optional role check."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Authentication logic would be implemented here
            # This is a placeholder for the actual implementation
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def audit_log(action: str, resource_type: str, resource_id: Optional[str] = None):
    """Decorator to log user actions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Audit logging logic would be implemented here
            # This is a placeholder for the actual implementation
            logger.info(f"Audit: {action} on {resource_type}:{resource_id}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator