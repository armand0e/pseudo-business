"""Testing Agent Module.

This module provides the main Testing Agent implementation that coordinates test generation,
security scanning, and coverage analysis for the Agentic AI Development Platform.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Union, Optional, Any
from dataclasses import dataclass

from .test_generator import TestGenerator, TestSpec
from .security_scanner import SecurityScanner, SecurityIssue
from .coverage_analyzer import CoverageAnalyzer, CoverageMetrics

@dataclass
class TestingConfig:
    """Configuration for the Testing Agent."""
    source_dirs: List[str]
    test_output_dir: str
    security_output_dir: str
    coverage_output_dir: str
    min_coverage: float = 90.0
    enable_security_scan: bool = True
    zap_path: Optional[str] = None

@dataclass
class TestingResult:
    """Results from testing operations."""
    test_specs: List[TestSpec]
    security_issues: List[SecurityIssue]
    coverage_metrics: Dict[str, CoverageMetrics]
    coverage_pass: bool
    reports: Dict[str, Path]

class TestingAgent:
    """Coordinates test generation, security scanning, and coverage analysis."""

    def __init__(self, config: TestingConfig):
        self.config = config
        self.test_generator = TestGenerator()
        self.security_scanner = SecurityScanner()
        self.coverage_analyzer = CoverageAnalyzer()

        # Configure components
        if config.zap_path:
            self.security_scanner.configure_zap_path(config.zap_path)
        self.coverage_analyzer.setup_coverage_config(config.source_dirs)

    async def execute_testing_pipeline(self) -> TestingResult:
        """Execute the full testing pipeline."""
        # Create output directories
        test_dir = Path(self.config.test_output_dir)
        security_dir = Path(self.config.security_output_dir)
        coverage_dir = Path(self.config.coverage_output_dir)

        for directory in [test_dir, security_dir, coverage_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Run test generation
        test_specs = await self._generate_tests()
        test_report = test_dir / "test_report.md"
        self._generate_test_summary(test_specs, test_report)

        # Run security scanning if enabled
        security_issues = []
        if self.config.enable_security_scan:
            security_issues = await self._run_security_scans()
            security_report = security_dir / "security_report.md"
            self.security_scanner.generate_security_report(
                security_issues,
                security_report
            )

        # Run coverage analysis
        coverage_metrics = await self._analyze_coverage()
        coverage_report = coverage_dir / "coverage_report.md"
        coverage_pass = self.coverage_analyzer.generate_coverage_report(
            coverage_metrics,
            coverage_report,
            self.config.min_coverage
        )

        # Generate coverage badge
        self.coverage_analyzer.export_coverage_badge(
            coverage_metrics,
            coverage_dir / "coverage-badge.svg"
        )

        return TestingResult(
            test_specs=test_specs,
            security_issues=security_issues,
            coverage_metrics=coverage_metrics,
            coverage_pass=coverage_pass,
            reports={
                "test": test_report,
                "security": security_dir / "security_report.md",
                "coverage": coverage_report,
                "coverage_badge": coverage_dir / "coverage-badge.svg"
            }
        )

    async def _generate_tests(self) -> List[TestSpec]:
        """Generate test suites for all components."""
        test_specs = []

        for source_dir in self.config.source_dirs:
            source_path = Path(source_dir)
            if not source_path.exists():
                continue

            # Generate unit tests for Python files
            for py_file in source_path.rglob("*.py"):
                if not py_file.name.startswith("test_"):
                    test_specs.extend(
                        self.test_generator.generate_unit_tests(py_file)
                    )

            # Generate integration tests for API endpoints
            if source_path.name in ["routers", "controllers", "api"]:
                api_files = list(source_path.rglob("*.py"))
                endpoints = self._extract_endpoints(api_files)
                test_specs.extend(
                    self.test_generator.generate_integration_tests(
                        api_files,
                        endpoints
                    )
                )

            # Generate E2E tests based on workflow specs
            workflows = self._load_workflow_specs()
            test_specs.extend(
                self.test_generator.generate_e2e_tests(workflows)
            )

        # Generate test files
        test_output = Path(self.config.test_output_dir)
        for test_type in ["unit", "integration", "e2e"]:
            type_specs = [s for s in test_specs if s.test_type == test_type]
            if type_specs:
                self.test_generator.generate_pytest_file(
                    type_specs,
                    test_output / f"test_{test_type}.py"
                )

        return test_specs

    async def _run_security_scans(self) -> List[SecurityIssue]:
        """Run security scans on the codebase."""
        issues = []

        # Scan Python code with Bandit
        for source_dir in self.config.source_dirs:
            source_path = Path(source_dir)
            if source_path.exists():
                issues.extend(
                    self.security_scanner.scan_python_code(source_path)
                )

        # Scan web application if running
        # This would typically be done in a staging environment
        # app_url = "http://localhost:8000"  # Example URL
        # issues.extend(self.security_scanner.scan_web_application(app_url))

        return issues

    async def _analyze_coverage(self) -> Dict[str, CoverageMetrics]:
        """Run coverage analysis on test execution."""
        coverage_dir = Path(self.config.coverage_output_dir)
        return self.coverage_analyzer.run_coverage_analysis(
            "pytest",  # Basic pytest command
            coverage_dir
        )

    def _extract_endpoints(self, api_files: List[Path]) -> List[str]:
        """Extract API endpoints from router/controller files."""
        # This is a simple implementation - could be enhanced to actually
        # parse FastAPI/Flask routes from the files
        endpoints = []
        common_endpoints = [
            "/api/health",
            "/api/v1/users",
            "/api/v1/projects",
            "/api/v1/tasks"
        ]
        endpoints.extend(common_endpoints)
        return endpoints

    def _load_workflow_specs(self) -> List[Dict[str, str]]:
        """Load end-to-end workflow specifications."""
        # This could be enhanced to load from a configuration file
        return [
            {
                "name": "user_registration",
                "description": "Complete user registration flow",
                "steps": [
                    "Register new user",
                    "Verify email",
                    "Complete profile",
                    "Login"
                ]
            },
            {
                "name": "project_creation",
                "description": "Create and configure new project",
                "steps": [
                    "Create project",
                    "Add team members",
                    "Configure settings",
                    "Start task"
                ]
            }
        ]

    def _generate_test_summary(
        self,
        test_specs: List[TestSpec],
        output_file: Path
    ) -> None:
        """Generate a summary report of all generated tests."""
        # Group tests by type
        tests_by_type = {}
        for spec in test_specs:
            tests_by_type.setdefault(spec.test_type, []).append(spec)

        # Generate report content
        report_lines = [
            "# Test Generation Summary\n",
            "## Overview\n",
            f"- Total Tests: {len(test_specs)}",
        ]

        for test_type, specs in tests_by_type.items():
            report_lines.append(f"- {test_type.title()} Tests: {len(specs)}")

        report_lines.append("\n## Test Details\n")

        for test_type, specs in tests_by_type.items():
            report_lines.extend([
                f"### {test_type.title()} Tests\n",
                "| Test Name | Description | Dependencies |",
                "|-----------|-------------|--------------|"
            ])

            for spec in specs:
                deps = ", ".join(spec.dependencies) if spec.dependencies else "None"
                report_lines.append(
                    f"| {spec.name} | {spec.description} | {deps} |"
                )
            report_lines.append("")

        # Write report
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))