"""
Automated Backup System

Provides scheduled, incremental backups with retention policies.
"""

import os
import tarfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging
import hashlib
import json
import schedule
import time
import threading

from .config import settings
from .database import get_db_context
from .models import File, AuditLog

logger = logging.getLogger(__name__)


@dataclass
class BackupInfo:
    """Information about a backup."""
    id: str
    backup_type: str  # full, incremental
    created_at: datetime
    file_count: int
    total_size: int
    checksum: str
    status: str  # pending, completed, failed
    error_message: Optional[str] = None


class BackupManager:
    """Manages automated backups with scheduling and retention."""

    def __init__(
        self,
        backup_dir: str = "/app/backups",
        retention_days: int = 30,
        max_backups: int = 100
    ):
        """Initialize backup manager."""
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self.max_backups = max_backups
        self.backup_metadata_file = self.backup_dir / "backup_manifest.json"
        self._load_manifest()
        
        # Scheduler thread
        self.scheduler_thread: Optional[threading.Thread] = None
        self.scheduler_running = False

    def _load_manifest(self) -> None:
        """Load backup manifest from disk."""
        if self.backup_metadata_file.exists():
            with open(self.backup_metadata_file, 'r') as f:
                self.manifest = json.load(f)
        else:
            self.manifest = {
                "version": "1.0",
                "last_backup": None,
                "backups": []
            }

    def _save_manifest(self) -> None:
        """Save backup manifest to disk."""
        with open(self.backup_metadata_file, 'w') as f:
            json.dump(self.manifest, f, indent=2, default=str)

    def create_backup(
        self,
        backup_type: str = "full",
        include_uploads: bool = True,
        include_database: bool = True,
        compression: str = "gzip"
    ) -> BackupInfo:
        """Create a new backup."""
        
        backup_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{backup_id}"
        
        logger.info(f"Starting {backup_type} backup: {backup_id}")

        try:
            # Collect files to backup
            files_to_backup = []
            total_size = 0
            
            if include_uploads:
                uploads_dir = Path(settings.upload_dir)
                if uploads_dir.exists():
                    for file_path in uploads_dir.rglob("*"):
                        if file_path.is_file():
                            files_to_backup.append(file_path)
                            total_size += file_path.stat().st_size

            # Create archive
            if compression == "gzip":
                archive_path = self._create_tar_gz(backup_path, files_to_backup, backup_id)
            elif compression == "zip":
                archive_path = self._create_zip(backup_path, files_to_backup, backup_id)
            else:
                archive_path = self._create_tar_gz(backup_path, files_to_backup, backup_id)

            # Calculate checksum
            checksum = self._calculate_checksum(archive_path)

            # Create backup info
            backup_info = BackupInfo(
                id=backup_id,
                backup_type=backup_type,
                created_at=datetime.utcnow(),
                file_count=len(files_to_backup),
                total_size=total_size,
                checksum=checksum,
                status="completed"
            )

            # Add to manifest
            self.manifest["last_backup"] = backup_info.created_at.isoformat()
            self.manifest["backups"].append({
                "id": backup_info.id,
                "type": backup_info.backup_type,
                "created_at": backup_info.created_at.isoformat(),
                "file_count": backup_info.file_count,
                "total_size": backup_info.total_size,
                "checksum": backup_info.checksum,
                "status": backup_info.status,
                "archive_path": str(archive_path)
            })
            self._save_manifest()

            # Clean old backups
            self._cleanup_old_backups()

            logger.info(f"Backup {backup_id} completed successfully")

            return backup_info

        except Exception as e:
            logger.error(f"Backup {backup_id} failed: {e}")
            backup_info = BackupInfo(
                id=backup_id,
                backup_type=backup_type,
                created_at=datetime.utcnow(),
                file_count=0,
                total_size=0,
                checksum="",
                status="failed",
                error_message=str(e)
            )
            return backup_info

    def _create_tar_gz(
        self,
        base_path: Path,
        files: List[Path],
        backup_id: str
    ) -> Path:
        """Create a gzip-compressed tar archive."""
        archive_path = base_path.with_suffix(".tar.gz")
        
        with tarfile.open(archive_path, "w:gz") as tar:
            for file_path in files:
                arcname = file_path.relative_to(file_path.parent.parent)
                tar.add(file_path, arcname=arcname)
        
        return archive_path

    def _create_zip(
        self,
        base_path: Path,
        files: List[Path],
        backup_id: str
    ) -> Path:
        """Create a ZIP archive."""
        archive_path = base_path.with_suffix(".zip")
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                arcname = file_path.relative_to(file_path.parent.parent)
                zipf.write(file_path, arcname=arcname)
        
        return archive_path

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """Verify integrity of a backup."""
        backup_entry = self._get_backup_entry(backup_id)
        if not backup_entry:
            raise ValueError(f"Backup {backup_id} not found")

        archive_path = Path(backup_entry["archive_path"])
        if not archive_path.exists():
            return {
                "backup_id": backup_id,
                "valid": False,
                "error": "Archive file not found"
            }

        # Verify checksum
        calculated_checksum = self._calculate_checksum(archive_path)
        stored_checksum = backup_entry.get("checksum", "")

        return {
            "backup_id": backup_id,
            "valid": calculated_checksum == stored_checksum,
            "checksum_match": calculated_checksum == stored_checksum,
            "calculated_checksum": calculated_checksum,
            "stored_checksum": stored_checksum
        }

    def restore_backup(self, backup_id: str, restore_path: str) -> bool:
        """Restore a backup to the specified path."""
        backup_entry = self._get_backup_entry(backup_id)
        if not backup_entry:
            raise ValueError(f"Backup {backup_id} not found")

        archive_path = Path(backup_entry["archive_path"])
        if not archive_path.exists():
            raise ValueError(f"Archive file not found: {archive_path}")

        target_path = Path(restore_path)
        target_path.mkdir(parents=True, exist_ok=True)

        try:
            if str(archive_path).endswith('.tar.gz'):
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(target_path)
            elif str(archive_path).endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(target_path)
            
            logger.info(f"Restored backup {backup_id} to {restore_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup {backup_id}: {e}")
            raise

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all backups."""
        return self.manifest.get("backups", [])

    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup."""
        backup_entry = self._get_backup_entry(backup_id)
        if not backup_entry:
            raise ValueError(f"Backup {backup_id} not found")

        # Delete archive file
        archive_path = Path(backup_entry["archive_path"])
        if archive_path.exists():
            archive_path.unlink()

        # Remove from manifest
        self.manifest["backups"] = [
            b for b in self.manifest["backups"] if b["id"] != backup_id
        ]
        self._save_manifest()

        logger.info(f"Deleted backup {backup_id}")
        return True

    def _cleanup_old_backups(self) -> None:
        """Remove old backups based on retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        # Filter backups to keep
        backups_to_keep = []
        for backup in self.manifest.get("backups", []):
            created_at = datetime.fromisoformat(backup["created_at"])
            if created_at >= cutoff_date:
                backups_to_keep.append(backup)

        # If still too many, keep most recent
        if len(backups_to_keep) > self.max_backups:
            backups_to_keep = sorted(
                backups_to_keep,
                key=lambda x: x["created_at"],
                reverse=True
            )[:self.max_backups]

        # Delete removed backup files
        backup_ids_to_remove = set(
            b["id"] for b in self.manifest.get("backups", [])
        ) - set(b["id"] for b in backups_to_keep)

        for backup in self.manifest.get("backups", []):
            if backup["id"] in backup_ids_to_remove:
                archive_path = Path(backup.get("archive_path", ""))
                if archive_path.exists():
                    archive_path.unlink()

        self.manifest["backups"] = backups_to_keep
        self._save_manifest()

    def _get_backup_entry(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Get a backup entry from manifest."""
        for backup in self.manifest.get("backups", []):
            if backup["id"] == backup_id:
                return backup
        return None

    def schedule_backup(
        self,
        backup_type: str = "incremental",
        interval_hours: int = 24,
        include_uploads: bool = True,
        include_database: bool = True
    ) -> None:
        """Schedule automatic backups."""
        def job():
            self.create_backup(
                backup_type=backup_type,
                include_uploads=include_uploads,
                include_database=include_database
            )

        schedule.every(interval_hours).hours.do(job)

        if not self.scheduler_running:
            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(
                target=self._run_scheduler,
                daemon=True
            )
            self.scheduler_thread.start()

    def _run_scheduler(self) -> None:
        """Run the backup scheduler."""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)

    def stop_scheduler(self) -> None:
        """Stop the backup scheduler."""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)


# Global instance
backup_manager = BackupManager()
