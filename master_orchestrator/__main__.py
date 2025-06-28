"""
Master Orchestrator Application Entry Point.

This module provides:
1. Project setup and development environment configuration
2. Command-line interface for testing the Master Orchestrator
3. Example usage of the orchestration workflow
"""

import os
import sys
from master_orchestrator import __version__
from master_orchestrator.orchestrator import MasterOrchestrator

def setup_project() -> None:
    """Set up the project development environment."""
    print("Setting up project development environment...")

    # Create necessary directories
    os.makedirs("project_code", exist_ok=True)
    os.makedirs("project_code/frontend", exist_ok=True)
    os.makedirs("project_code/backend", exist_ok=True)
    os.makedirs("project_code/db", exist_ok=True)

    # Create sample configuration files
    with open("project_code/config.py", "w") as f:
        f.write("# Project configuration\n")
        f.write("DEBUG = True\n")

    print("Project environment set up successfully.")

def test_orchestrator(requirements_text: str) -> None:
    """
    Test the Master Orchestrator with sample requirements.

    Args:
        requirements_text: Natural language description of user requirements
    """
    print("\n=== Testing Master Orchestrator ===")
    print(f"Using requirements: {requirements_text}")

    try:
        # Initialize and use the orchestrator
        with MasterOrchestrator() as orchestrator:
            result = orchestrator.process_requirements(requirements_text)

        # Display results
        print("\nOrchestration completed successfully!")
        print(f"Codebase path: {result['codebase_path']}")
        print(f"Generated {len(result['tasks'])} tasks")
        print(f"Collected {len(result['artifacts'])} code artifacts")

    except Exception as e:
        print(f"\nError during orchestration: {e}", file=sys.stderr)
        sys.exit(1)

def main() -> None:
    """Main entry point for the Master Orchestrator application."""
    print(f"Master Orchestrator v{__version__}")
    print("=" * 50)

    # Set up project environment
    setup_project()

    # Test with sample requirements
    sample_requirements = """
    Create a web application for task management.
    Features needed:
    - User authentication (login/logout)
    - Task creation and assignment
    - Project management
    Use React for the frontend, FastAPI for the backend, and PostgreSQL for the database.
    Deploy to production environment.
    """

    test_orchestrator(sample_requirements)

if __name__ == "__main__":
    main()