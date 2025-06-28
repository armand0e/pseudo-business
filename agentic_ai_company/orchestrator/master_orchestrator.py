from agentic_ai_company.orchestrator.nlp_processor import NLPProcessor
from agentic_ai_company.orchestrator.task_decomposer import TaskDecomposer
from agentic_ai_company.orchestrator.agent_coordinator import AgentCoordinator
from agentic_ai_company.orchestrator.code_aggregator import CodeAggregator
from agentic_ai_company.orchestrator.error_handler import ErrorHandler

class MasterOrchestrator:
    """
    Central coordination and workflow management.
    """

    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.task_decomposer = TaskDecomposer()
        self.agent_coordinator = AgentCoordinator()
        self.code_aggregator = CodeAggregator()
        self.error_handler = ErrorHandler()

    def process_requirements(self, text: str) -> None:
        """
        Accepts a natural language input and orchestrates the entire workflow.

        Args:
            text: The natural language requirements.
        """
        try:
            print("Processing requirements...")
            requirements = self.nlp_processor.parse(text)
            tasks = self.task_decomposer.decompose(requirements)
            self.agent_coordinator.assign_tasks(tasks)
            artifacts = self.agent_coordinator.collect_artifacts()
            self.code_aggregator.merge_artifacts(artifacts)
            print("Requirements processed successfully.")
        except Exception as e:
            self.error_handler.log_error(e)
            self.error_handler.notify_admin(e)