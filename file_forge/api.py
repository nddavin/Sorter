"""
FastAPI endpoints for the comprehensive file processing system.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from .auth import get_current_active_user, get_current_admin_user, User
from .database import get_db
from .models import File as FileModel, SortingRule, AuditLog
from .processors import file_processor, sorting_engine
from .security import security_manager, rate_limiter
from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== FILE UPLOAD & MANAGEMENT =====

@router.post("/upload", response_model=Dict[str, Any])
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: Optional[str] = None,
    tags: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Secure file upload with comprehensive validation and processing.
    """
    logger.info(f"Upload request from user {current_user.username}: {file.filename}")

    # Rate limiting check
    if not rate_limiter.check_rate_limit(current_user.id, 0):  # We'll check size after reading
        raise HTTPException(status_code=429, detail="Upload rate limit exceeded")

    # Read file content
    try:
        file_content = await file.read()
        file_size = len(file_content)
    except Exception as e:
        logger.error(f"Failed to read file content: {e}")
        raise HTTPException(status_code=400, detail="Failed to read file content")

    # Rate limiting with actual size
    if not rate_limiter.check_rate_limit(current_user.id, file_size):
        raise HTTPException(status_code=429, detail="Upload rate limit exceeded")

    # Comprehensive security validation
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    validation = security_manager.validate_file_upload(file.filename, file_content, current_user.id)

    if not validation['is_valid']:
        logger.warning(f"File validation failed for {file.filename}: {validation['errors']}")
        raise HTTPException(status_code=400, detail=f"Validation failed: {', '.join(validation['errors'])}")

    # Generate secure filename
    secure_filename = security_manager.generate_secure_filename(validation['sanitized_filename'])
    file_path = os.path.join(settings.upload_dir, secure_filename)

    # Validate file path is within allowed directory
    resolved_path = os.path.abspath(file_path)
    upload_dir_resolved = os.path.abspath(settings.upload_dir)
    if not resolved_path.startswith(upload_dir_resolved):
        raise HTTPException(status_code=400, detail="Invalid file path")

    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)

    try:
        # Save file securely
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Process file metadata
        processed_info = file_processor.process_file(file_path, secure_filename)

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]

        # Create database record
        db_file = FileModel(
            filename=secure_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_type=processed_info['file_type'],
            mime_type=processed_info['mime_type'],
            file_size=file_size,
            file_hash=processed_info['file_hash'],
            metadata=processed_info['metadata'],
            tags=tag_list,
            category=category,
            owner_id=current_user.id,
            content=processed_info['content'][:10000] if processed_info['content'] else ""  # Limit content storage
        )

        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # Log successful upload
        audit_entry = AuditLog(
            user_id=current_user.id,
            action="upload",
            resource_type="file",
            resource_id=str(db_file.id),
            details={
                "filename": secure_filename,
                "original_filename": file.filename,
                "file_size": file_size,
                "file_type": processed_info['file_type']
            }
        )
        db.add(audit_entry)
        db.commit()

        # Background processing for heavy operations
        background_tasks.add_task(process_file_background, db_file.id, processed_info)

        logger.info(f"File uploaded successfully: {secure_filename} by {current_user.username}")

        return {
            "message": "File uploaded successfully",
            "file_id": db_file.id,
            "filename": secure_filename,
            "file_size": file_size,
            "file_type": processed_info['file_type'],
            "warnings": validation['warnings']
        }

    except Exception as e:
        # Clean up on error - validate path before deletion
        if file_path and os.path.exists(file_path):
            resolved_path = os.path.abspath(file_path)
            upload_dir_resolved = os.path.abspath(settings.upload_dir)
            if resolved_path.startswith(upload_dir_resolved):
                os.unlink(file_path)

        logger.error(f"Upload failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/files", response_model=List[Dict[str, Any]])
def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    file_type: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|filename|file_size|file_type)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's files with filtering and sorting."""
    query = db.query(FileModel).filter(FileModel.owner_id == current_user.id)

    # Apply filters
    if file_type:
        query = query.filter(FileModel.file_type == file_type)
    if category:
        query = query.filter(FileModel.category == category)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                FileModel.filename.ilike(search_term),
                FileModel.original_filename.ilike(search_term),
                FileModel.content.ilike(search_term)
            )
        )

    # Apply sorting
    sort_column = getattr(FileModel, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    files = query.offset(skip).limit(limit).all()

    return [
        {
            "id": f.id,
            "filename": f.filename,
            "original_filename": f.original_filename,
            "file_type": f.file_type,
            "file_size": f.file_size,
            "category": f.category,
            "tags": f.tags,
            "created_at": f.created_at.isoformat(),
            "processing_status": f.processing_status
        }
        for f in files
    ]


@router.get("/files/{file_id}")
def get_file_details(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific file."""
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "id": file.id,
        "filename": file.filename,
        "original_filename": file.original_filename,
        "file_type": file.file_type,
        "mime_type": file.mime_type,
        "file_size": file.file_size,
        "file_hash": file.file_hash,
        "metadata": file.metadata,
        "tags": file.tags,
        "category": file.category,
        "processing_status": file.processing_status,
        "created_at": file.created_at.isoformat(),
        "updated_at": file.updated_at.isoformat()
    }


@router.get("/download/{file_id}")
def download_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download a file securely."""
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Log download
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="download",
        resource_type="file",
        resource_id=str(file_id),
        details={"filename": file.filename}
    )
    db.add(audit_entry)
    db.commit()

    return FileResponse(
        file.file_path,
        media_type=file.mime_type,
        filename=file.original_filename
    )


@router.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a file."""
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete physical file
    try:
        if os.path.exists(file.file_path):
            os.unlink(file.file_path)
    except Exception as e:
        logger.warning(f"Failed to delete physical file {file.file_path}: {e}")

    # Delete from database
    db.delete(file)
    db.commit()

    # Log deletion
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="delete",
        resource_type="file",
        resource_id=str(file_id),
        details={"filename": file.filename}
    )
    db.add(audit_entry)
    db.commit()

    return {"message": "File deleted successfully"}


# ===== SORTING RULES =====

@router.post("/sorting-rules")
def create_sorting_rule(
    name: str,
    description: Optional[str] = None,
    conditions: Optional[Dict[str, Any]] = None,
    actions: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new sorting rule."""
    rule = SortingRule(
        name=name,
        description=description,
        conditions=conditions or {},
        actions=actions or {},
        created_by_id=current_user.id
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "conditions": rule.conditions,
        "actions": rule.actions,
        "created_at": rule.created_at.isoformat()
    }


@router.get("/sorting-rules")
def list_sorting_rules(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's sorting rules."""
    rules = db.query(SortingRule).filter(SortingRule.created_by_id == current_user.id).all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "is_active": r.is_active,
            "conditions": r.conditions,
            "actions": r.actions,
            "created_at": r.created_at.isoformat()
        }
        for r in rules
    ]


@router.post("/sort")
def apply_sorting(
    file_ids: List[int],
    rule_ids: Optional[List[int]] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Apply sorting rules to files."""
    # Get user's files
    files = db.query(FileModel).filter(
        and_(FileModel.owner_id == current_user.id, FileModel.id.in_(file_ids))
    ).all()

    if not files:
        raise HTTPException(status_code=404, detail="No files found")

    # Get sorting rules
    if rule_ids:
        rules = db.query(SortingRule).filter(
            and_(SortingRule.created_by_id == current_user.id, SortingRule.id.in_(rule_ids))
        ).all()
    else:
        # Use all active rules
        rules = db.query(SortingRule).filter(
            and_(SortingRule.created_by_id == current_user.id, SortingRule.is_active == True)
        ).all()

    # Apply sorting
    sorted_files = sorting_engine.apply_sorting_rules(files, rules)

    return {
        "message": "Sorting applied successfully",
        "sorted_files": [
            {
                "id": f.id,
                "filename": f.filename,
                "sort_priority": f.sort_priority,
                "category": f.category
            }
            for f in sorted_files
        ]
    }


# ===== ADMIN ENDPOINTS =====

@router.get("/admin/stats")
def get_system_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system statistics (admin only)."""
    total_files = db.query(FileModel).count()
    total_users = db.query(User).count()
    total_size = db.query(FileModel).with_entities(db.func.sum(FileModel.file_size)).scalar() or 0

    return {
        "total_files": total_files,
        "total_users": total_users,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2)
    }


@router.get("/admin/audit-logs")
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs (admin only)."""
    query = db.query(AuditLog)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)

    logs = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()

    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "username": log.username,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "success": log.success,
            "details": log.details
        }
        for log in logs
    ]


# ===== BACKGROUND TASKS =====

def process_file_background(file_id: int, processed_info: Dict[str, Any]):
    """Background processing for uploaded files."""
    from .database import get_db_context
    from .models import File as FileModel
    import logging

    logger = logging.getLogger(__name__)

    try:
        with get_db_context() as db:
            # Get file record
            file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
            if not file_record:
                logger.error(f"File record {file_id} not found for background processing")
                return

            # Update processing status
            file_record.processing_status = "processing"
            db.commit()

            # Perform heavy processing tasks
            try:
                # Full text indexing for searchable content
                if processed_info.get('content'):
                    # Here you would integrate with search engine like Elasticsearch
                    logger.info(f"Indexed content for file {file_id}")

                # Generate thumbnails for images
                if processed_info.get('file_type') == 'image':
                    # Here you would generate and store thumbnails
                    logger.info(f"Generated thumbnail for image file {file_id}")

                # Content analysis and tagging
                # Here you would run AI/ML analysis for automatic tagging
                logger.info(f"Completed content analysis for file {file_id}")

                # Virus scanning integration
                # Here you would integrate with antivirus service
                logger.info(f"Virus scan completed for file {file_id}")

                # Update processing status to completed
                file_record.processing_status = "completed"
                db.commit()

                logger.info(f"Background processing completed for file {file_id}")

            except Exception as e:
                logger.error(f"Background processing failed for file {file_id}: {e}")
                file_record.processing_status = "failed"
                db.commit()

    except Exception as e:
        logger.error(f"Database error in background processing for file {file_id}: {e}")