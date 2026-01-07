"""
Enterprise API endpoints for version control, backups, cloud sync, AI/ML, and more.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, or_

from .auth import get_current_active_user, get_current_admin_user, User
from .database import get_db
from .models import File as FileModel, AuditLog, SearchIndex
from .version_control import version_control, FileRevision
from .backup_system import backup_manager
from .cloud_storage import cloud_storage, init_cloud_providers
from .ai_processor import ocr_processor, content_classifier, auto_tagger
from .notifications import notification_manager, templates, init_notification_channels
from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== VERSION CONTROL ENDPOINTS =====

@router.post("/files/{file_id}/revisions")
def create_revision(
    file_id: int,
    change_description: Optional[str] = "Manual revision",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new revision of a file."""
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        revision = version_control.create_revision(
            db, file, current_user.id, change_description
        )
        return {
            "message": "Revision created successfully",
            "revision_id": revision.id,
            "revision_number": revision.revision_number,
            "created_at": revision.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to create revision: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create revision: {str(e)}")


@router.get("/files/{file_id}/revisions", response_model=List[Dict[str, Any]])
def list_revisions(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all revisions of a file."""
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    revisions = version_control.get_revisions(db, file_id)
    return [
        {
            "id": r.id,
            "revision_number": r.revision_number,
            "file_size": r.file_size,
            "file_hash": r.file_hash,
            "created_at": r.created_at.isoformat(),
            "change_description": r.change_description
        }
        for r in revisions
    ]


@router.post("/files/{file_id}/rollback/{revision_id}")
def rollback_to_revision(
    file_id: int,
    revision_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Rollback a file to a specific revision."""
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        updated_file = version_control.rollback(db, file, revision_id, current_user.id)
        return {
            "message": "Rollback successful",
            "file_id": updated_file.id,
            "new_hash": updated_file.file_hash
        }
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")


@router.get("/files/{file_id}/compare")
def compare_revisions(
    file_id: int,
    rev1_id: int,
    rev2_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Compare two revisions of a file."""
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        comparison = version_control.compare_revisions(db, file_id, rev1_id, rev2_id)
        return comparison
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


# ===== FULL-TEXT SEARCH ENDPOINTS =====

@router.get("/search")
def search_files(
    q: str,
    file_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Full-text search across file content and metadata."""
    # Search in database content
    query = db.query(FileModel).filter(FileModel.owner_id == current_user.id)
    
    # Full-text search in content field
    search_term = f"%{q}%"
    query = query.filter(
        or_(
            FileModel.filename.ilike(search_term),
            FileModel.original_filename.ilike(search_term),
            FileModel.content.ilike(search_term),
            FileModel.metadata.contains({"$or": [{"key": q}]})  # Simplified metadata search
        )
    )
    
    if file_type:
        query = query.filter(FileModel.file_type == file_type)
    if category:
        query = query.filter(FileModel.category == category)
    if tags:
        tag_list = [t.strip() for t in tags.split(',')]
        for tag in tag_list:
            query = query.filter(FileModel.tags.contains([tag]))
    
    files = query.order_by(desc(FileModel.created_at)).offset(skip).limit(limit).all()
    
    # Also search in SearchIndex if available
    search_results = db.query(SearchIndex).filter(
        and_(
            SearchIndex.content_text.ilike(search_term),
            SearchIndex.file.has(owner_id=current_user.id)
        )
    ).all()
    
    return {
        "query": q,
        "results": [
            {
                "id": f.id,
                "filename": f.filename,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "category": f.category,
                "created_at": f.created_at.isoformat()
            }
            for f in files
        ],
        "search_index_matches": len(search_results),
        "total": len(files)
    }


# ===== BACKUP ENDPOINTS =====

@router.post("/backups")
def create_backup(
    backup_type: str = Query("full", regex="^(full|incremental)$"),
    include_uploads: bool = True,
    compression: str = Query("gzip", regex="^(gzip|zip)$"),
    current_user: User = Depends(get_current_admin_user),
    background_tasks: BackgroundTasks = None
):
    """Create a new backup (admin only)."""
    try:
        backup = backup_manager.create_backup(
            backup_type=backup_type,
            include_uploads=include_uploads,
            compression=compression
        )
        
        # Send notification if configured
        notification_manager.send(
            title="Backup Completed",
            body=f"{backup_type.capitalize()} backup completed: {backup.file_count} files",
            severity="success" if backup.status == "completed" else "error",
            metadata={
                "backup_id": backup.id,
                "file_count": backup.file_count,
                "total_size": backup.total_size
            }
        )
        
        return {
            "message": "Backup created successfully",
            "backup_id": backup.id,
            "backup_type": backup.backup_type,
            "file_count": backup.file_count,
            "total_size": backup.total_size,
            "checksum": backup.checksum,
            "status": backup.status
        }
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/backups")
def list_backups(
    current_user: User = Depends(get_current_admin_user)
):
    """List all backups (admin only)."""
    backups = backup_manager.list_backups()
    return {"backups": backups}


@router.get("/backups/{backup_id}/verify")
def verify_backup(
    backup_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Verify backup integrity (admin only)."""
    try:
        result = backup_manager.verify_backup(backup_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/backups/{backup_id}/restore")
def restore_backup(
    backup_id: str,
    restore_path: str = "/tmp/sorter_restore",
    current_user: User = Depends(get_current_admin_user)
):
    """Restore a backup (admin only)."""
    try:
        backup_manager.restore_backup(backup_id, restore_path)
        return {
            "message": "Backup restored successfully",
            "restore_path": restore_path
        }
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.delete("/backups/{backup_id}")
def delete_backup(
    backup_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a backup (admin only)."""
    try:
        backup_manager.delete_backup(backup_id)
        return {"message": "Backup deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/backups/schedule")
def schedule_backup(
    backup_type: str = "incremental",
    interval_hours: int = 24,
    include_uploads: bool = True,
    current_user: User = Depends(get_current_admin_user)
):
    """Schedule automatic backups (admin only)."""
    backup_manager.schedule_backup(
        backup_type=backup_type,
        interval_hours=interval_hours,
        include_uploads=include_uploads
    )
    return {"message": "Backup scheduling enabled"}


# ===== CLOUD STORAGE ENDPOINTS =====

@router.post("/cloud/connect")
def connect_cloud_provider(
    provider: str,  # s3, google_drive, azure
    current_user: User = Depends(get_current_admin_user)
):
    """Connect to a cloud storage provider (admin only)."""
    cloud_provider = cloud_storage.get_provider(provider)
    if not cloud_provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not found")
    
    success = cloud_provider.connect()
    return {
        "provider": provider,
        "connected": success
    }


@router.post("/cloud/sync/{provider}")
def sync_to_cloud(
    provider: str,
    local_dir: str = "./uploads",
    remote_dir: str = "",
    current_user: User = Depends(get_current_admin_user)
):
    """Sync local directory to cloud storage (admin only)."""
    try:
        results = cloud_storage.sync_to_cloud(provider, local_dir, remote_dir)
        success_count = sum(1 for r in results.values() if r.success)
        return {
            "message": "Sync completed",
            "provider": provider,
            "total_files": len(results),
            "successful_uploads": success_count,
            "failed_uploads": len(results) - success_count
        }
    except Exception as e:
        logger.error(f"Cloud sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cloud/{provider}/files")
def list_cloud_files(
    provider: str,
    path: str = "",
    current_user: User = Depends(get_current_admin_user)
):
    """List files in cloud storage."""
    cloud_provider = cloud_storage.get_provider(provider)
    if not cloud_provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not found")
    
    if not cloud_provider._connected:
        cloud_provider.connect()
    
    files = cloud_provider.list_files(path)
    return {
        "provider": provider,
        "path": path,
        "files": [
            {
                "name": f.name,
                "path": f.path,
                "size": f.size,
                "modified_at": f.modified_at.isoformat()
            }
            for f in files
        ]
    }


# ===== AI/ML ENDPOINTS =====

@router.post("/files/{file_id}/ocr")
def perform_ocr(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Perform OCR on a file (admin only)."""
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    try:
        if file.file_type == "image":
            result = ocr_processor.process_image(file.file_path)
        elif file.file_type == "document":
            result = ocr_processor.process_pdf(file.file_path)
        else:
            raise HTTPException(status_code=400, detail="OCR not supported for this file type")
        
        if result.success:
            # Update file with OCR text
            file.content = result.text
            db.commit()
        
        return {
            "success": result.success,
            "text": result.text,
            "confidence": result.confidence,
            "processing_time": result.processing_time,
            "error": result.error
        }
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/{file_id}/classify")
def classify_content(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Classify file content using ML."""
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        result = content_classifier.classify(
            file_path=file.file_path,
            file_type=file.file_type,
            metadata=file.metadata,
            content_text=file.content or ""
        )
        
        return {
            "category": result.category,
            "subcategory": result.subcategory,
            "confidence": result.confidence,
            "suggested_tags": result.suggested_tags,
            "entities": result.entities,
            "language": result.language
        }
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/{file_id}/auto-tag")
def auto_tag_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Automatically tag a file using AI analysis."""
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        suggestions = auto_tagger.analyze_and_tag(
            file_path=file.file_path,
            file_type=file.file_type,
            metadata=file.metadata,
            content_text=file.content or ""
        )
        
        return {
            "file_id": file_id,
            "suggestions": [
                {
                    "tag": s.tag,
                    "source": s.source,
                    "confidence": s.confidence,
                    "reason": s.reason
                }
                for s in suggestions
            ]
        }
    except Exception as e:
        logger.error(f"Auto-tagging failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== NOTIFICATION ENDPOINTS =====

@router.post("/notifications/test")
def test_notifications(
    channel: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Test a notification channel (admin only)."""
    provider = notification_manager.channels.get(channel)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Channel {channel} not found")
    
    success = provider.test_connection()
    return {
        "channel": channel,
        "connected": success
    }


@router.post("/notifications/send")
def send_notification(
    title: str,
    body: str,
    severity: str = "info",
    channels: Optional[List[str]] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """Send a notification (admin only)."""
    results = notification_manager.send(
        title=title,
        body=body,
        severity=severity,
        channels=channels
    )
    return {
        "message": "Notifications sent",
        "results": results
    }


# ===== SYSTEM STATUS =====

@router.get("/enterprise/status")
def enterprise_status(
    current_user: User = Depends(get_current_admin_user)
):
    """Get enterprise feature status."""
    return {
        "version_control": {
            "enabled": True,
            "status": "active"
        },
        "backup_system": {
            "enabled": settings.backup_enabled,
            "retention_days": settings.backup_retention_days
        },
        "cloud_storage": {
            "providers": list(cloud_storage.providers.keys()),
            "connected": sum(1 for p in cloud_storage.providers.values() if p._connected)
        },
        "ai_ml": {
            "ocr_enabled": settings.ocr_enabled,
            "classification_enabled": settings.classification_enabled,
            "auto_tagging_enabled": settings.auto_tagging_enabled
        },
        "notifications": {
            "channels": list(notification_manager.channels.keys()),
            "configured": len(notification_manager.channels) > 0
        }
    }
