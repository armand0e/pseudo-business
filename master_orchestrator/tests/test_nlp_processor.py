"""
Unit tests for the NLP Processor module.
"""

import unittest
from master_orchestrator.nlp_processor import NLPProcessor
from master_orchestrator.constants import ProjectType, TechStackPreferences, DeploymentTarget

class TestNLPProcessor(unittest.TestCase):
    """
    Test suite for the NLPProcessor class.
    """

    def setUp(self):
        """Set up the test fixture by creating a new NLPProcessor instance."""
        self.processor = NLPProcessor()

    def test_parse_basic_requirements(self):
        """Test parsing of basic requirements with default values."""
        text = "I need a web application."
        result = self.processor.parse(text)

        # Check default values
        self.assertEqual(result["description"], text)
        self.assertEqual(result["project_type"], ProjectType.WEB_APP)
        self.assertEqual(len(result["features"]), 0)  # No features mentioned

    def test_parse_with_features(self):
        """Test parsing of requirements with specific features."""
        text = "I need a web application with user authentication and database integration."
        result = self.processor.parse(text)

        # Check extracted features
        self.assertIn("user authentication", result["features"])
        self.assertIn("database integration", result["features"])

    def test_parse_with_tech_stack(self):
        """Test parsing of requirements with technology stack preferences."""
        text = "I want a web app using React for the frontend and FastAPI for the backend."
        result = self.processor.parse(text)

        # Check extracted tech stack
        self.assertEqual(result["tech_stack_preferences"].frontend, "React")
        self.assertEqual(result["tech_stack_preferences"].backend, "FastAPI")

    def test_parse_with_deployment_target(self):
        """Test parsing of requirements with deployment target."""
        text = "This web application should be deployed to production."
        result = self.processor.parse(text)

        # Check extracted deployment target
        self.assertEqual(result["deployment_target"], DeploymentTarget.PRODUCTION)

    def test_extract_project_type_mobile(self):
        """Test extraction of mobile app project type."""
        text = "I need an iOS application."
        result = self.processor.parse(text)
        self.assertEqual(result["project_type"], ProjectType.MOBILE_APP)

if __name__ == "__main__":
    unittest.main()