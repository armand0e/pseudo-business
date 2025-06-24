"""Agent Coordinator Module

This module provides the AgentCoordinator class for managing and coordinating
different types of agents in the system.
"""

from typing import Dict, List, Callable, Any
import time
from enum import Enum, auto
from dataclasses import dataclass
from src.infrastructure.logging_system import LoggingSystem

_logging_system = LoggingSystem()
logger = _logging_system.get_logger()

class AgentType(Enum):
    BACKEND = auto()
    DATABASE = auto()
    FRONTEND = auto()
    TESTING = auto()

@dataclass
class Task:
    task_id: str
    description: str
    agent_type: AgentType
    priority: int = 1
    dependencies: List[str] = None
    start_time: float = None
    duration: float = 0.0

@dataclass
class Agent:
    agent_id: str
    agent_type: AgentType
    capabilities: List[str]
    current_task: Task = None
    status: str = "idle"

@_logging_system.error_handler
class AgentCoordinator:
    """A class to coordinate different types of agents in the system."""

    def __init__(self, config: Dict):
        """
        Initialize the AgentCoordinator with a given configuration.

        Args:
            config (Dict): Configuration dictionary containing settings for timeouts,
                         retry policies, and concurrency limits.
        """
        logger.info("Initializing AgentCoordinator")
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.config = config

        # Initialize default configuration values
        self.timeout_settings = config.get("timeouts", {})
        self.retry_policies = config.get("retry_policies", {})
        self.concurrency_limits = config.get("concurrency_limits", {})

    def register_agent(self, agent_id: str, agent_type: AgentType, capabilities: List[str]) -> bool:
        """
        Register a new agent with the coordinator.

        Args:
            agent_id (str): Unique identifier for the agent.
            agent_type (AgentType): Type of the agent.
            capabilities (List[str]): List of capabilities the agent possesses.

        Returns:
            bool: True if registration was successful, False otherwise.
        """
        logger.info(f"Registering agent {agent_id} of type {agent_type.name}")
        if agent_id in self.agents:
            logger.warning(f"Agent {agent_id} already registered")
            return False

        self.agents[agent_id] = Agent(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities
        )
        logger.info(f"Successfully registered agent {agent_id}")
        return True

    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the coordinator.

        Args:
            agent_id (str): Unique identifier of the agent to unregister.

        Returns:
            bool: True if unregistration was successful, False otherwise.
        """
        logger.info(f"Unregistering agent {agent_id}")
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found for unregistration")
            return False

        del self.agents[agent_id]
        logger.info(f"Successfully unregistered agent {agent_id}")
        return True

    def add_task(self, task: Task) -> bool:
        """
        Add a new task to the coordinator.

        Args:
            task (Task): The task to add.

        Returns:
            bool: True if the task was added successfully, False otherwise.
        """
        logger.info(f"Adding task {task.task_id}: {task.description[:50]}...")
        if task.task_id in self.tasks:
            logger.warning(f"Task {task.task_id} already exists")
            return False

        self.tasks[task.task_id] = task
        logger.info(f"Successfully added task {task.task_id}")
        return True

    def assign_tasks(self):
        """
        Assign tasks to agents based on their capabilities and current workload.
        """
        logger.info("Assigning tasks to agents")
        # Sort tasks by priority
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: t.priority,
            reverse=True
        )
        logger.debug(f"Found {len(sorted_tasks)} tasks to assign")

        for task in sorted_tasks:
            if task.task_id in [t.task_id for t in [a.current_task for a in self.agents.values() if a.current_task]]:
                logger.debug(f"Task {task.task_id} already assigned to an agent")
                continue

            # Find suitable agents for this task type
            suitable_agents = [
                agent for agent in self.agents.values()
                if agent.agent_type == task.agent_type and agent.current_task is None
            ]
            logger.debug(f"Found {len(suitable_agents)} suitable agents for task {task.task_id}")

            if not suitable_agents:
                logger.warning(f"No suitable agents available for task {task.task_id}")
                continue

            # Select the first suitable agent (simple round-robin would be better)
            selected_agent = suitable_agents[0]
            logger.info(f"Selected agent {selected_agent.agent_id} for task {task.task_id}")

            # Check concurrency limits for this agent type
            max_concurrent = self.concurrency_limits.get(
                selected_agent.agent_type.name.lower(),
                float('inf')
            )

            concurrent_tasks = sum(1 for agent in self.agents.values()
                                 if agent.agent_type == task.agent_type and agent.current_task is not None)
            logger.debug(f"Current concurrent tasks of type {task.agent_type.name}: {concurrent_tasks}")

            if concurrent_tasks >= max_concurrent:
                logger.warning(f"Concurrency limit reached for {task.agent_type.name} agents")
                continue

            # Assign the task
            import time
            task.start_time = time.time()
            selected_agent.current_task = task
            selected_agent.status = "working"
            logger.info(f"Assigned task {task.task_id} to agent {selected_agent.agent_id}")

    def monitor_agents(self):
        """
        Monitor agents' statuses and handle timeouts.
        """
        logger.info("Monitoring agents for timeouts")
        current_time = time.time()

        for agent in self.agents.values():
            if agent.current_task is None:
                continue

            timeout = self.timeout_settings.get(
                f"{agent.agent_type.name.lower()}_timeout",
                300  # Default 5 minutes
            )
            logger.debug(f"Timeout setting for {agent.agent_type.name} agents: {timeout} seconds")

            task_start_time = agent.current_task.start_time or current_time - agent.current_task.duration
            elapsed_time = current_time - task_start_time
            logger.debug(f"Agent {agent.agent_id} working on task for {elapsed_time:.1f} seconds")

            if elapsed_time > timeout:
                logger.warning(f"Agent {agent.agent_id} timed out on task {agent.current_task.task_id}")
                agent.current_task = None
                agent.status = "idle"

    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific agent.

        Args:
            agent_id (str): Unique identifier of the agent.

        Returns:
            Dict[str, Any]: Dictionary containing the agent's status information.
        """
        logger.debug(f"Getting status for agent {agent_id}")
        agent = self.agents.get(agent_id)
        if not agent:
            logger.warning(f"Agent {agent_id} not found")
            return {}

        return {
            "agent_id": agent.agent_id,
            "type": agent.agent_type.name.lower(),
            "status": agent.status,
            "current_task": agent.current_task.task_id if agent.current_task else None,
            "capabilities": agent.capabilities
        }

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific task.

        Args:
            task_id (str): Unique identifier of the task.

        Returns:
            Dict[str, Any]: Dictionary containing the task's status information.
        """
        logger.debug(f"Getting status for task {task_id}")
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return {}

        # Find which agent is working on this task
        working_agent = None
        for agent in self.agents.values():
            if agent.current_task and agent.current_task.task_id == task_id:
                working_agent = agent
                break

        return {
            "task_id": task.task_id,
            "description": task.description,
            "type": task.agent_type.name.lower(),
            "priority": task.priority,
            "status": "completed" if not working_agent else "working",
            "dependencies": task.dependencies or []
        }

    def execute_workflow(self):
        """
        Execute the coordination workflow.
        """
        logger.info("Starting coordination workflow")
        while True:
            self.assign_tasks()
            self.monitor_agents()

            # Sleep to prevent busy waiting
            time.sleep(1)