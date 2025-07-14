import unittest
import os
from unittest.mock import patch, MagicMock
from master_orchestrator.orchestrator import MasterOrchestrator

class TestEvolutionIntegration(unittest.TestCase):
    """
    Tests the integration of the Evolution Engine with the Master Orchestrator.
    """

    def setUp(self):
        """Set up the test environment."""
        self.orchestrator = MasterOrchestrator()
        self.test_code = "def hello():\n    print('Hello, world!')"
        self.test_code_path = "test_code.py"
        with open(self.test_code_path, "w") as f:
            f.write(self.test_code)

    def tearDown(self):
        """Clean up the test environment."""
        if os.path.exists(self.test_code_path):
            os.remove(self.test_code_path)

    @patch('master_orchestrator.code_aggregator.CodeAggregator.merge_artifacts')
    @patch('master_orchestrator.nlp_processor.NLPProcessor.parse')
    @patch('master_orchestrator.task_decomposer.TaskDecomposer.decompose')
    @patch('master_orchestrator.agent_coordinator.AgentCoordinator')
    def test_evolution_engine_integration(self, MockAgentCoordinator, mock_decompose, mock_parse, mock_merge_artifacts):
        """
        Test that the Evolution Engine is called during the orchestration process.
        """
        # Mock the sub-components
        mock_merge_artifacts.return_value = self.test_code_path
        mock_parse.return_value = {}
        mock_decompose.return_value = []
        
        # Mock the AgentCoordinator to have no active tasks
        mock_agent_coordinator_instance = MockAgentCoordinator.return_value
        mock_agent_coordinator_instance.active_tasks = []
        mock_agent_coordinator_instance.collect_artifacts.return_value = []

        # Run the process
        result = self.orchestrator.process_requirements("A simple web app")

        # Assertions
        self.assertTrue(result.get("optimized"))
        self.assertIn("fitness", result)
        self.assertGreater(result["fitness"]["total"], 0)

if __name__ == "__main__":
    unittest.main()