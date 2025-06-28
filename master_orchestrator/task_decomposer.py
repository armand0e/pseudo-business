"""
Task Decomposer for breaking down requirements into actionable tasks.

This module transforms structured requirements into a list of tasks that can be assigned to specialized agents,
including task dependencies and priorities.
"""

from typing import List, Dict
from master_orchestrator.constants import AgentType, TechStackPreferences

class TaskDecomposer:
    """
    Decomposes structured requirements into specific tasks with dependencies.

    Attributes:
        project_type_to_tasks: Mapping of project types to predefined task templates.
    """

    def __init__(self):
        """Initialize the task decomposer with predefined task templates."""
        self.project_type_to_tasks = {
            "WEB_APP": self._get_web_app_tasks,
            "MOBILE_APP": self._get_mobile_app_tasks,
            "MICROSERVICE": self._get_microservice_tasks,
            "DATA_PIPELINE": self._get_data_pipeline_tasks
        }

    def decompose(self, requirements: Dict) -> List[Dict]:
        """
        Decompose structured requirements into a list of tasks.

        Args:
            requirements: Structured requirements dictionary

        Returns:
            List of task dictionaries with keys:
                - agent_type
                - description
                - dependencies
                - priority
                - estimated_time
        """
        project_type = requirements["project_type"].value.upper()
        decompose_method = self.project_type_to_tasks.get(project_type, self._get_generic_tasks)

        tasks = decompose_method(requirements)

        # Assign priorities based on task importance
        for i, task in enumerate(tasks):
            task["priority"] = i  # Lower numbers are higher priority

        return tasks

    def _get_web_app_tasks(self, requirements) -> List[Dict]:
        """Generate tasks for a web application project."""
        tasks = []

        # Common tasks
        tasks.extend([
            {
                "agent_type": AgentType.FRONTEND,
                "description": "Create React component structure",
                "dependencies": [],
                "estimated_time": 120  # minutes
            },
            {
                "agent_type": AgentType.BACKEND,
                "description": "Set up FastAPI application with basic routes",
                "dependencies": [],
                "estimated_time": 90
            },
            {
                "agent_type": AgentType.DATABASE,
                "description": f"Design database schema for {requirements['project_type']}",
                "dependencies": [],
                "estimated_time": 60
            }
        ])

        # Add tasks based on features
        if any(f.lower() in requirements["features"] for f in ["user authentication", "login"]):
            tasks.append({
                "agent_type": AgentType.BACKEND,
                "description": "Implement user authentication endpoints",
                "dependencies": [
                    "Set up FastAPI application with basic routes",
                    "Design database schema for web app"
                ],
                "estimated_time": 120
            })

        if "database integration" in requirements["features"]:
            tasks.append({
                "agent_type": AgentType.BACKEND,
                "description": f"Implement {requirements['tech_stack_preferences'].database} integration",
                "dependencies": [
                    "Design database schema for web app"
                ],
                "estimated_time": 180
            })

        return tasks

    def _get_mobile_app_tasks(self, requirements) -> List[Dict]:
        """Generate tasks for a mobile application project."""
        # Similar structure to web app but with React Native instead of React
        tasks = self._get_web_app_tasks(requirements)

        for task in tasks:
            if task["agent_type"] == AgentType.FRONTEND and "description" in task:
                task["description"] = task["description"].replace("React", "React Native")

        return tasks

    def _get_microservice_tasks(self, requirements) -> List[Dict]:
        """Generate tasks for a microservice project."""
        tasks = []

        # Microservice-specific tasks
        tasks.extend([
            {
                "agent_type": AgentType.BACKEND,
                "description": f"Set up {requirements['tech_stack_preferences'].backend} microservice",
                "dependencies": [],
                "estimated_time": 120
            },
            {
                "agent_type": AgentType.DATABASE,
                "description": f"Design database schema for {requirements['project_type']}",
                "dependencies": [],
                "estimated_time": 60
            }
        ])

        # Add API integration task if needed
        if any(f.lower() in requirements["features"] for f in ["API endpoints", "api"]):
            tasks.append({
                "agent_type": AgentType.BACKEND,
                "description": "Implement API endpoints",
                "dependencies": [
                    f"Set up {requirements['tech_stack_preferences'].backend} microservice"
                ],
                "estimated_time": 180
            })

        return tasks

    def _get_data_pipeline_tasks(self, requirements) -> List[Dict]:
        """Generate tasks for a data pipeline project."""
        tasks = []

        # Data pipeline-specific tasks
        tasks.extend([
            {
                "agent_type": AgentType.BACKEND,
                "description": f"Set up {requirements['tech_stack_preferences'].backend} application",
                "dependencies": [],
                "estimated_time": 90
            },
            {
                "agent_type": AgentType.DATABASE,
                "description": f"Design database schema for {requirements['project_type']}",
                "dependencies": [],
                "estimated_time": 60
            }
        ])

        # Add data processing task
        tasks.append({
            "agent_type": AgentType.BACKEND,
            "description": "Implement data processing logic",
            "dependencies": [
                f"Design database schema for data pipeline"
            ],
            "estimated_time": 240
        })

        return tasks

    def _get_generic_tasks(self, requirements) -> List[Dict]:
        """Generate generic tasks when project type is unknown."""
        return [
            {
                "agent_type": AgentType.BACKEND,
                "description": f"Set up {requirements['tech_stack_preferences'].backend} application",
                "dependencies": [],
                "estimated_time": 120
            },
            {
                "agent_type": AgentType.DATABASE,
                "description": f"Design database schema for generic project",
                "dependencies": [],
                "estimated_time": 60
            }
        ]