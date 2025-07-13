"""
NLP Processor for parsing and extracting structured requirements from natural language input.

This module uses spaCy to perform entity recognition, dependency parsing, and requirement extraction.
"""

import spacy
from typing import Dict, Any
from master_orchestrator.constants import ProjectType, TechStackPreferences, DeploymentTarget

class NLPProcessor:
    """
    Processes natural language text to extract structured requirements.

    Attributes:
        nlp (spaCy Language): The spaCy language model.
    """

    def __init__(self):
        """Initialize the NLP processor with the spaCy model."""
        self.nlp = spacy.load("en_core_web_sm")

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse natural language text and extract structured requirements.

        Args:
            text: Natural language description of user requirements

        Returns:
            Dictionary containing parsed requirements with keys:
                - description
                - project_type
                - features
                - tech_stack_preferences
                - deployment_target
        """
        doc = self.nlp(text)

        # Initialize default values
        requirements = {
            "description": text,
            "project_type": ProjectType.WEB_APP,  # Default value
            "features": [],
            "tech_stack_preferences": TechStackPreferences(
                frontend="React",
                backend="FastAPI",
                database="PostgreSQL"
            ),
            "deployment_target": DeploymentTarget.DEV
        }

        # Extract project type
        self._extract_project_type(doc, requirements)

        # Extract features
        self._extract_features(doc, requirements)

        # Extract technology preferences
        self._extract_tech_stack(doc, requirements)

        # Extract deployment target
        self._extract_deployment_target(doc, requirements)

        return requirements

    def _extract_project_type(self, doc, requirements):
        """Extract project type from the parsed document."""
        for ent in doc.ents:
            if ent.label_ == "PRODUCT" and ent.text.lower() in ["web app", "website"]:
                requirements["project_type"] = ProjectType.WEB_APP
            elif ent.label_ == "PRODUCT" and ent.text.lower() in ["mobile app", "ios app", "android app"]:
                requirements["project_type"] = ProjectType.MOBILE_APP

    def _extract_features(self, doc, requirements):
        """Extract features from the parsed document."""
        feature_keywords = {
            "authentication": "user authentication",
            "login": "user login",
            "database": "database integration",
            "api": "API endpoints",
            "frontend": "frontend components",
            "backend": "backend services"
        }

        for token in doc:
            if token.text.lower() in feature_keywords.values():
                requirements["features"].append(feature_keywords[token.text.lower()])

    def _extract_tech_stack(self, doc, requirements):
        """Extract technology stack preferences from the parsed document."""
        tech_mapping = {
            "react": {"frontend": "React"},
            "angular": {"frontend": "Angular"},
            "vue": {"frontend": "Vue.js"},
            "fastapi": {"backend": "FastAPI"},
            "flask": {"backend": "Flask"},
            "django": {"backend": "Django"},
            "postgres": {"database": "PostgreSQL"},
            "mysql": {"database": "MySQL"},
            "mongodb": {"database": "MongoDB"}
        }

        for token in doc:
            if token.text.lower() in tech_mapping:
                requirements["tech_stack_preferences"].__dict__.update(
                    tech_mapping[token.text.lower()]
                )

    def _extract_deployment_target(self, doc, requirements):
        """Extract deployment target from the parsed document."""
        for ent in doc.ents:
            if ent.label_ == "ORG" and ent.text.lower() == "production":
                requirements["deployment_target"] = DeploymentTarget.PRODUCTION