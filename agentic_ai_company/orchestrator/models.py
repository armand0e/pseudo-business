from typing import List, Dict, Any
from enum import Enum

class ProjectType(Enum):
    SAAS = "SaaS"
    MOBILE_APP = "Mobile App"
    WEB_APP = "Web App"

class DeploymentTarget(Enum):
    AWS = "AWS"
    GCP = "GCP"
    AZURE = "Azure"

class TechStackPreferences:
    frontend: str
    backend: str
    database: str

class SaaSRequirements:
    description: str
    project_type: ProjectType
    features: List[str]
    tech_stack_preferences: TechStackPreferences
    deployment_target: DeploymentTarget

class AgentTask:
    agent_type: str
    description: str
    dependencies: List[str]
    priority: int
    estimated_time: int

class CodeArtifact:
    agent_type: str
    files: Dict[str, str]  # Mapping of file paths to content
    dependencies: List[str]
    metadata: Dict[str, Any]