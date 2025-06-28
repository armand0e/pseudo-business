"""
Unit tests for the Task Decomposer module.
"""

import unittest
from master_orchestrator.task_decomposer import TaskDecomposer
from master_orchestrator.constants import ProjectType, TechStackPreferences

class TestTaskDecomposer(unittest.TestCase):
    """
    Test suite for the TaskDecomposer class.
    """

    def setUp(self):
        """Set up the test fixture by creating a new TaskDecomposer instance."""
        self.decomposer = TaskDecomposer()

    def test_decompose_web_app(self):
        """Test decomposition of web application requirements."""
        requirements = {
            "project_type": ProjectType.WEB_APP,
            "features": ["user authentication", "database integration"],
            "tech_stack_preferences": TechStackPreferences(
                frontend="React",
                backend="FastAPI",
                database="PostgreSQL"
            )
        }

        tasks = self.decomposer.decompose(requirements)

        # Check that we have the expected number of tasks
        self.assertGreater(len(tasks), 0)

        # Check for specific tasks based on features
        has_auth_task = any("authentication" in task["description"].lower() for task in tasks)
        has_db_integration = any("integration" in task["description"].lower() and "database" in task["description"].lower() for task in tasks)

        self.assertTrue(has_auth_task, "User authentication task should be present")
        self.assertTrue(has_db_integration, "Database integration task should be present")

    def test_decompose_mobile_app(self):
        """Test decomposition of mobile application requirements."""
        requirements = {
            "project_type": ProjectType.MOBILE_APP,
            "features": ["API endpoints"],
            "tech_stack_preferences": TechStackPreferences(
                frontend="React Native",
                backend="FastAPI"
            )
        }

        tasks = self.decomposer.decompose(requirements)

        # Check for React Native in task descriptions
        has_react_native = any("react native" in task["description"].lower() for task in tasks)
        self.assertTrue(has_react_native, "React Native should be mentioned in the tasks")

    def test_decompose_microservice(self):
        """Test decomposition of microservice requirements."""
        requirements = {
            "project_type": ProjectType.MICROSERVICE,
            "features": ["API endpoints"],
            "tech_stack_preferences": TechStackPreferences(
                backend="FastAPI"
            )
        }

        tasks = self.decomposer.decompose(requirements)

        # Check for microservice-specific tasks
        has_microservice = any("microservice" in task["description"].lower() for task in tasks)
        self.assertTrue(has_microservice, "Microservice setup task should be present")

    def test_decompose_unknown_project_type(self):
        """Test decomposition of requirements with an unknown project type."""
        # Create a custom project type
        class CustomProjectType:
            value = "CUSTOM_PROJECT"

        requirements = {
            "project_type": CustomProjectType(),
            "features": [],
            "tech_stack_preferences": TechStackPreferences(
                frontend="React",
                backend="FastAPI"
            )
        }

        tasks = self.decomposer.decompose(requirements)

        # Should still generate generic tasks
        self.assertGreater(len(tasks), 0)
        self.assertTrue(any("generic" in task["description"].lower() for task in tasks))

if __name__ == "__main__":
    unittest.main()