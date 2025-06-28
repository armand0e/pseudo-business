"""
Integration tests for agent workflows.
"""

import unittest
import asyncio
from unittest.mock import patch, MagicMock
from master_orchestrator.agent_coordinator import AgentCoordinator
from master_orchestrator.task_decomposer import TaskDecomposer
from master_orchestrator.nlp_processor import NLPProcessor

class TestAgentWorkflowIntegration(unittest.TestCase):
    """
    Integration test suite for the complete agent workflow.
    """

    def setUp(self):
        """Set up the test fixture by creating instances of all components."""
        self.nlp_processor = NLPProcessor()
        self.task_decomposer = TaskDecomposer()
        self.agent_coordinator = AgentCoordinator()

        # Verify that TechStackPreferences is properly initialized in all components
        self.assertIsNotNone(self.agent_coordinator.tech_stack_preferences)

    @patch('master_orchestrator.agent_coordinator.AgentCoordinator._call_agent')
    def test_complete_workflow(self, mock_call_agent):
        """Test the complete workflow from NLP processing to task execution."""
        # Mock the _call_agent method to simulate successful agent responses
        mock_call_agent.return_value = asyncio.Future()
        mock_call_agent.return_value.set_result({"status": "success"})

        # Step 1: Process natural language requirements
        text = "I need a web application with user authentication and database integration."
        requirements = self.nlp_processor.parse(text)

        # Step 2: Decompose requirements into tasks
        tasks = self.task_decomposer.decompose(requirements)

        # Step 3: Assign tasks to agents
        self.agent_coordinator.assign_tasks(tasks)

        # Wait for all tasks to complete
        while self.agent_coordinator.active_tasks:
            asyncio.sleep(0.1)  # Give time for async operations

        # Verify that all tasks were processed
        self.assertEqual(len(self.agent_coordinator.task_queue), 0)
        self.assertEqual(len(self.agent_coordinator.active_tasks), 0)

    @patch('master_orchestrator.agent_coordinator.AgentCoordinator._call_agent')
    def test_workflow_with_failed_task_recovery(self, mock_call_agent):
        """Test the workflow with task failure and retry."""
        # First call fails, second call succeeds
        attempt = [0]  # Use a list to allow modification in nested function

        async def mock_call(endpoint, task):
            if attempt[0] == 0:
                attempt[0] += 1
                raise Exception("Simulated failure")
            return {"status": "success"}

        mock_call_agent.side_effect = mock_call

        # Process requirements and decompose tasks
        text = "I need a web application with user authentication."
        requirements = self.nlp_processor.parse(text)
        tasks = self.task_decomposer.decompose(requirements)

        # Assign tasks - the first one should fail then succeed on retry
        self.agent_coordinator.assign_tasks(tasks)

        # Wait for all tasks to complete
        while self.agent_coordinator.active_tasks:
            asyncio.sleep(0.1)

        # Verify that all tasks were eventually processed successfully
        self.assertEqual(len(self.agent_coordinator.task_queue), 0)
        self.assertEqual(len(self.agent_coordinator.active_tasks), 0)

    def test_concurrent_task_handling_performance(self):
        """Test performance with concurrent task handling."""
        with patch('master_orchestrator.agent_coordinator.AgentCoordinator._call_agent') as mock_call:
            # Mock with a simple success response
            mock_call.return_value = asyncio.Future()
            mock_call.return_value.set_result({"status": "success"})

            # Create many tasks
            text = "I need a web application with various features."
            requirements = self.nlp_processor.parse(text)
            tasks = self.task_decomposer.decompose(requirements)

            # Double the number of tasks to test concurrency
            all_tasks = tasks * 2

            # Record start time
            start_time = asyncio.get_event_loop().time()

            # Assign and process all tasks
            self.agent_coordinator.assign_tasks(all_tasks)

            # Wait for completion
            while self.agent_coordinator.active_tasks:
                asyncio.sleep(0.1)

            # Calculate elapsed time
            end_time = asyncio.get_event_loop().time()
            elapsed = end_time - start_time

            # The test passes if all tasks are processed (assertions above)
            # And the processing time is reasonable for the number of tasks
            self.assertLess(elapsed, 10)  # Should complete in under 10 seconds

if __name__ == "__main__":
    unittest.main()