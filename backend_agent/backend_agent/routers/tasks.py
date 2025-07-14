"""
Tasks Router

API endpoints for task management operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.session import get_db
from ..models import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    TaskStatus, TaskPriority, AgentType, BaseResponse
)
from ..services.task_service import TaskService
from ..middleware.error_handler import TaskNotFoundError

router = APIRouter()
task_service = TaskService()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
):
    """Create a new task"""
    # In a real app, user_id would come from the auth dependency
    task = await task_service.create_task(db=db, task_data=task_data, user_id=1)
    return task

@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status_filter: Optional[TaskStatus] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """List tasks with optional filtering"""
    tasks, total = await task_service.list_tasks(
        db=db,
        project_id=project_id,
        status=status_filter,
        skip=skip,
        limit=limit
    )
    
    return TaskListResponse(
        success=True,
        message="Tasks retrieved successfully",
        data=tasks,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """Get task by ID"""
    try:
        task = await task_service.get_task(db=db, task_id=task_id)
        return task
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
):
    """Update task"""
    try:
        task = await task_service.update_task(db=db, task_id=task_id, task_data=task_data)
        return task
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{task_id}", response_model=BaseResponse)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """Delete task"""
    if not await task_service.delete_task(db=db, task_id=task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return BaseResponse(success=True, message="Task deleted successfully")