"""Coverage Analyzer Module.

This module handles code coverage analysis and reporting, integrating with coverage.py
to track how much of the codebase is covered by tests.
"""

import json
from pathlib import Path
from typing import Dict, List, Union, Optional, Any
from dataclasses import dataclass
import subprocess
import xml.etree.ElementTree as ET

@dataclass
class CoverageMetrics:
    """Represents code coverage metrics for a component."""
    line_rate: float
    branch_rate: float
    complexity: float
    covered_lines: int
    total_lines: int
    uncovered_lines: List[int]
    covered_branches: int
    total_branches: int
    file_path: str

class CoverageAnalyzer:
    """Analyzes and reports on code coverage metrics."""

    def __init__(self):
        self.coverage_rc = {
            "run": {
                "source": ["src"],
                "branch": True,
            },
            "report": {
                "exclude_lines": [
                    "pragma: no cover",
                    "def __repr__",
                    "raise NotImplementedError",
                    "if __name__ == .__main__.:",
                    "pass",
                ]
            }
        }

    def setup_coverage_config(self, source_dirs: List[str]) -> None:
        """Configure coverage settings for the project."""
        self.coverage_rc["run"]["source"] = source_dirs
        
        # Write .coveragerc file
        config_path = Path(".coveragerc")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("[run]\n")
            f.write(f"source = {','.join(source_dirs)}\n")
            f.write("branch = True\n\n")
            
            f.write("[report]\n")
            f.write("exclude_lines =\n")
            for line in self.coverage_rc["report"]["exclude_lines"]:
                f.write(f"    {line}\n")

    def run_coverage_analysis(
        self,
        test_command: str,
        output_dir: Union[str, Path]
    ) -> Dict[str, CoverageMetrics]:
        """Run test coverage analysis and collect metrics."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Run tests with coverage
            subprocess.run(
                ["coverage", "run", "-m", "pytest", test_command],
                check=True
            )

            # Generate coverage reports
            subprocess.run(
                ["coverage", "xml", "-o", str(output_dir / "coverage.xml")],
                check=True
            )
            subprocess.run(
                ["coverage", "html", "--directory", str(output_dir / "html")],
                check=True
            )
            subprocess.run(
                ["coverage", "json", "-o", str(output_dir / "coverage.json")],
                check=True
            )

            return self.parse_coverage_data(output_dir)

        except subprocess.CalledProcessError as e:
            print(f"Error running coverage analysis: {e}")
            return {}

    def parse_coverage_data(self, output_dir: Path) -> Dict[str, CoverageMetrics]:
        """Parse coverage data from generated reports."""
        metrics = {}

        try:
            # Parse XML report for detailed metrics
            xml_path = output_dir / "coverage.xml"
            tree = ET.parse(xml_path)
            root = tree.getroot()

            for class_elem in root.findall(".//class"):
                filename = class_elem.get("filename")
                if not filename:
                    continue

                # Extract metrics
                metrics[filename] = CoverageMetrics(
                    line_rate=float(class_elem.get("line-rate", 0)),
                    branch_rate=float(class_elem.get("branch-rate", 0)),
                    complexity=float(class_elem.get("complexity", 0)),
                    covered_lines=len(class_elem.findall(".//line[@hits='1']")),
                    total_lines=len(class_elem.findall(".//line")),
                    uncovered_lines=[
                        int(line.get("number"))
                        for line in class_elem.findall(".//line[@hits='0']")
                    ],
                    covered_branches=len(class_elem.findall(".//line[@branch='true'][@hits='1']")),
                    total_branches=len(class_elem.findall(".//line[@branch='true']")),
                    file_path=filename
                )

        except (ET.ParseError, FileNotFoundError) as e:
            print(f"Error parsing coverage XML: {e}")

        return metrics

    def generate_coverage_report(
        self,
        metrics: Dict[str, CoverageMetrics],
        output_file: Union[str, Path],
        min_coverage: float = 90.0
    ) -> bool:
        """Generate a comprehensive coverage report and check against minimum threshold."""
        output_file = Path(output_file)
        
        # Calculate overall metrics
        total_covered_lines = sum(m.covered_lines for m in metrics.values())
        total_lines = sum(m.total_lines for m in metrics.values())
        total_coverage = (total_covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        # Generate report content
        report_lines = [
            "# Code Coverage Report\n",
            "## Summary\n",
            f"- Overall Coverage: {total_coverage:.2f}%",
            f"- Files Analyzed: {len(metrics)}",
            f"- Total Lines: {total_lines}",
            f"- Covered Lines: {total_covered_lines}",
            f"- Coverage Threshold: {min_coverage}%\n",
            "## Coverage by File\n"
        ]
        
        # Sort files by coverage percentage
        sorted_files = sorted(
            metrics.items(),
            key=lambda x: x[1].line_rate,
            reverse=True
        )
        
        for file_path, file_metrics in sorted_files:
            coverage_pct = file_metrics.line_rate * 100
            report_lines.extend([
                f"### {file_path}\n",
                f"- Line Coverage: {coverage_pct:.2f}%",
                f"- Branch Coverage: {file_metrics.branch_rate * 100:.2f}%",
                f"- Complexity: {file_metrics.complexity}",
                f"- Lines: {file_metrics.total_lines} (covered: {file_metrics.covered_lines})",
                f"- Branches: {file_metrics.total_branches} (covered: {file_metrics.covered_branches})",
            ])
            
            if file_metrics.uncovered_lines:
                report_lines.extend([
                    "\nUncovered Lines:",
                    "```",
                    ", ".join(map(str, sorted(file_metrics.uncovered_lines))),
                    "```\n"
                ])
        
        # Write report to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        
        # Check if coverage meets minimum threshold
        return total_coverage >= min_coverage

    def export_coverage_badge(
        self,
        metrics: Dict[str, CoverageMetrics],
        output_file: Union[str, Path]
    ) -> None:
        """Generate a coverage badge in SVG format."""
        output_file = Path(output_file)
        
        # Calculate total coverage
        total_covered_lines = sum(m.covered_lines for m in metrics.values())
        total_lines = sum(m.total_lines for m in metrics.values())
        coverage = (total_covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        # Determine badge color based on coverage
        if coverage >= 90:
            color = "success"
        elif coverage >= 75:
            color = "yellow"
        else:
            color = "red"
        
        # Generate badge using shields.io format
        badge_url = (
            f"https://img.shields.io/badge/coverage-{coverage:.1f}%25-{color}"
        )
        
        # Download badge
        try:
            subprocess.run(
                ["curl", "-o", str(output_file), badge_url],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error generating coverage badge: {e}")