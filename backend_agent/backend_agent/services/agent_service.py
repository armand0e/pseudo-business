"""
Agent Service

Business logic for agent management, registration, and coordination.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..database import crud
from ..database.session import get_db
from ..models import AgentType, AgentRegistration, AgentStatus
from ..middleware.error_handler import AgentUnavailableError

logger = logging.getLogger(__name__)

class AgentService:
    """Service for agent management operations"""

    async def register_agent(self, db: Session, registration: AgentRegistration) -> crud.models.Agent:
        """
        Register a new agent with the backend
        
        Args:
            db: Database session
            registration: Agent registration data
            
        Returns:
            Registration confirmation
        """
        logger.info(f"Registering agent: {registration.agent_type}")
        db_agent = crud.get_agent_by_type(db, agent_type=registration.agent_type)
        if db_agent:
            # For simplicity, we'll just return the existing agent.
            # In a real app, you might want to update it.
            return db_agent
        return crud.create_agent(db=db, agent=registration)

    async def get_agent_status(self, db: Session, agent_type: AgentType) -> Optional[AgentStatus]:
        """
        Get current status of an agent
        
        Args:
            db: Database session
            agent_type: Type of agent
            
        Returns:
            Agent status or None if not found
        """
        db_agent = crud.get_agent_by_type(db, agent_type=agent_type.value)
        if not db_agent:
            return None

        # In a real app, you would have a more sophisticated way of tracking
        # agent health and load.
        return AgentStatus(
            agent_type=db_agent.agent_type,
            is_active=db_agent.is_active,
            current_tasks=0,  # Placeholder
            max_capacity=db_agent.max_capacity,
            last_heartbeat=datetime.utcnow()  # Placeholder
        )

    async def list_agents(self, db: Session) -> List[AgentStatus]:
        """
        List all registered agents and their status
        
        Args:
            db: Database session
            
        Returns:
            List of agent statuses
        """
        agents = []
        db_agents = crud.get_agents(db)
        for db_agent in db_agents:
            status = await self.get_agent_status(db, agent_type=AgentType(db_agent.agent_type))
            if status:
                agents.append(status)
        return agents