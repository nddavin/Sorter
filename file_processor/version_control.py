"""
Version Control System for File Revisions

Provides file versioning, diff tracking, and rollback capabilities.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
import logging

from .models import File, AuditLog, Base
from .encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


@dataclass
class FileRevision:
    """Represents a file revision."""
    id: int
    file_id: int
    revision_number: int
    file_path: str
    file_size: int
    file_hash: str
    created_at: datetime
    created_by_id: int
    change_description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    content_diff: Optional[str] = None


class VersionControl:
    """Version control for file revisions and rollback."""

    def __init__(self, revisions_dir: str = "/app/revisions"):
        """Initialize version control system."""
        self.revisions_dir = Path(revisions_dir)
        self.revisions_dir.mkdir(parents=True, exist_ok=True)

    def create_revision(
        self,
        db: Session,
        file: File,
        user_id: int,
        change_description: str = "Auto-saved revision"
    ) -> FileRevision:
        """Create a new revision of a file."""
        
        # Get next revision number
        last_revision = db.query(FileRevision).filter(
            FileRevision.file_id == file.id
        ).order_by(FileRevision.revision_number.desc()).first()
        
        revision_number = (last_revision.revision_number + 1) if last_revision else 1

        # Copy file to revisions directory
        revision_filename = f"{file.id}_v{revision_number}_{file.file_hash[:16]}"
        revision_path = self.revisions_dir / revision_filename

        # Read original file and copy
        try:
            with open(file.file_path, 'rb') as src:
                content = src.read()
                # Store encrypted for security
                with open(revision_path, 'wb') as dst:
                    dst.write(encrypt_data(content))
        except Exception as e:
            logger.error(f"Failed to copy file for revision: {e}")
            raise

        # Create revision record
        revision = FileRevisionModel(
            file_id=file.id,
            revision_number=revision_number,
            file_path=str(revision_path),
            file_size=file.file_size,
            file_hash=file.file_hash,
            created_by_id=user_id,
            change_description=change_description,
            metadata=file.metadata or {}
        )

        db.add(revision)
        db.commit()
        db.refresh(revision)

        logger.info(f"Created revision {revision_number} for file {file.id}")

        return self._model_to_revision(revision)

    def get_revisions(self, db: Session, file_id: int) -> List[FileRevision]:
        """Get all revisions for a file."""
        revisions = db.query(FileRevisionModel).filter(
            FileRevisionModel.file_id == file_id
        ).order_by(FileRevisionModel.revision_number.desc()).all()

        return [self._model_to_revision(r) for r in revisions]

    def get_revision(self, db: Session, revision_id: int) -> Optional[FileRevision]:
        """Get a specific revision."""
        revision = db.query(FileRevisionModel).filter(
            FileRevisionModel.id == revision_id
        ).first()

        return self._model_to_revision(revision) if revision else None

    def rollback(
        self,
        db: Session,
        file: File,
        revision_id: int,
        user_id: int
    ) -> File:
        """Rollback a file to a previous revision."""
        
        revision = self.get_revision(db, revision_id)
        if not revision:
            raise ValueError(f"Revision {revision_id} not found")

        # Read revision content
        try:
            with open(revision.file_path, 'rb') as f:
                content = decrypt_data(f.read())
        except Exception as e:
            logger.error(f"Failed to read revision: {e}")
            raise

        # Backup current state before rollback
        self.create_revision(
            db, file, user_id,
            change_description=f"Auto-backup before rollback to v{revision.revision_number}"
        )

        # Write back the old content
        with open(file.file_path, 'wb') as f:
            f.write(content)

        # Update file hash and metadata
        file.file_hash = revision.file_hash
        file.updated_at = datetime.utcnow()
        file.processing_status = "completed"

        # Create audit log
        audit = AuditLog(
            user_id=user_id,
            action="rollback",
            resource_type="file",
            resource_id=str(file.id),
            details={
                "revision_id": revision_id,
                "revision_number": revision.revision_number,
                "previous_hash": file.file_hash,
                "new_hash": revision.file_hash
            }
        )
        db.add(audit)
        db.commit()

        logger.info(f"Rolled back file {file.id} to revision {revision.revision_number}")

        return file

    def compare_revisions(
        self,
        db: Session,
        file_id: int,
        rev1_id: int,
        rev2_id: int
    ) -> Dict[str, Any]:
        """Compare two revisions of a file."""
        
        rev1 = self.get_revision(db, rev1_id)
        rev2 = self.get_revision(db, rev2_id)

        if not rev1 or not rev2:
            raise ValueError("One or both revisions not found")

        # Read content from both revisions
        content1 = self._read_revision_content(rev1)
        content2 = self._read_revision_content(rev2)

        # Calculate diff
        diff_result = self._calculate_diff(
            content1.decode('utf-8', errors='ignore'),
            content2.decode('utf-8', errors='ignore')
        )

        return {
            "revision1": {
                "id": rev1.id,
                "number": rev1.revision_number,
                "created_at": rev1.created_at.isoformat(),
                "file_hash": rev1.file_hash,
                "file_size": rev1.file_size
            },
            "revision2": {
                "id": rev2.id,
                "number": rev2.revision_number,
                "created_at": rev2.created_at.isoformat(),
                "file_hash": rev2.file_hash,
                "file_size": rev2.file_size
            },
            "differences": {
                "lines_added": diff_result["added"],
                "lines_removed": diff_result["removed"],
                "changes": diff_result["changes"],
                "similarity": diff_result["similarity"]
            }
        }

    def _read_revision_content(self, revision: FileRevision) -> bytes:
        """Read and decrypt revision content."""
        with open(revision.file_path, 'rb') as f:
            return decrypt_data(f.read())

    def _calculate_diff(
        self,
        content1: str,
        content2: str
    ) -> Dict[str, Any]:
        """Calculate differences between two text contents."""
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')

        added = set(lines2) - set(lines1)
        removed = set(lines1) - set(lines2)

        # Calculate similarity ratio
        common = set(lines1) & set(lines2)
        similarity = len(common) / max(len(set(lines1) | set(lines2)), 1)

        return {
            "added": len(added),
            "removed": len(removed),
            "changes": list(added)[:10] + list(removed)[:10],  # First 10 changes
            "similarity": round(similarity, 2)
        }

    def _model_to_revision(self, model: 'FileRevisionModel') -> FileRevision:
        """Convert database model to dataclass."""
        return FileRevision(
            id=model.id,
            file_id=model.file_id,
            revision_number=model.revision_number,
            file_path=model.file_path,
            file_size=model.file_size,
            file_hash=model.file_hash,
            created_at=model.created_at,
            created_by_id=model.created_by_id,
            change_description=model.change_description,
            metadata=model.metadata or {}
        )


# Database model for revisions
class FileRevisionModel(Base):
    """Database model for file revisions."""
    __tablename__ = "file_revisions"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_description = Column(Text)
    metadata = Column(JSON, default=lambda: {})

    file = relationship("File")
    created_by = relationship("User")

    __table_args__ = (
        Index('idx_revision_file', 'file_id'),
        Index('idx_revision_created', 'created_at'),
    )


# Import for SQLAlchemy columns
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

# Global instance
version_control = VersionControl()
