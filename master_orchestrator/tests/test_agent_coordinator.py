"""
Unit tests and integration tests for the Agent Coordinator module.
"""

import unittest
import asyncio
from unittest.mock import patch, MagicMock
from master_orchestrator.agent_coordinator import AgentCoordinator

class TestAgentCoordinator(unittest.TestCase):
    """
    Test suite for the AgentCoordinator class.
    """

    def setUp(self):
        """Set up the test fixture by creating a new AgentCoordinator instance."""
        self.coordinator = AgentCoordinator()

        # Verify that TechStackPreferences is properly initialized
        self.assertIsNotNone(self.coordinator.tech_stack_preferences)

    def test_assign_tasks_adds_to_queue(self):
        """Test that tasks are added to the queue when assigned."""
        tasks = [
            {"agent_type": "FRONTEND", "description": "Task 1", "priority": 1},
            {"agent_type": "BACKEND", "description": "Task 2", "priority": 0}
        ]

        # Sort by priority before assigning
        sorted_tasks = sorted(tasks, key=lambda t: t["priority"])
        self.coordinator.assign_tasks(sorted_tasks)

        # Check that tasks are in the queue (in reverse order of priority)
        self.assertEqual(len(self.coordinator.task_queue), len(tasks))
        self.assertEqual(self.coordinator.task_queue[0]["description"], "Task 2")  # Highest priority

    @patch('master_orchestrator.agent_coordinator.AgentCoordinator._call_agent')
    def test_execute_task_success(self, mock_call_agent):
        """Test successful execution of a task."""
        # Mock the _call_agent method to return a success response
        mock_call_agent.return_value = asyncio.Future()
        mock_call_agent.return_value.set_result({"status": "success"})

        # Create a task and execute it
        task = {"agent_type": "FRONTEND", "description": "Test Task"}
        asyncio.run(self.coordinator._execute_task(task))

        # Check that the task was executed successfully
        self.assertNotIn(id(task), self.coordinator.active_tasks)

    @patch('master_orchestrator.agent_coordinator.AgentCoordinator._call_agent')
    def test_execute_task_failure_and_retry(self, mock_call_agent):
        """Test task failure and retry mechanism."""
        # Mock the _call_agent method to raise an exception
        mock_call_agent.side_effect = Exception("Simulated error")

        # Create a task and execute it (should fail)
        task = {"agent_type": "FRONTEND", "description": "Test Task"}
        asyncio.run(self.coordinator._execute_task(task))

        # The task should still be in active_tasks with increased attempts
        self.assertIn(id(task), self.coordinator.active_tasks)
        self.assertEqual(self.coordinator.active_tasks[id(task)]["attempts"], 1)

    def test_collect_artifacts(self):
        """Test the collection of artifacts from completed tasks."""
        # This is a simple test since collect_artifacts is currently hardcoded
        artifacts = self.coordinator.collect_artifacts()

        # Check that we get the expected number of artifact sets
        self.assertEqual(len(artifacts), 2)

        # Check for specific agent types in the artifacts
        agent_types = [artifact["agent_type"] for artifact in artifacts]
        self.assertIn("FRONTEND", agent_types)
        self.assertIn("BACKEND", agent_types)

    def test_concurrent_task_handling(self):
        """Test handling of multiple tasks concurrently."""
        # Create a mock for _call_agent that simulates different response times
        async def mock_call_agent(endpoint, task):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {"status": "success"}

        with patch('master_orchestrator.agent_coordinator.AgentCoordinator._call_agent', new=mock_call_agent):
            # Create multiple tasks
            tasks = [
                {"agent_type": "FRONTEND", "description": f"Task {i}"}
                for i in range(5)
            ]

            # Assign and execute all tasks
            self.coordinator.assign_tasks(tasks)

            # Wait for all tasks to complete
            while self.coordinator.active_tasks:
                asyncio.sleep(0.01)

            # All tasks should be completed
            self.assertEqual(len(self.coordinator.task_queue), 0)
            self.assertEqual(len(self.coordinator.active_tasks), 0)

if __name__ == "__main__":
    unittest.main()