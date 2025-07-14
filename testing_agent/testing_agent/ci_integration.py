"""CI/CD Integration Module.

This module provides functionality to integrate the Testing Agent with CI/CD pipelines,
supporting GitHub Actions, GitLab CI, and other CI/CD platforms.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import yaml

@dataclass
class CIConfig:
    """Configuration for CI pipeline integration."""
    platform: str  # "github", "gitlab", etc.
    language: str
    test_command: str
    coverage_threshold: float
    security_scan: bool
    environment_vars: Dict[str, str]

class CIPipelineGenerator:
    """Generates CI/CD pipeline configurations."""

    SUPPORTED_PLATFORMS = ["github", "gitlab", "jenkins", "azure"]
    
    def __init__(self, config: CIConfig):
        self.config = config
        self.validate_config()

    def validate_config(self) -> None:
        """Validate the CI configuration."""
        if self.config.platform not in self.SUPPORTED_PLATFORMS:
            raise ValueError(
                f"Unsupported CI platform. Must be one of: {self.SUPPORTED_PLATFORMS}"
            )

    def generate_pipeline_config(self, output_file: Union[str, Path]) -> None:
        """Generate CI pipeline configuration file."""
        if self.config.platform == "github":
            content = self._generate_github_workflow()
            filename = ".github/workflows/testing.yml"
        elif self.config.platform == "gitlab":
            content = self._generate_gitlab_ci()
            filename = ".gitlab-ci.yml"
        elif self.config.platform == "jenkins":
            content = self._generate_jenkinsfile()
            filename = "Jenkinsfile"
        else:  # azure
            content = self._generate_azure_pipeline()
            filename = "azure-pipelines.yml"

        # Use specified output file if provided
        if output_file:
            output_path = Path(output_file)
        else:
            output_path = Path(filename)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            if self.config.platform in ["github", "gitlab", "azure"]:
                yaml.safe_dump(content, f, sort_keys=False)
            else:
                f.write(content)  # Jenkinsfile is groovy syntax

    def _generate_github_workflow(self) -> Dict:
        """Generate GitHub Actions workflow configuration."""
        return {
            "name": "Testing Pipeline",
            "on": {
                "push": {
                    "branches": ["main", "master"],
                },
                "pull_request": {
                    "branches": ["main", "master"],
                },
            },
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {
                            "uses": "actions/checkout@v3"
                        },
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v4",
                            "with": {
                                "python-version": "3.11"
                            }
                        },
                        {
                            "name": "Install dependencies",
                            "run": "\n".join([
                                "python -m pip install --upgrade pip",
                                "pip install -r requirements.txt",
                                "pip install -r testing_agent/requirements.txt"
                            ])
                        },
                        {
                            "name": "Run tests and coverage",
                            "run": self.config.test_command
                        },
                    ] + ([
                        {
                            "name": "Run security scan",
                            "run": "bandit -r . -f json -o security-report.json"
                        }
                    ] if self.config.security_scan else []) + [
                        {
                            "name": "Upload coverage report",
                            "uses": "actions/upload-artifact@v3",
                            "with": {
                                "name": "coverage-report",
                                "path": "coverage/"
                            }
                        },
                        {
                            "name": "Check coverage threshold",
                            "run": f"coverage report --fail-under={self.config.coverage_threshold}"
                        }
                    ],
                    "env": self.config.environment_vars
                }
            }
        }

    def _generate_gitlab_ci(self) -> Dict:
        """Generate GitLab CI configuration."""
        config = {
            "image": "python:3.11",
            "stages": ["test"],
            "variables": self.config.environment_vars,
            "test": {
                "stage": "test",
                "before_script": [
                    "python -m pip install --upgrade pip",
                    "pip install -r requirements.txt",
                    "pip install -r testing_agent/requirements.txt"
                ],
                "script": [
                    self.config.test_command,
                    f"coverage report --fail-under={self.config.coverage_threshold}"
                ],
                "coverage": {
                    "report": {
                        "coverage_report": {
                            "coverage_format": "cobertura",
                            "path": "coverage.xml"
                        }
                    }
                },
                "artifacts": {
                    "reports": {
                        "coverage_report": "coverage.xml"
                    },
                    "paths": ["coverage/"]
                }
            }
        }

        if self.config.security_scan:
            config["security_scan"] = {
                "stage": "test",
                "script": ["bandit -r . -f json -o security-report.json"],
                "artifacts": {
                    "reports": {
                        "security_report": "security-report.json"
                    }
                }
            }

        return config

    def _generate_jenkinsfile(self) -> str:
        """Generate Jenkinsfile configuration."""
        # Convert environment variables to Jenkins format
        env_vars = "\n            ".join(
            f"{k} = '{v}'" for k, v in self.config.environment_vars.items()
        )

        return f"""pipeline {{
    agent {{
        docker {{
            image 'python:3.11'
        }}
    }}
    
    environment {{
        {env_vars}
    }}
    
    stages {{
        stage('Setup') {{
            steps {{
                sh 'python -m pip install --upgrade pip'
                sh 'pip install -r requirements.txt'
                sh 'pip install -r testing_agent/requirements.txt'
            }}
        }}
        
        stage('Test') {{
            steps {{
                sh '{self.config.test_command}'
            }}
        }}
        
        stage('Coverage Check') {{
            steps {{
                sh 'coverage report --fail-under={self.config.coverage_threshold}'
            }}
        }}{'''
        
        stage('Security Scan') {
            steps {
                sh 'bandit -r . -f json -o security-report.json'
            }
        }''' if self.config.security_scan else ''}
    }}
    
    post {{
        always {{
            archiveArtifacts artifacts: 'coverage/**, security-report.json', fingerprint: true
            junit 'test-results/*.xml'
        }}
    }}
}}"""

    def _generate_azure_pipeline(self) -> Dict:
        """Generate Azure Pipelines configuration."""
        config = {
            "trigger": ["main", "master"],
            "pool": {
                "vmImage": "ubuntu-latest"
            },
            "variables": self.config.environment_vars,
            "steps": [
                {
                    "task": "UsePythonVersion@0",
                    "inputs": {
                        "versionSpec": "3.11"
                    }
                },
                {
                    "script": "\n".join([
                        "python -m pip install --upgrade pip",
                        "pip install -r requirements.txt",
                        "pip install -r testing_agent/requirements.txt"
                    ]),
                    "displayName": "Install dependencies"
                },
                {
                    "script": self.config.test_command,
                    "displayName": "Run tests and coverage"
                },
                {
                    "script": f"coverage report --fail-under={self.config.coverage_threshold}",
                    "displayName": "Check coverage threshold"
                },
                {
                    "task": "PublishCodeCoverageResults@1",
                    "inputs": {
                        "codeCoverageTool": "Cobertura",
                        "summaryFileLocation": "coverage.xml",
                        "reportDirectory": "coverage"
                    }
                }
            ]
        }

        if self.config.security_scan:
            config["steps"].append({
                "script": "bandit -r . -f json -o security-report.json",
                "displayName": "Run security scan"
            })

        return config

class CIResultParser:
    """Parses and processes CI pipeline results."""

    def __init__(self, platform: str):
        self.platform = platform

    def parse_test_results(self, results_file: Union[str, Path]) -> Dict:
        """Parse test execution results from CI pipeline."""
        results_file = Path(results_file)
        
        try:
            if results_file.suffix == '.xml':
                # Parse JUnit XML format
                import xml.etree.ElementTree as ET
                tree = ET.parse(results_file)
                root = tree.getroot()
                
                return {
                    'tests': int(root.get('tests', 0)),
                    'failures': int(root.get('failures', 0)),
                    'errors': int(root.get('errors', 0)),
                    'skipped': int(root.get('skipped', 0)),
                    'time': float(root.get('time', 0))
                }
            else:
                # Assume JSON format
                import json
                with open(results_file, 'r') as f:
                    return json.load(f)
                    
        except Exception as e:
            print(f"Error parsing test results: {e}")
            return {}

    def parse_coverage_results(self, coverage_file: Union[str, Path]) -> Dict:
        """Parse coverage results from CI pipeline."""
        coverage_file = Path(coverage_file)
        
        try:
            if coverage_file.suffix == '.xml':
                # Parse Cobertura XML format
                import xml.etree.ElementTree as ET
                tree = ET.parse(coverage_file)
                root = tree.getroot()
                
                return {
                    'line_rate': float(root.get('line-rate', 0)) * 100,
                    'branch_rate': float(root.get('branch-rate', 0)) * 100,
                    'complexity': float(root.get('complexity', 0))
                }
            else:
                # Assume JSON format
                import json
                with open(coverage_file, 'r') as f:
                    return json.load(f)
                    
        except Exception as e:
            print(f"Error parsing coverage results: {e}")
            return {}

    def parse_security_results(self, security_file: Union[str, Path]) -> Dict:
        """Parse security scan results from CI pipeline."""
        try:
            with open(security_file, 'r') as f:
                results = json.load(f)
            
            # Aggregate results by severity
            severity_counts = {
                'high': 0,
                'medium': 0,
                'low': 0
            }
            
            for issue in results.get('results', []):
                severity = issue.get('issue_severity', 'low').lower()
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            return {
                'total_issues': len(results.get('results', [])),
                'severity_counts': severity_counts
            }
            
        except Exception as e:
            print(f"Error parsing security results: {e}")
            return {}