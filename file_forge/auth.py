"""
Authentication and authorization utilities with enterprise security controls.
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.responses import JSONResponse

from .config import settings
from .models import User, Session as UserSession
from .database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT
security = HTTPBearer()

# Token expiration settings (session hardening)
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens
REFRESH_TOKEN_EXPIRE_DAYS = 7
DEVICE_TOKEN_EXPIRE_DAYS = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with short expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire, 
        "type": "access",
        "iat": datetime.now(timezone.utc)
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], device_fingerprint: str = None) -> str:
    """Create JWT refresh token with device binding."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire, 
        "type": "refresh",
        "iat": datetime.now(timezone.utc)
    })
    
    # Bind to device if provided
    if device_fingerprint:
        to_encode["device_id"] = device_fingerprint
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def generate_device_fingerprint(request: Request) -> str:
    """Generate device fingerprint from request headers."""
    # Collect client identifiers
    user_agent = request.headers.get("user-agent", "")
    accept_language = request.headers.get("accept-language", "")
    accept_encoding = request.headers.get("accept-encoding", "")
    
    # Create fingerprint
    fingerprint_string = f"{user_agent}|{accept_language}|{accept_encoding}"
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]


def create_session(db: Session, user_id: int, device_fingerprint: str, ip_address: str) -> UserSession:
    """Create a new user session with device binding."""
    session = UserSession(
        user_id=user_id,
        device_fingerprint=device_fingerprint,
        ip_address=ip_address,
        expires_at=datetime.now(timezone.utc) + timedelta(days=DEVICE_TOKEN_EXPIRE_DAYS),
        is_active=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def validate_session(db: Session, session_id: int, device_fingerprint: str) -> bool:
    """Validate session exists and device matches."""
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.is_active == True
    ).first()
    
    if not session:
        return False
    
    if session.expires_at < datetime.now(timezone.utc):
        session.is_active = False
        db.commit()
        return False
    
    # Device fingerprint check
    if session.device_fingerprint != device_fingerprint:
        logger.warning(f"Session {session_id} device mismatch - possible session hijacking")
        session.is_active = False
        db.commit()
        return False
    
    return True


def rotate_refresh_token(db: Session, old_token: str, device_fingerprint: str, user_id: int) -> Tuple[str, str]:
    """Rotate refresh token for session security."""
    payload = verify_token(old_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify device matches
    if payload.get("device_id") and payload.get("device_id") != device_fingerprint:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device mismatch - please re-authenticate"
        )
    
    # Create new tokens
    new_access_token = create_access_token({"sub": payload.get("sub"), "session_id": payload.get("session_id")})
    new_refresh_token = create_refresh_token({"sub": payload.get("sub"), "session_id": payload.get("session_id")}, device_fingerprint)
    
    return new_access_token, new_refresh_token


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None,
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user with session validation."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    # Validate session if session_id in token
    session_id = payload.get("session_id")
    if session_id and request:
        device_fingerprint = generate_device_fingerprint(request)
        if not validate_session(db, session_id, device_fingerprint):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid - please re-authenticate"
            )

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (alias for get_current_user for API clarity)."""
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current admin user."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, username: str, email: str, password: str, role: str = "user", full_name: Optional[str] = None) -> User:
    """Create a new user."""
    # Check for existing username
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role,
        full_name=full_name
    )
    db.add(db_user)
    db.refresh(db_user)
    return db_user


def check_permissions(user: User, required_role: str) -> bool:
    """Check if user has required role permissions."""
    role_hierarchy = {
        "user": 1,
        "manager": 2,
        "admin": 3
    }

    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 999)

    return user_level >= required_level


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(db: Session, api_key: str) -> Optional[User]:
    """Verify API key and return associated user."""
    hashed_key = hash_api_key(api_key)
    user = db.query(User).filter(User.api_key == hashed_key).first()
    return user if user and user.is_active else None


import logging
logger = logging.getLogger(__name__)
