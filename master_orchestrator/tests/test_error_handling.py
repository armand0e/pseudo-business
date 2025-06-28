"""
Tests for validating error handling and logging mechanisms.
"""

import unittest
from unittest.mock import patch, MagicMock
import asyncio
import logging
from master_orchestrator.agent_coordinator import AgentCoordinator

class TestErrorHandling(unittest.TestCase):
    """
    Test suite for validating error handling mechanisms.
    """

    def setUp(self):
        """Set up the test fixture by creating a new AgentCoordinator instance."""
        self.coordinator = AgentCoordinator()

        # Verify that TechStackPreferences is properly initialized
        self.assertIsNotNone(self.coordinator.tech_stack_preferences)

    @patch('master_orchestrator.agent_coordinator.AgentCoordinator._call_agent')
    def test_task_execution_error_logging(self, mock_call_agent):
        """Test that errors during task execution are properly logged."""
        # Set up a mock logger
        with patch('logging.Logger.error') as mock_logger:
            # Mock the _call_agent method to raise an exception
            mock_call_agent.side_effect = Exception("Simulated error")

            # Create a task and execute it (should fail)
            task = {"agent_type": "FRONTEND", "description": "Task that will fail"}
            asyncio.run(self.coordinator._execute_task(task))

            # Verify that the logger was called with the error message
            mock_logger.assert_called()
            args, _ = mock_logger.call_args
            self.assertIn("Simulated error", str(args[0]))

    @patch('master_orchestrator.agent_coordinator.AgentCoordinator._call_agent')
    def test_retry_error_logging(self, mock_call_agent):
        """Test that retry attempts are properly logged."""
        # Set up a mock logger
        with patch('logging.Logger.warning') as mock_logger:
            # Mock the _call_agent method to raise an exception on first attempt
            mock_call_agent.side_effect = Exception("Simulated error")

            # Create a task and execute it (should fail)
            task = {"agent_type": "FRONTEND", "description": "Task that will fail"}
            asyncio.run(self.coordinator._execute_task(task))

            # Check if warning about retry was logged
            self.assertTrue(mock_logger.called)

    @patch('master_orchestrator.agent_coordinator.AgentCoordinator._call_agent')
    def test_max_retries_exceeded_logging(self, mock_call_agent):
        """Test that exceeding max retries is properly logged."""
        # Set up a mock logger
        with patch('logging.Logger.error') as mock_logger:
            # Mock the _call_agent method to always raise an exception
            mock_call_agent.side_effect = Exception("Simulated error")

            # Temporarily override retry config to force max retries
            original_max_attempts = self.coordinator.retry_config["max_attempts"]
            self.coordinator.retry_config["max_attempts"] = 1

            try:
                # Create a task and execute it (should fail permanently)
                task = {"agent_type": "FRONTEND", "description": "Task that will exceed retries"}
                asyncio.run(self.coordinator._execute_task(task))

                # Check if error about max retries was logged
                self.assertTrue(mock_logger.called)
            finally:
                # Restore original retry config
                self.coordinator.retry_config["max_attempts"] = original_max_attempts

    def test_logging_configuration(self):
        """Test that the logging configuration is properly set up."""
        # Check if the root logger has handlers configured
        root_logger = logging.getLogger()
        self.assertTrue(len(root_logger.handlers) > 0)

        # Check if there's at least one handler for ERROR level
        error_handlers = [h for h in root_logger.handlers if h.level <= logging.ERROR]
        self.assertTrue(len(error_handlers) > 0)

    @patch('master_orchestrator.agent_coordinator.AgentCoordinator._call_agent')
    def test_error_propagation(self, mock_call_agent):
        """Test that errors are properly propagated and not swallowed."""
        # Mock the _call_agent method to raise an exception
        mock_call_agent.side_effect = Exception("Simulated error")

        # Create a task and execute it (should fail)
        task = {"agent_type": "FRONTEND", "description": "Task that will fail"}

        with self.assertRaises(Exception):
            asyncio.run(self.coordinator._execute_task(task))

if __name__ == "__main__":
    unittest.main()