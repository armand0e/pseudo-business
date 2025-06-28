"""
Master Orchestrator for coordinating the entire system workflow.

This module provides the central orchestration functionality that ties together
NLP processing, task decomposition, agent coordination, code aggregation,
and error handling.
"""

from typing import Dict, Any
from master_orchestrator.nlp_processor import NLPProcessor
from master_orchestrator.task_decomposer import TaskDecomposer
from master_orchestrator.agent_coordinator import AgentCoordinator
from master_orchestrator.code_aggregator import CodeAggregator
from master_orchestrator.error_handler import ErrorHandler
from master_orchestrator.constants import TechStackPreferences

class MasterOrchestrator:
    """
    Central component responsible for coordinating the entire system workflow.

    Attributes:
        nlp_processor: NLPProcessor instance for parsing requirements.
        task_decomposer: TaskDecomposer instance for decomposing tasks.
        agent_coordinator: AgentCoordinator instance for managing agents.
        code_aggregator: CodeAggregator instance for merging code artifacts.
        error_handler: ErrorHandler instance for centralized error management.
    """

    def __init__(self):
        """Initialize the Master Orchestrator with all subcomponents."""
        self.nlp_processor = NLPProcessor()
        self.task_decomposer = TaskDecomposer()
        self.agent_coordinator = AgentCoordinator()
        self.code_aggregator = CodeAggregator()
        self.error_handler = ErrorHandler()
        self.tech_stack_preferences = TechStackPreferences()

    def process_requirements(self, text: str) -> Dict[str, Any]:
        """
        Process natural language requirements and orchestrate the entire workflow.

        Args:
            text: Natural language description of user requirements

        Returns:
            Dictionary containing:
                - codebase_path: Path to the merged codebase
                - tasks: List of all generated tasks
                - artifacts: List of collected code artifacts
        """
        try:
            # Step 1: Parse requirements using NLP processor
            requirements = self.nlp_processor.parse(text)

            # Step 2: Decompose tasks from structured requirements
            tasks = self.task_decomposer.decompose(requirements)

            # Step 3: Coordinate agents to execute tasks
            self.agent_coordinator.assign_tasks(tasks)

            # Wait for all tasks to complete (in a real implementation, this would be async)
            while self.agent_coordinator.active_tasks:
                pass

            # Step 4: Collect code artifacts from completed tasks
            artifacts = self.agent_coordinator.collect_artifacts()

            # Step 5: Merge artifacts into a cohesive codebase
            codebase_path = self.code_aggregator.merge_artifacts(artifacts)

            return {
                "codebase_path": codebase_path,
                "tasks": tasks,
                "artifacts": artifacts
            }

        except Exception as e:
            # Handle any errors that occur during the workflow
            if not self.error_handler.handle_exception(e, context={"step": "process_requirements"}):
                raise  # Re-raise critical errors

    def __enter__(self):
        """Context manager entry point for resource management."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point for cleanup."""
        if exc_type is not None:
            # Handle any exceptions that propagated out
            self.error_handler.log_error(exc_val)
            self.code_aggregator.clean_up()