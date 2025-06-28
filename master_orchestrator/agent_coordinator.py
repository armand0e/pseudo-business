"""
Agent Coordinator for managing task assignment to specialized agents.

This module handles dispatching tasks to appropriate agents, monitoring their execution,
and collecting code artifacts from completed tasks.
"""

import asyncio
from typing import List, Dict, Any
from master_orchestrator.constants import AgentType, DEFAULT_AGENT_ENDPOINTS, DEFAULT_RETRY_CONFIG, TechStackPreferences

class AgentCoordinator:
    """
    Coordinates task assignment to specialized agents and manages their execution.

    Attributes:
        agent_endpoints: Mapping of agent types to their service endpoints.
        retry_config: Configuration for retrying failed tasks.
        task_queue: Priority queue of tasks waiting to be assigned.
        active_tasks: Dictionary mapping task IDs to their current state.
        tech_stack_preferences: Technology stack preferences for the project.
    """

    def __init__(self):
        """Initialize the agent coordinator with default configurations."""
        self.agent_endpoints = DEFAULT_AGENT_ENDPOINTS
        self.retry_config = DEFAULT_RETRY_CONFIG
        self.task_queue = []
        self.active_tasks = {}
        self.loop = asyncio.get_event_loop()
        self.tech_stack_preferences = TechStackPreferences()

    def assign_tasks(self, tasks: List[Dict]) -> None:
        """
        Assign a list of tasks to the task queue and begin processing.

        Args:
            tasks: List of task dictionaries
        """
        # Add tasks to the queue in priority order
        for task in sorted(tasks, key=lambda t: t["priority"]):
            self.task_queue.append(task)
            self._process_task_queue()

    def _process_task_queue(self) -> None:
        """Process the next task in the queue if available."""
        if not self.active_tasks and self.task_queue:
            task = self.task_queue.pop(0)
            self.loop.create_task(self._execute_task(task))

    async def _execute_task(self, task: Dict) -> None:
        """
        Execute a single task by sending it to the appropriate agent.

        Args:
            task: Task dictionary containing agent_type and other details
        """
        task_id = id(task)
        self.active_tasks[task_id] = {
            "state": "executing",
            "attempts": 0,
            "task_data": task
        }

        try:
            endpoint = self.agent_endpoints[AgentType(task["agent_type"])]
            # In a real implementation, this would be an HTTP request to the agent's endpoint
            await self._call_agent(endpoint, task)
            self.active_tasks[task_id]["state"] = "completed"
        except Exception as e:
            self.active_tasks[task_id]["state"] = "failed"
            self.active_tasks[task_id]["error"] = str(e)

            # Check if we should retry
            if (self.active_tasks[task_id]["attempts"] < self.retry_config["max_attempts"]):
                delay = self.retry_config["backoff_factor"] * (
                    2 ** self.active_tasks[task_id]["attempts"]
                )
                asyncio.create_task(
                    self._retry_task(task_id, delay)
                )
            else:
                # Max retries reached - task failed permanently
                pass

        finally:
            del self.active_tasks[task_id]
            self._process_task_queue()

    async def _call_agent(self, endpoint: str, task: Dict) -> Any:
        """
        Simulate calling an agent's endpoint with the given task.

        In a real implementation, this would be an HTTP POST request to the agent's API.
        """
        # This is a placeholder for the actual agent communication
        # In production, use a proper HTTP client like aiohttp
        await asyncio.sleep(1)  # Simulate network delay

        # Simulate different responses based on task type
        if "authentication" in task["description"].lower():
            return {"status": "success", "artifact": "user_auth_code.py"}
        elif "database" in task["description"].lower():
            return {"status": "success", "artifact": "db_schema.sql"}
        else:
            return {"status": "success", "artifact": f"{task['agent_type']}_output.txt"}

    async def _retry_task(self, task_id: int, delay: float) -> None:
        """Retry a failed task after a delay."""
        await asyncio.sleep(delay)
        self.active_tasks[task_id]["attempts"] += 1
        self.loop.create_task(self._execute_task(self.active_tasks[task_id]["task_data"]))

    def collect_artifacts(self) -> List[Dict]:
        """
        Collect code artifacts from completed tasks.

        Returns:
            List of artifact dictionaries with keys:
                - agent_type
                - files (dict mapping file paths to content)
                - dependencies
                - metadata
        """
        # In a real implementation, this would gather artifacts from all agents
        return [
            {
                "agent_type": AgentType.FRONTEND,
                "files": {"src/components/App.js": "// App component code"},
                "dependencies": [],
                "metadata": {}
            },
            {
                "agent_type": AgentType.BACKEND,
                "files": {"api/main.py": "// API routes", "models/user.py": "// User model"},
                "dependencies": [],
                "metadata": {}
            }
        ]