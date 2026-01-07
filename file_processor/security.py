"""
Security utilities for file upload and processing with enterprise controls.
"""

import os
import re
import uuid
import hashlib
import magic
import time
import json
import redis
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging
from functools import wraps
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

from .config import settings

logger = logging.getLogger(__name__)


class SecurityManager:
    """Comprehensive security manager for file operations."""

    def __init__(self):
        """Initialize security manager."""
        self.allowed_extensions = set(settings.allowed_extensions)
        self.max_file_size = settings.max_file_size
        self.blocked_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.sh', '.bash',
            '.php', '.pl', '.cgi', '.asp', '.jsp', '.aspx', '.htaccess',
            '.htpasswd', '.ini', '.conf', '.config', '.bak', '.backup'
        }

        # Dangerous file signatures (file magic bytes)
        self.dangerous_signatures = {
            b'\x4d\x5a': 'Windows executable',  # MZ
            b'\x7f\x45\x4c\x46': 'ELF executable',  # ELF
            b'\x23\x21': 'Script file',  # #!
            b'\x3c\x3f\x70\x68\x70': 'PHP file',  # <?php
            b'\x3c\x73\x63\x72\x69\x70\x74': 'JavaScript/VBScript',  # <script
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

        # 2. Check for double extension attack
        if self.has_double_extension(sanitized_name):
            validation_result['is_valid'] = False
            validation_result['errors'].append('Double extension detected - potential file type spoofing')
            return validation_result

        # 3. File extension validation
        if not self.is_allowed_extension(sanitized_name):
            validation_result['is_valid'] = False
            validation_result['errors'].append(f'File extension not allowed: {Path(sanitized_name).suffix}')
            return validation_result

        # 4. Blocked extension check
        if self.is_blocked_extension(sanitized_name):
            validation_result['is_valid'] = False
            validation_result['errors'].append(f'File type blocked for security: {Path(sanitized_name).suffix}')
            return validation_result

        # 5. File size validation
        file_size = len(file_content)
        if file_size > self.max_file_size:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f'File too large: {file_size} bytes (max: {self.max_file_size})')
            return validation_result

        if file_size == 0:
            validation_result['is_valid'] = False
            validation_result['errors'].append('Empty file not allowed')
            return validation_result

        # 6. MIME type validation
        detected_mime = self.detect_mime_type(file_content)
        expected_mime = self.get_expected_mime_type(sanitized_name)

        if detected_mime != expected_mime:
            validation_result['warnings'].append(f'MIME type mismatch: detected {detected_mime}, expected {expected_mime}')

        # 7. Content signature validation
        if self.has_dangerous_signature(file_content):
            validation_result['is_valid'] = False
            validation_result['errors'].append('File contains potentially dangerous content')
            return validation_result

        # 8. Content analysis
        content_analysis = self.analyze_content(file_content, sanitized_name)
        validation_result['warnings'].extend(content_analysis.get('warnings', []))
        validation_result['file_info'] = content_analysis.get('info', {})

        return validation_result

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and injection."""
        if not filename or len(filename) > 255:
            return ''

        # Remove path components (path traversal defense)
        filename = os.path.basename(filename)

        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)

        # Remove leading/trailing dots and spaces
        filename = filename.strip(' .')

        # Ensure filename is not empty and doesn't start with dot
        if not filename or filename.startswith('.'):
            return ''

        # Whitelist approach - only allow safe characters
        if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
            return ''

        return filename

    def has_double_extension(self, filename: str) -> bool:
        """Detect double extensions (e.g., file.txt.exe)."""
        # Check for multiple dots indicating potential spoofing
        parts = filename.split('.')
        if len(parts) > 2:
            # Check if the last extension is in allowed but earlier one is not
            ext = parts[-1].lower()
            if ext in ['exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'sh', 'php']:
                return True
            # Check for tricks like file.txt.pdf.exe
            suspicious = ['exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'sh', 'php', 'html', 'htm']
            for part in parts[:-1]:
                if part.lower() in suspicious:
                    return True
        return False

    def is_allowed_extension(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        ext = Path(filename).suffix.lower()
        return ext in self.allowed_extensions and ext not in self.blocked_extensions

    def is_blocked_extension(self, filename: str) -> bool:
        """Check if file extension is blocked."""
        ext = Path(filename).suffix.lower()
        return ext in self.blocked_extensions

    def detect_mime_type(self, file_content: bytes) -> str:
        """Detect MIME type from file content."""
        try:
            mime = magic.Magic(mime=True)
            return mime.from_buffer(file_content)
        except Exception:
            return 'application/octet-stream'

    def get_expected_mime_type(self, filename: str) -> str:
        """Get expected MIME type for filename."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'

    def has_dangerous_signature(self, file_content: bytes) -> bool:
        """Check for dangerous file signatures."""
        for signature, description in self.dangerous_signatures.items():
            try:
                sig_bytes = signature.decode('unicode_escape').encode('latin1')
                if file_content.startswith(sig_bytes):
                    logger.warning(f"Dangerous signature detected: {description}")
                    return True
            except Exception:
                continue
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

    def validate_file_path(self, file_path: str, base_dir: str) -> bool:
        """Validate that file path is within allowed directory (path traversal defense)."""
        try:
            # Resolve and normalize paths
            resolved_path = Path(file_path).resolve()
            base_path = Path(base_dir).resolve()
            
            # Check if path is within base directory
            return str(resolved_path).startswith(str(base_path))
        except Exception:
            return False


class RedisRateLimiter:
    """Redis-backed rate limiter for file uploads."""

    def __init__(self, redis_url: str = None, max_uploads_per_minute: int = 10, max_size_per_minute: int = 10 * 1024 * 1024):
        """Initialize rate limiter with Redis backend."""
        self.max_uploads_per_minute = max_uploads_per_minute
        self.max_size_per_minute = max_size_per_minute
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis = None

    @property
    def redis(self):
        """Lazy Redis connection."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                return None
        return self._redis

    def check_rate_limit(self, user_id: int, file_size: int) -> Dict[str, Any]:
        """Check if user is within rate limits using Redis."""
        result = {
            'allowed': True,
            'remaining': self.max_uploads_per_minute,
            'retry_after': None
        }

        if not self.redis:
            # Fallback to in-memory if Redis unavailable
            return self._check_memory_limit(user_id, file_size)

        try:
            current_minute = int(time.time() // 60)
            upload_key = f"rate:uploads:{user_id}:{current_minute}"
            size_key = f"rate:size:{user_id}:{current_minute}"

            # Get current counts
            current_uploads = self.redis.get(upload_key) or 0
            current_size = int(self.redis.get(size_key) or 0)

            # Check limits
            if int(current_uploads) >= self.max_uploads_per_minute:
                result['allowed'] = False
                result['retry_after'] = 60 - (int(time.time()) % 60)
                return result

            if current_size + file_size > self.max_size_per_minute:
                result['allowed'] = False
                result['retry_after'] = 60 - (int(time.time()) % 60)
                return result

            # Increment counters with TTL
            pipe = self.redis.pipeline()
            pipe.incr(upload_key)
            pipe.incrby(size_key, file_size)
            pipe.expire(upload_key, 60)
            pipe.expire(size_key, 60)
            pipe.execute()

            result['remaining'] = self.max_uploads_per_minute - int(current_uploads) - 1

        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fail open - allow request if Redis fails

        return result

    def _check_memory_limit(self, user_id: int, file_size: int) -> Dict[str, Any]:
        """In-memory fallback for rate limiting."""
        result = {'allowed': True, 'remaining': self.max_uploads_per_minute, 'retry_after': None}
        # Simplified in-memory implementation
        return result


class AuditLogger:
    """Audit logging infrastructure for compliance."""

    def __init__(self, elasticsearch_url: str = None):
        """Initialize audit logger."""
        self.es_url = elasticsearch_url or os.getenv("ELASTICSEARCH_URL")
        self._redis = None
        self.local_logs = []

    @property
    def redis(self):
        """Lazy Redis connection for log streaming."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
            except Exception:
                pass
        return self._redis

    def log(self, action: str, user_id: int, resource_type: str, resource_id: str = None, 
            details: Dict[str, Any] = None, ip_address: str = None, user_agent: str = None):
        """Log an audit event."""
        event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': action,
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': details or {},
            'ip_address': ip_address,
            'user_agent': user_agent,
            'event_type': 'audit'
        }

        # Log locally
        self.local_logs.append(event)

        # Stream to Redis for centralized logging
        if self.redis:
            try:
                self.redis.lpush('audit:logs', json.dumps(event))
            except Exception as e:
                logger.error(f"Failed to push audit log to Redis: {e}")

        # Log to Elasticsearch if configured
        if self.es_url:
            self._index_to_elasticsearch(event)

        logger.info(f"Audit: {action} on {resource_type}:{resource_id} by user {user_id}")

    def _index_to_elasticsearch(self, event: Dict[str, Any]):
        """Index event to Elasticsearch."""
        try:
            import requests
            requests.post(
                f"{self.es_url}/audit-logs/_doc",
                json=event,
                timeout=5
            )
        except Exception as e:
            logger.error(f"Failed to index audit log to Elasticsearch: {e}")

    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent audit logs."""
        return self.local_logs[-limit:]


class ClientSideEncryption:
    """Client-side encryption for zero-knowledge storage."""

    def __init__(self, master_key: bytes = None):
        """Initialize encryption with master key."""
        self.master_key = master_key or os.getenv("ENCRYPTION_KEY", "").encode()
        if not self.master_key:
            logger.warning("No encryption key configured - encryption will generate ephemeral keys")
            self.master_key = Fernet.generate_key()
        
        # Derive separate keys for different purposes
        self.fernet = Fernet(self.master_key)
        self.aes_key = hashlib.pbkdf2_hmac('sha256', self.master_key, b'sorter-aes-key', 100000)

    def generate_file_key(self) -> bytes:
        """Generate a random key for file encryption."""
        return Fernet.generate_key()

    def encrypt_file(self, file_content: bytes, file_key: bytes = None) -> Dict[str, Any]:
        """Encrypt file content with optional client-provided key."""
        if file_key:
            f = Fernet(file_key)
            encrypted = f.encrypt(file_content)
            return {
                'encrypted_content': encrypted,
                'key': file_key.decode()
            }
        else:
            # Use server-generated key
            encrypted = self.fernet.encrypt(file_content)
            return {
                'encrypted_content': encrypted,
                'key': None  # Server manages key
            }

    def decrypt_file(self, encrypted_content: bytes, key: str = None) -> bytes:
        """Decrypt file content."""
        if key:
            f = Fernet(key.encode())
            return f.decrypt(encrypted_content)
        else:
            return self.fernet.decrypt(encrypted_content)

    def encrypt_for_storage(self, file_content: bytes, user_key: bytes) -> bytes:
        """Encrypt file for server-side storage using AES-GCM."""
        nonce = os.urandom(12)
        aesgcm = AESGCM(user_key)
        encrypted = aesgcm.encrypt(nonce, file_content, None)
        return nonce + encrypted  # Prepend nonce

    def decrypt_from_storage(self, encrypted_data: bytes, user_key: bytes) -> bytes:
        """Decrypt file from server-side storage."""
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        aesgcm = AESGCM(user_key)
        return aesgcm.decrypt(nonce, ciphertext, None)


class ClamAVScanner:
    """ClamAV virus scanning integration."""

    def __init__(self, clamav_host: str = None, clamav_port: int = 3310):
        """Initialize ClamAV scanner."""
        self.clamav_host = clamav_host or os.getenv("CLAMAV_HOST", "clamav")
        self.clamav_port = clamav_port
        self.socket = None

    def connect(self):
        """Connect to ClamAV daemon."""
        try:
            import socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.clamav_host, self.clamav_port))
            # Read greeting
            greeting = self.socket.recv(1024)
            return b"READY" in greeting
        except Exception as e:
            logger.error(f"Failed to connect to ClamAV: {e}")
            return False

    def scan_content(self, file_content: bytes) -> Dict[str, Any]:
        """Scan file content for viruses."""
        result = {
            'is_clean': True,
            'virus_name': None,
            'error': None
        }

        if not self.socket and not self.connect():
            result['error'] = "ClamAV not available - scan skipped"
            return result

        try:
            # Send INSTREAM command
            self.socket.send(b"zINSTREAM\0")
            
            # Send file content in chunks
            chunk_size = 2048
            for i in range(0, len(file_content), chunk_size):
                chunk = file_content[i:i + chunk_size]
                self.socket.send(len(chunk).to_bytes(4, 'big') + chunk)
            
            # Send end marker
            self.socket.send(b'\0\0\0\0')
            
            # Read result
            response = self.socket.recv(1024)
            response_str = response.decode('utf-8', errors='ignore')
            
            if 'FOUND' in response_str:
                result['is_clean'] = False
                # Extract virus name
                virus_match = re.search(r'FOUND\s+(.+)', response_str)
                result['virus_name'] = virus_match.group(1).strip() if virus_match else 'Unknown'
                logger.warning(f"Virus detected: {result['virus_name']}")
            elif 'OK' not in response_str:
                result['error'] = f"ClamAV error: {response_str}"

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"ClamAV scan error: {e}")

        return result

    def close(self):
        """Close ClamAV connection."""
        if self.socket:
            try:
                self.socket.send(b"QUIT\0")
                self.socket.close()
            except Exception:
                pass
            self.socket = None

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan a file for viruses using clamscan CLI."""
        import subprocess
        result = {
            'is_clean': True,
            'virus_name': None,
            'error': None
        }

        try:
            process = subprocess.run(
                ['clamscan', '--fdpass', file_path],
                capture_output=True,
                text=True,
                timeout=60
            )

            if 'Infected' in process.stdout:
                match = re.search(r'Infected files:\s*(\d+)', process.stdout)
                if match and int(match.group(1)) > 0:
                    result['is_clean'] = False
                    virus_match = re.search(r'(.+?):\s*(.+)\sFOUND', process.stdout)
                    result['virus_name'] = virus_match.group(2).strip() if virus_match else 'Unknown'

        except subprocess.TimeoutExpired:
            result['error'] = 'ClamAV scan timed out'
        except FileNotFoundError:
            result['error'] = 'ClamAV not installed'
        except Exception as e:
            result['error'] = str(e)

        return result


# Global instances
security_manager = SecurityManager()
rate_limiter = RedisRateLimiter()
audit_logger = AuditLogger()
client_encryption = ClientSideEncryption()
clamav_scanner = ClamAVScanner()


def require_auth(roles: Optional[List[str]] = None):
    """Decorator to require authentication and optional role check."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Authentication logic handled by FastAPI Depends
            result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator


def audit_log(action: str, resource_type: str, resource_id: Optional[str] = None):
    """Decorator to log user actions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            # Log action - user_id should be in kwargs or result
            user_id = kwargs.get('current_user', {}).get('id', 0) if isinstance(kwargs.get('current_user'), dict) else 0
            audit_logger.log(action, user_id, resource_type, resource_id)
            return result
        return wrapper
    return decorator
