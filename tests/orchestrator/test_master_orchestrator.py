import unittest
from unittest.mock import patch, MagicMock

from agentic_ai_company.orchestrator.master_orchestrator import MasterOrchestrator

class TestMasterOrchestrator(unittest.TestCase):
    """
    Tests for the MasterOrchestrator.
    """

    @patch('agentic_ai_company.orchestrator.master_orchestrator.NLPProcessor')
    @patch('agentic_ai_company.orchestrator.master_orchestrator.TaskDecomposer')
    @patch('agentic_ai_company.orchestrator.master_orchestrator.AgentCoordinator')
    @patch('agentic_ai_company.orchestrator.master_orchestrator.CodeAggregator')
    @patch('agentic_ai_company.orchestrator.master_orchestrator.ErrorHandler')
    def test_process_requirements_success(self, mock_error_handler, mock_code_aggregator, mock_agent_coordinator, mock_task_decomposer, mock_nlp_processor):
        """
        Tests that the process_requirements method runs successfully.
        """
        # Arrange
        master_orchestrator = MasterOrchestrator()
        master_orchestrator.nlp_processor = mock_nlp_processor.return_value
        master_orchestrator.task_decomposer = mock_task_decomposer.return_value
        master_orchestrator.agent_coordinator = mock_agent_coordinator.return_value
        master_orchestrator.code_aggregator = mock_code_aggregator.return_value
        master_orchestrator.error_handler = mock_error_handler.return_value

        mock_nlp_processor.return_value.parse.return_value = MagicMock()
        mock_task_decomposer.return_value.decompose.return_value = []
        mock_agent_coordinator.return_value.collect_artifacts.return_value = []
        
        # Act
        master_orchestrator.process_requirements("Create a new SaaS application.")

        # Assert
        master_orchestrator.nlp_processor.parse.assert_called_once_with("Create a new SaaS application.")
        master_orchestrator.task_decomposer.decompose.assert_called_once()
        master_orchestrator.agent_coordinator.assign_tasks.assert_called_once_with([])
        master_orchestrator.agent_coordinator.collect_artifacts.assert_called_once()
        master_orchestrator.code_aggregator.merge_artifacts.assert_called_once_with([])
        master_orchestrator.error_handler.log_error.assert_not_called()
        master_orchestrator.error_handler.notify_admin.assert_not_called()

if __name__ == '__main__':
    unittest.main()