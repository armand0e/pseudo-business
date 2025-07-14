"""
Projects Router

API endpoints for project management operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.session import get_db
from ..models import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
    ProjectStatus, BaseResponse
)
from ..services.project_service import ProjectService
from ..middleware.error_handler import ProjectNotFoundError

router = APIRouter()
project_service = ProjectService()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
):
    """Create a new project"""
    # In a real app, user_id would come from the auth dependency
    project = await project_service.create_project(db=db, project_data=project_data, user_id=1)
    return project

@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """List projects with optional filtering"""
    projects, total = await project_service.list_projects(
        db=db,
        skip=skip,
        limit=limit
    )
    
    return ProjectListResponse(
        success=True,
        message="Projects retrieved successfully",
        data=projects,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Get project by ID"""
    try:
        project = await project_service.get_project(db=db, project_id=project_id)
        return project
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
):
    """Update project"""
    try:
        project = await project_service.update_project(db=db, project_id=project_id, project_data=project_data)
        return project
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{project_id}", response_model=BaseResponse)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Delete project and all associated tasks"""
    if not await project_service.delete_project(db=db, project_id=project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return BaseResponse(success=True, message="Project deleted successfully")