"""CRUD operations for the Database Agent."""
import logging
import uuid
from datetime import datetime
from typing import Optional, Sequence, Any, Dict

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, Field

from .models import User, Project, Task, Agent, TaskDependency, AuditLog
from .auth import get_password_hash

logger = logging.getLogger(__name__)


class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class FilterParams(BaseModel):
    """Base filter parameters."""
    search: Optional[str] = None
    is_active: Optional[bool] = None


class UserCreate(BaseModel):
    """User creation model."""
    email: str
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: bool = False


class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class ProjectCreate(BaseModel):
    """Project creation model."""
    name: str
    description: Optional[str] = None
    priority: str = "medium"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata_: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    """Project update model."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata_: Optional[Dict[str, Any]] = None


class TaskCreate(BaseModel):
    """Task creation model."""
    title: str
    description: Optional[str] = None
    type: str
    priority: str = "medium"
    project_id: uuid.UUID
    assignee_id: Optional[uuid.UUID] = None
    agent_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = None
    metadata_: Optional[Dict[str, Any]] = None


class TaskUpdate(BaseModel):
    """Task update model."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[uuid.UUID] = None
    agent_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    metadata_: Optional[Dict[str, Any]] = None


class AgentCreate(BaseModel):
    """Agent creation model."""
    name: str
    type: str
    capabilities: Optional[list] = None
    configuration: Optional[Dict[str, Any]] = None
    project_id: Optional[uuid.UUID] = None
    metadata_: Optional[Dict[str, Any]] = None


class AgentUpdate(BaseModel):
    """Agent update model."""
    name: Optional[str] = None
    status: Optional[str] = None
    capabilities: Optional[list] = None
    configuration: Optional[Dict[str, Any]] = None
    project_id: Optional[uuid.UUID] = None
    last_active: Optional[datetime] = None
    metadata_: Optional[Dict[str, Any]] = None


class CRUDBase:
    """Base CRUD operations."""
    
    def __init__(self, model):
        self.model = model
    
    async def get(self, db: AsyncSession, id: uuid.UUID):
        """Get a single record by ID."""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        filters: Optional[FilterParams] = None,
    ):
        """Get multiple records with pagination and filtering."""
        query = select(self.model)
        
        # Apply filters if provided
        if filters:
            if filters.search and hasattr(self.model, 'name'):
                query = query.where(self.model.name.ilike(f"%{filters.search}%"))
            if filters.is_active is not None and hasattr(self.model, 'is_active'):
                query = query.where(self.model.is_active == filters.is_active)
        
        # Add pagination
        query = query.offset(pagination.skip).limit(pagination.limit)
        
        # Execute query
        result = await db.execute(query)
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, obj_in, **kwargs):
        """Create a new record."""
        # Convert Pydantic model to dict if needed
        if hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump(exclude_unset=True)
        else:
            obj_data = obj_in
        
        # Add any additional kwargs
        obj_data.update(kwargs)
        
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(self, db: AsyncSession, db_obj, obj_in):
        """Update an existing record."""
        # Convert Pydantic model to dict if needed
        if hasattr(obj_in, 'model_dump'):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, id: uuid.UUID):
        """Delete a record by ID."""
        result = await db.execute(delete(self.model).where(self.model.id == id))
        await db.commit()
        return result.rowcount > 0
    
    async def count(self, db: AsyncSession, filters: Optional[FilterParams] = None) -> int:
        """Count records with optional filtering."""
        query = select(func.count(self.model.id))
        
        if filters:
            if filters.search and hasattr(self.model, 'name'):
                query = query.where(self.model.name.ilike(f"%{filters.search}%"))
            if filters.is_active is not None and hasattr(self.model, 'is_active'):
                query = query.where(self.model.is_active == filters.is_active)
        
        result = await db.execute(query)
        return result.scalar()


class CRUDUser(CRUDBase):
    """CRUD operations for User model."""
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, user_in: UserCreate) -> User:
        """Create a new user with hashed password."""
        hashed_password = get_password_hash(user_in.password)
        
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_password=hashed_password,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            is_admin=user_in.is_admin,
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    async def update(self, db: AsyncSession, db_user: User, user_in: UserUpdate) -> User:
        """Update user with optional password hashing."""
        update_data = user_in.model_dump(exclude_unset=True)
        
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        await db.commit()
        await db.refresh(db_user)
        return db_user


class CRUDProject(CRUDBase):
    """CRUD operations for Project model."""
    
    async def get_by_owner(self, db: AsyncSession, owner_id: uuid.UUID) -> Sequence[Project]:
        """Get projects by owner."""
        result = await db.execute(
            select(Project)
            .where(Project.owner_id == owner_id)
            .options(selectinload(Project.tasks))
        )
        return result.scalars().all()
    
    async def get_with_tasks(self, db: AsyncSession, id: uuid.UUID) -> Optional[Project]:
        """Get project with tasks."""
        result = await db.execute(
            select(Project)
            .where(Project.id == id)
            .options(selectinload(Project.tasks), selectinload(Project.agents))
        )
        return result.scalar_one_or_none()


class CRUDTask(CRUDBase):
    """CRUD operations for Task model."""
    
    async def get_by_project(self, db: AsyncSession, project_id: uuid.UUID) -> Sequence[Task]:
        """Get tasks by project."""
        result = await db.execute(
            select(Task)
            .where(Task.project_id == project_id)
            .options(selectinload(Task.dependencies))
        )
        return result.scalars().all()
    
    async def get_by_assignee(self, db: AsyncSession, assignee_id: uuid.UUID) -> Sequence[Task]:
        """Get tasks by assignee."""
        result = await db.execute(
            select(Task)
            .where(Task.assignee_id == assignee_id)
            .options(joinedload(Task.project))
        )
        return result.scalars().all()
    
    async def get_by_status(self, db: AsyncSession, status: str) -> Sequence[Task]:
        """Get tasks by status."""
        result = await db.execute(
            select(Task)
            .where(Task.status == status)
            .options(joinedload(Task.project), joinedload(Task.assignee))
        )
        return result.scalars().all()


class CRUDAgent(CRUDBase):
    """CRUD operations for Agent model."""
    
    async def get_by_type(self, db: AsyncSession, agent_type: str) -> Sequence[Agent]:
        """Get agents by type."""
        result = await db.execute(select(Agent).where(Agent.type == agent_type))
        return result.scalars().all()
    
    async def get_available(self, db: AsyncSession) -> Sequence[Agent]:
        """Get available agents (idle status)."""
        result = await db.execute(select(Agent).where(Agent.status == "idle"))
        return result.scalars().all()
    
    async def update_status(self, db: AsyncSession, agent_id: uuid.UUID, status: str) -> Optional[Agent]:
        """Update agent status."""
        agent = await self.get(db, agent_id)
        if agent:
            agent.status = status
            agent.last_active = datetime.utcnow()
            await db.commit()
            await db.refresh(agent)
        return agent


# CRUD instances
user_crud = CRUDUser(User)
project_crud = CRUDProject(Project)
task_crud = CRUDTask(Task)
agent_crud = CRUDAgent(Agent)


async def create_audit_log(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    changes: Optional[Dict[str, Any]] = None,
    metadata_: Optional[Dict[str, Any]] = None,
):
    """Create an audit log entry."""
    audit_log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=user_id,
        changes=changes,
        metadata_=metadata_,
    )
    
    db.add(audit_log)
    await db.commit()
    return audit_log