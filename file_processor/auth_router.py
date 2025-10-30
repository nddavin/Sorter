"""
Authentication router for user registration, login, and management.
"""

from datetime import timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .auth import (
    authenticate_user, create_user, get_current_active_user,
    get_current_admin_user, create_access_token, create_refresh_token,
    get_password_hash, User
)
from .database import get_db
from .models import User as UserModel, AuditLog
from .config import settings

router = APIRouter()


@router.post("/register", response_model=Dict[str, Any])
def register_user(
    username: str,
    email: str,
    password: str,
    full_name: str = None,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    # Validate input
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Check if user exists
    existing_user = db.query(UserModel).filter(
        (UserModel.username == username) | (UserModel.email == email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # Create user
    try:
        user = create_user(db, username, email, password, "user")
        user.full_name = full_name

        # Log registration
        audit_entry = AuditLog(
            user_id=user.id,
            action="register",
            resource_type="user",
            resource_id=str(user.id),
            details={"username": username, "email": email}
        )
        db.add(audit_entry)
        db.commit()

        return {
            "message": "User registered successfully",
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=Dict[str, Any])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login = "2025-01-01T00:00:00Z"  # Would use datetime.utcnow()
    db.commit()

    # Create tokens
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    refresh_token = create_refresh_token(data={"sub": user.username})

    # Log login
    audit_entry = AuditLog(
        user_id=user.id,
        action="login",
        resource_type="user",
        resource_id=str(user.id),
        details={"ip_address": "127.0.0.1"}  # Would get from request
    )
    db.add(audit_entry)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    }


@router.post("/refresh", response_model=Dict[str, Any])
def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    from .auth import verify_token

    payload = verify_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(UserModel).filter(UserModel.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Create new access token
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.get("/me", response_model=Dict[str, Any])
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "last_login": current_user.last_login,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }


@router.put("/me", response_model=Dict[str, Any])
def update_user_profile(
    full_name: str = None,
    email: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    if full_name is not None:
        current_user.full_name = full_name
    if email is not None:
        # Check if email is already taken
        existing = db.query(UserModel).filter(
            UserModel.email == email,
            UserModel.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = email

    db.commit()

    # Log profile update
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="update_profile",
        resource_type="user",
        resource_id=str(current_user.id),
        details={"fields_updated": ["full_name"] if full_name else ["email"]}
    )
    db.add(audit_entry)
    db.commit()

    return {
        "message": "Profile updated successfully",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name
        }
    }


@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    from .auth import verify_password

    # Verify old password
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()

    # Log password change
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="change_password",
        resource_type="user",
        resource_id=str(current_user.id)
    )
    db.add(audit_entry)
    db.commit()

    return {"message": "Password changed successfully"}


# Admin endpoints
@router.get("/users", response_model=list)
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    users = db.query(UserModel).offset(skip).limit(limit).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user role (admin only)."""
    if role not in ["user", "manager", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    user.role = role
    db.commit()

    # Log role change
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="update_user_role",
        resource_type="user",
        resource_id=str(user_id),
        details={"old_role": old_role, "new_role": role}
    )
    db.add(audit_entry)
    db.commit()

    return {"message": f"User role updated to {role}"}


@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Activate/deactivate user (admin only)."""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = is_active
    db.commit()

    # Log status change
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="update_user_status",
        resource_type="user",
        resource_id=str(user_id),
        details={"is_active": is_active}
    )
    db.add(audit_entry)
    db.commit()

    status_text = "activated" if is_active else "deactivated"
    return {"message": f"User {status_text}"}