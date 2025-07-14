"""
Agents Router

API endpoints for agent management and coordination.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database.session import get_db
from ..models import (
    AgentRegistration, AgentStatus, AgentListResponse,
    AgentType, BaseResponse
)
from ..services.agent_service import AgentService

router = APIRouter()
agent_service = AgentService()

@router.post("/register", response_model=AgentStatus, status_code=status.HTTP_201_CREATED)
async def register_agent(
    registration: AgentRegistration,
    db: Session = Depends(get_db),
):
    """Register a new agent"""
    agent = await agent_service.register_agent(db=db, registration=registration)
    return agent

@router.get("/", response_model=AgentListResponse)
async def list_agents(
    db: Session = Depends(get_db),
):
    """List all registered agents and their status"""
    agents = await agent_service.list_agents(db=db)
    return AgentListResponse(
        success=True,
        message="Agents retrieved successfully",
        data=agents
    )

@router.get("/{agent_type}/status", response_model=AgentStatus)
async def get_agent_status(
    agent_type: AgentType,
    db: Session = Depends(get_db),
):
    """Get status of a specific agent"""
    status_response = await agent_service.get_agent_status(db=db, agent_type=agent_type)
    if not status_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_type} not found"
        )
    return status_response