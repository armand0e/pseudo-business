"""
Database CRUD

CRUD operations for the Backend Agent database models.
"""

from sqlalchemy.orm import Session
from . import models
from .. import models as pydantic_models
from typing import List, Optional

def get_task(db: Session, task_id: int) -> Optional[models.Task]:
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
) -> List[models.Task]:
    query = db.query(models.Task)
    if project_id:
        query = query.filter(models.Task.project_id == project_id)
    if status:
        query = query.filter(models.Task.status == status)
    return query.offset(skip).limit(limit).all()

def create_task(db: Session, task: pydantic_models.TaskCreate, user_id: int) -> models.Task:
    db_task = models.Task(**task.dict(), created_by=user_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, task: pydantic_models.TaskUpdate) -> Optional[models.Task]:
    db_task = get_task(db, task_id)
    if db_task:
        update_data = task.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int) -> bool:
    db_task = get_task(db, task_id)
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False

def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[models.Project]:
    return db.query(models.Project).offset(skip).limit(limit).all()

def create_project(db: Session, project: pydantic_models.ProjectCreate, user_id: int) -> models.Project:
    db_project = models.Project(**project.dict(), created_by=user_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def update_project(db: Session, project_id: int, project: pydantic_models.ProjectUpdate) -> Optional[models.Project]:
    db_project = get_project(db, project_id)
    if db_project:
        update_data = project.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_project, key, value)
        db.commit()
        db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int) -> bool:
    db_project = get_project(db, project_id)
    if db_project:
        db.delete(db_project)
        db.commit()
        return True
    return False

def get_agent(db: Session, agent_id: int) -> Optional[models.Agent]:
    return db.query(models.Agent).filter(models.Agent.id == agent_id).first()

def get_agent_by_type(db: Session, agent_type: str) -> Optional[models.Agent]:
    return db.query(models.Agent).filter(models.Agent.agent_type == agent_type).first()

def get_agents(db: Session, skip: int = 0, limit: int = 100) -> List[models.Agent]:
    return db.query(models.Agent).offset(skip).limit(limit).all()

def create_agent(db: Session, agent: pydantic_models.AgentRegistration) -> models.Agent:
    db_agent = models.Agent(**agent.dict())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent