"""
SQLAlchemy models for the File Processor application.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

Base = declarative_base()


class User(Base):
    """User model with role-based access control."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="user", nullable=False)  # admin, manager, user
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))
    api_key = Column(String(255), unique=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    files = relationship("File", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")
    sorting_rules = relationship("SortingRule", back_populates="created_by")

    __table_args__ = (
        Index('idx_user_role_active', 'role', 'is_active'),
    )


class File(Base):
    """File model with comprehensive metadata."""
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    mime_type = Column(String(100))
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(128), unique=True, index=True)  # SHA-256 hash

    # Processing status
    processing_status = Column(String(20), default="uploaded")  # uploaded, processing, completed, failed
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    processing_error = Column(Text)

    # Metadata
    metadata = Column(JSON, default=dict)  # Extracted metadata (dimensions, duration, etc.)
    tags = Column(JSON, default=list)  # User-defined tags
    custom_fields = Column(JSON, default=dict)  # Custom metadata fields

    # Sorting and organization
    sort_priority = Column(Float, default=0.0)
    category = Column(String(50))
    subcategory = Column(String(50))

    # Encryption
    is_encrypted = Column(Boolean, default=False)
    encryption_key_id = Column(String(255))

    # Relationships
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="files")

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_file_owner_status', 'owner_id', 'processing_status'),
        Index('idx_file_type_size', 'file_type', 'file_size'),
        Index('idx_file_created', 'created_at'),
        Index('idx_file_hash', 'file_hash'),
    )


class SortingRule(Base):
    """Custom sorting rules defined by users."""
    __tablename__ = "sorting_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    rule_type = Column(String(20), nullable=False)  # automatic, manual, scheduled
    is_active = Column(Boolean, default=True)

    # Rule configuration
    conditions = Column(JSON, nullable=False)  # Rule conditions
    actions = Column(JSON, nullable=False)  # Actions to perform

    # Scheduling (for automated rules)
    schedule_cron = Column(String(100))  # Cron expression
    last_run = Column(DateTime)
    next_run = Column(DateTime)

    # Relationships
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = relationship("User", back_populates="sorting_rules")

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_sorting_rule_active', 'is_active', 'rule_type'),
    )


class AuditLog(Base):
    """Comprehensive audit logging."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Who
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="audit_logs")
    username = Column(String(50))  # Store username for historical records
    ip_address = Column(String(45))  # IPv4/IPv6
    user_agent = Column(String(500))

    # What
    action = Column(String(50), nullable=False)  # upload, download, delete, process, etc.
    resource_type = Column(String(50), nullable=False)  # file, user, rule, etc.
    resource_id = Column(String(100))  # ID of the affected resource

    # Details
    details = Column(JSON, default=dict)  # Additional context
    old_values = Column(JSON)  # For update operations
    new_values = Column(JSON)  # For update operations

    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Session info
    session_id = Column(String(255))
    api_key_used = Column(Boolean, default=False)

    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )


class Workflow(Base):
    """Automated workflow definitions."""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Workflow configuration
    trigger_type = Column(String(20), nullable=False)  # manual, scheduled, event
    trigger_config = Column(JSON, default=dict)  # Trigger-specific configuration

    steps = Column(JSON, nullable=False)  # Workflow steps definition
    variables = Column(JSON, default=dict)  # Workflow variables

    # Scheduling
    schedule_cron = Column(String(100))
    last_run = Column(DateTime)
    next_run = Column(DateTime)

    # Statistics
    run_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    average_runtime = Column(Float)

    # Relationships
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = relationship("User", foreign_keys=[created_by_id])

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_workflow_active_trigger', 'is_active', 'trigger_type'),
    )


class WorkflowExecution(Base):
    """Workflow execution records."""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    workflow = relationship("Workflow")

    # Execution details
    status = Column(String(20), default="running")  # running, completed, failed, cancelled
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    runtime_seconds = Column(Float)

    # Trigger info
    trigger_type = Column(String(20))
    trigger_details = Column(JSON, default=dict)

    # Results
    output = Column(JSON, default=dict)
    error_message = Column(Text)

    # Context
    variables = Column(JSON, default=dict)
    files_processed = Column(JSON, default=list)

    __table_args__ = (
        Index('idx_workflow_exec_status', 'workflow_id', 'status'),
        Index('idx_workflow_exec_started', 'started_at'),
    )


class SearchIndex(Base):
    """Search index for files (used with Elasticsearch)."""
    __tablename__ = "search_index"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    file = relationship("File")

    # Searchable content
    content_text = Column(Text)  # Extracted text content
    metadata_json = Column(JSON)  # Searchable metadata

    # Search optimization
    search_vector = Column(Text)  # Pre-processed search terms
    last_indexed = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_search_file', 'file_id'),
        Index('idx_search_last_indexed', 'last_indexed'),
    )