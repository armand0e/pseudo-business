"""
Project-wide constants for Master Orchestrator.
"""

from enum import Enum, auto

class ProjectType(Enum):
    """Enumeration of supported project types."""
    WEB_APP = auto()
    MOBILE_APP = auto()
    MICROSERVICE = auto()
    DATA_PIPELINE = auto()

class AgentType(Enum):
    """Enumeration of specialized agent types."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    TESTING = "testing"
    DEVOPS = "devops"

class DeploymentTarget(Enum):
    """Enumeration of deployment target environments."""
    DEV = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class TechStackPreferences:
    """Data class for technology stack preferences."""

    def __init__(self, frontend="React", backend="FastAPI", database="PostgreSQL"):
        self.frontend = frontend
        self.backend = backend
        self.database = database

# Technology stack preferences
DEFAULT_TECH_STACK = {
    "frontend": "React",
    "backend": "FastAPI",
    "database": "PostgreSQL"
}

# Default agent endpoints (URLs)
DEFAULT_AGENT_ENDPOINTS = {
    AgentType.FRONTEND: "/agents/frontend",
    AgentType.BACKEND: "/agents/backend",
    AgentType.DATABASE: "/agents/database",
    AgentType.TESTING: "/agents/testing",
    AgentType.DEVOPS: "/agents/devops"
}

# Default retry configuration
DEFAULT_RETRY_CONFIG = {
    "max_attempts": 3,
    "backoff_factor": 1,
    "timeout": 60
}