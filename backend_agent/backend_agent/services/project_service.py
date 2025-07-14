"""
Project Service

Business logic for project management and coordination.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..database import crud
from ..database.session import get_db
from ..models import ProjectCreate, ProjectUpdate, ProjectStatus
from ..middleware.error_handler import ProjectNotFoundError
from .orchestrator_service import OrchestratorService

logger = logging.getLogger(__name__)

class ProjectService:
    """Service for project management operations"""

    def __init__(self):
        self.orchestrator_service = OrchestratorService()

    async def create_project(self, db: Session, project_data: ProjectCreate, user_id: int) -> crud.models.Project:
        """
        Create a new project
        
        Args:
            db: Database session
            project_data: Project creation data
            user_id: ID of user creating the project
            
        Returns:
            Created project instance
        """
        logger.info(f"Creating project: {project_data.name}")
        db_project = crud.create_project(db=db, project=project_data, user_id=user_id)
        await self.orchestrator_service.notify_project_created(db_project.id, project_data.dict())
        return db_project

    async def get_project(self, db: Session, project_id: int) -> crud.models.Project:
        """
        Get project by ID
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            Project instance
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        logger.info(f"Getting project {project_id}")
        db_project = crud.get_project(db, project_id=project_id)
        if db_project is None:
            raise ProjectNotFoundError(project_id)
        return db_project

    async def update_project(self, db: Session, project_id: int, project_data: ProjectUpdate) -> crud.models.Project:
        """
        Update project
        
        Args:
            db: Database session
            project_id: Project ID
            project_data: Project update data
            
        Returns:
            Updated project instance
        """
        logger.info(f"Updating project {project_id}")
        db_project = crud.update_project(db=db, project_id=project_id, project=project_data)
        if db_project is None:
            raise ProjectNotFoundError(project_id)
        return db_project

    async def delete_project(self, db: Session, project_id: int) -> bool:
        """
        Delete project and all associated tasks
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            True if deleted successfully
        """
        logger.info(f"Deleting project {project_id}")
        return crud.delete_project(db=db, project_id=project_id)

    async def list_projects(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[crud.models.Project], int]:
        """
        List projects with optional filtering
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (projects list, total count)
        """
        logger.info("Listing projects")
        projects = crud.get_projects(db=db, skip=skip, limit=limit)
        # In a real app, we would also get the total count for pagination
        return projects, len(projects)