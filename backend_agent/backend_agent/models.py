"""
Backend Agent Pydantic Models

Data models for API requests and responses in the Backend Agent.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ProjectStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class AgentType(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    DEVOPS = "devops"

# Base Models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Task Models
class TaskBase(BaseModel):
    """Base task model"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    project_id: Optional[int] = None
    assigned_agent: Optional[AgentType] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskCreate(TaskBase):
    """Task creation model"""
    pass

class TaskUpdate(BaseModel):
    """Task update model"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_agent: Optional[AgentType] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskResponse(TaskBase):
    """Task response model"""
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Project Models
class ProjectBase(BaseModel):
    """Base project model"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    repository_url: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ProjectCreate(ProjectBase):
    """Project creation model"""
    pass

class ProjectUpdate(BaseModel):
    """Project update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    repository_url: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ProjectResponse(ProjectBase):
    """Project response model"""
    id: int
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    task_count: int = 0

    class Config:
        orm_mode = True

# Agent Models
class AgentStatus(BaseModel):
    """Agent status model"""
    agent_type: AgentType
    is_active: bool
    current_tasks: int
    max_capacity: int
    last_heartbeat: datetime

class AgentRegistration(BaseModel):
    """Agent registration model"""
    agent_type: AgentType
    endpoint_url: str
    capabilities: List[str]
    max_capacity: int = 5

# Response Collections
class TaskListResponse(BaseResponse):
    """Task list response"""
    data: List[TaskResponse]
    total: int
    page: int
    per_page: int

class ProjectListResponse(BaseResponse):
    """Project list response"""
    data: List[ProjectResponse]
    total: int
    page: int
    per_page: int

class AgentListResponse(BaseResponse):
    """Agent list response"""
    data: List[AgentStatus]

# Error Models
class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)