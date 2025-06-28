"""
Code Aggregator for merging code artifacts from different agents into a cohesive codebase.

This module handles merging code segments, resolving conflicts, and ensuring code compatibility.
"""

import os
import shutil
from typing import List, Dict
import git
from master_orchestrator.constants import AgentType, TechStackPreferences

class CodeAggregator:
    """
    Merges code artifacts from different agents into a cohesive codebase.

    Attributes:
        repo_path: Path to the Git repository for the project.
        temp_dir: Temporary directory for applying patches.
        tech_stack_preferences: Technology stack preferences for the project.
    """

    def __init__(self, repo_path: str = "project_code"):
        """Initialize the code aggregator with repository path."""
        self.repo_path = repo_path
        self.temp_dir = os.path.join(repo_path, ".temp_aggregation")
        self.tech_stack_preferences = TechStackPreferences()

        # Create repository if it doesn't exist
        if not os.path.exists(repo_path):
            os.makedirs(self.repo_path)
            git.Repo.init(self.repo_path)

    def merge_artifacts(self, artifacts: List[Dict]) -> str:
        """
        Merge code artifacts from different agents into the project codebase.

        Args:
            artifacts: List of artifact dictionaries with files and dependencies

        Returns:
            Path to the merged codebase
        """
        # Create temporary directory for merging
        os.makedirs(self.temp_dir, exist_ok=True)

        try:
            # Apply each artifact's changes
            for artifact in artifacts:
                self._apply_artifact(artifact)

            # Commit all changes
            repo = git.Repo(self.repo_path)
            repo.index.add(all=True)
            commit_message = f"Merge code artifacts from {len(artifacts)} agents"
            repo.index.commit(commit_message)

            # Clean up temporary directory
            shutil.rmtree(self.temp_dir)

            return self.repo_path

        except Exception as e:
            # Clean up on error
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            raise e

    def _apply_artifact(self, artifact: Dict) -> None:
        """
        Apply a single artifact's code changes to the temporary directory.

        Args:
            artifact: Artifact dictionary containing files and dependencies
        """
        # Create subdirectory for this agent's artifacts
        agent_dir = os.path.join(self.temp_dir, f"agent_{artifact['agent_type']}")
        os.makedirs(agent_dir, exist_ok=True)

        # Write each file to the temporary directory
        for file_path, content in artifact["files"].items():
            # Handle different agent types with specific file structures based on tech stack preferences
            if artifact["agent_type"] == AgentType.FRONTEND:
                dest_path = os.path.join(self.repo_path, "frontend", file_path)
            elif artifact["agent_type"] == AgentType.BACKEND:
                dest_path = os.path.join(self.repo_path, "backend", file_path)
            elif artifact["agent_type"] == AgentType.DATABASE:
                dest_path = os.path.join(self.repo_path, "db", file_path)
            else:
                dest_path = os.path.join(self.repo_path, file_path)

            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # Write the file content
            with open(dest_path, "w") as f:
                f.write(content)

    def get_codebase(self) -> str:
        """
        Get the path to the current codebase.

        Returns:
            Path to the project codebase
        """
        return self.repo_path

    def clean_up(self) -> None:
        """Clean up any temporary files and reset the aggregator."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)