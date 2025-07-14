"""
Task Service

Business logic for task management, assignment, and coordination.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..database import crud
from ..database.session import get_db
from ..models import TaskCreate, TaskUpdate, TaskStatus, TaskPriority, AgentType
from ..middleware.error_handler import TaskNotFoundError, TaskAssignmentError
from .orchestrator_service import OrchestratorService

logger = logging.getLogger(__name__)

class TaskService:
    """Service for task management operations"""

    def __init__(self):
        self.orchestrator_service = OrchestratorService()

    async def create_task(self, db: Session, task_data: TaskCreate, user_id: int) -> crud.models.Task:
        """
        Create a new task
        
        Args:
            db: Database session
            task_data: Task creation data
            user_id: ID of user creating the task
            
        Returns:
            Created task instance
        """
        logger.info(f"Creating task: {task_data.title}")
        db_task = crud.create_task(db=db, task=task_data, user_id=user_id)
        await self.orchestrator_service.notify_task_created(db_task.id, task_data.dict())
        return db_task

    async def get_task(self, db: Session, task_id: int) -> crud.models.Task:
        """
        Get task by ID
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            Task instance
            
        Raises:
            TaskNotFoundError: If task not found
        """
        logger.info(f"Getting task {task_id}")
        db_task = crud.get_task(db, task_id=task_id)
        if db_task is None:
            raise TaskNotFoundError(task_id)
        return db_task

    async def update_task(self, db: Session, task_id: int, task_data: TaskUpdate) -> crud.models.Task:
        """
        Update task
        
        Args:
            db: Database session
            task_id: Task ID
            task_data: Task update data
            
        Returns:
            Updated task instance
        """
        logger.info(f"Updating task {task_id}")
        db_task = crud.update_task(db=db, task_id=task_id, task=task_data)
        if db_task is None:
            raise TaskNotFoundError(task_id)
        return db_task

    async def delete_task(self, db: Session, task_id: int) -> bool:
        """
        Delete task
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            True if deleted successfully
        """
        logger.info(f"Deleting task {task_id}")
        return crud.delete_task(db=db, task_id=task_id)

    async def list_tasks(
        self,
        db: Session,
        project_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[crud.models.Task], int]:
        """
        List tasks with optional filtering
        
        Args:
            db: Database session
            project_id: Filter by project ID
            status: Filter by status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (tasks list, total count)
        """
        logger.info("Listing tasks")
        tasks = crud.get_tasks(
            db=db,
            project_id=project_id,
            status=status,
            skip=skip,
            limit=limit,
        )
        # In a real app, we would also get the total count for pagination
        return tasks, len(tasks)