"""SQLAlchemy models for the Database Agent."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="owner")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="assignee")
    
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
        Index("ix_users_username_active", "username", "is_active"),
    )


class Project(Base):
    """Project model for project management."""
    
    __tablename__ = "projects"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Enum("planning", "active", "paused", "completed", "cancelled", name="project_status"),
        default="planning",
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "critical", name="project_priority"),
        default="medium",
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="project")
    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="project")
    
    __table_args__ = (
        Index("ix_projects_status_priority", "status", "priority"),
        Index("ix_projects_owner_status", "owner_id", "status"),
    )


class Task(Base):
    """Task model for task management."""
    
    __tablename__ = "tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(300), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Enum("pending", "in_progress", "review", "completed", "cancelled", name="task_status"),
        default="pending",
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "critical", name="task_priority"),
        default="medium",
    )
    type: Mapped[str] = mapped_column(
        Enum("frontend", "backend", "database", "devops", "testing", "research", name="task_type"),
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer)
    actual_hours: Mapped[Optional[int]] = mapped_column(Integer)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship("User", back_populates="tasks")
    agent: Mapped[Optional["Agent"]] = relationship("Agent", back_populates="tasks")
    dependencies: Mapped[list["TaskDependency"]] = relationship(
        "TaskDependency", foreign_keys="TaskDependency.task_id", back_populates="task"
    )
    
    __table_args__ = (
        Index("ix_tasks_status_priority", "status", "priority"),
        Index("ix_tasks_project_status", "project_id", "status"),
        Index("ix_tasks_assignee_status", "assignee_id", "status"),
        Index("ix_tasks_type_status", "type", "status"),
    )


class Agent(Base):
    """Agent model for AI agent management."""
    
    __tablename__ = "agents"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), index=True)
    type: Mapped[str] = mapped_column(
        Enum("frontend", "backend", "database", "devops", "testing", "evolution", name="agent_type"),
        index=True,
    )
    status: Mapped[str] = mapped_column(
        Enum("idle", "busy", "error", "offline", name="agent_status"),
        default="idle",
        index=True,
    )
    capabilities: Mapped[Optional[list]] = mapped_column(JSON)
    configuration: Mapped[Optional[dict]] = mapped_column(JSON)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    
    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="agents")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="agent")
    
    __table_args__ = (
        Index("ix_agents_type_status", "type", "status"),
        Index("ix_agents_project_type", "project_id", "type"),
    )


class TaskDependency(Base):
    """Task dependency model for managing task relationships."""
    
    __tablename__ = "task_dependencies"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    depends_on_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    dependency_type: Mapped[str] = mapped_column(
        Enum("blocks", "requires", "relates_to", name="dependency_type"),
        default="blocks",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on: Mapped["Task"] = relationship("Task", foreign_keys=[depends_on_id])
    
    __table_args__ = (
        Index("ix_task_deps_task_id", "task_id"),
        Index("ix_task_deps_depends_on", "depends_on_id"),
    )


class AuditLog(Base):
    """Audit log model for tracking changes."""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    action: Mapped[str] = mapped_column(
        Enum("create", "update", "delete", name="audit_action"),
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    changes: Mapped[Optional[dict]] = mapped_column(JSON)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")
    
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_user_action", "user_id", "action"),
        Index("ix_audit_logs_created_at", "created_at"),
    )