"""Testing Agent CLI.

This module provides a command-line interface for the Testing Agent.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional

from .agent import TestingAgent, TestingConfig
from .ci_integration import CIConfig, CIPipelineGenerator


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Testing Agent - Generate tests, scan for security issues, and analyze coverage"
    )

    # Common arguments
    parser.add_argument(
        "--source-dirs", "-s", nargs="+", required=True,
        help="Source directories to analyze (space-separated)"
    )
    parser.add_argument(
        "--output-dir", "-o", default="testing_output",
        help="Base output directory for all results (default: testing_output)"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run testing pipeline")
    test_parser.add_argument(
        "--min-coverage", type=float, default=80.0,
        help="Minimum code coverage percentage (default: 80.0)"
    )
    test_parser.add_argument(
        "--skip-security", action="store_true",
        help="Skip security scanning"
    )
    test_parser.add_argument(
        "--zap-path", 
        help="Path to OWASP ZAP installation (optional)"
    )
    
    # CI command
    ci_parser = subparsers.add_parser("ci", help="Generate CI pipeline configuration")
    ci_parser.add_argument(
        "--platform", choices=["github", "gitlab", "jenkins", "azure"], required=True,
        help="CI platform to generate configuration for"
    )
    ci_parser.add_argument(
        "--language", default="python",
        help="Programming language (default: python)"
    )
    ci_parser.add_argument(
        "--test-command", default="pytest --cov=src",
        help="Test command to run in CI (default: 'pytest --cov=src')"
    )
    ci_parser.add_argument(
        "--coverage-threshold", type=float, default=80.0,
        help="Coverage threshold for CI (default: 80.0)"
    )
    ci_parser.add_argument(
        "--security-scan", action="store_true",
        help="Include security scanning in CI pipeline"
    )
    ci_parser.add_argument(
        "--output-file",
        help="Output file for CI configuration (default based on platform)"
    )
    
    return parser.parse_args()


async def run_testing_pipeline(args):
    """Run the full testing pipeline."""
    # Create output directories
    output_dir = Path(args.output_dir)
    test_dir = output_dir / "tests"
    security_dir = output_dir / "security"
    coverage_dir = output_dir / "coverage"
    
    # Create testing configuration
    config = TestingConfig(
        source_dirs=args.source_dirs,
        test_output_dir=str(test_dir),
        security_output_dir=str(security_dir),
        coverage_output_dir=str(coverage_dir),
        min_coverage=args.min_coverage,
        enable_security_scan=not args.skip_security,
        zap_path=args.zap_path
    )
    
    # Create and run testing agent
    agent = TestingAgent(config)
    result = await agent.execute_testing_pipeline()
    
    # Print summary
    print("\n=== Testing Results ===")
    print(f"Tests Generated: {len(result.test_specs)}")
    print(f"Security Issues: {len(result.security_issues)}")
    
    coverage_total = 0
    if result.coverage_metrics:
        total_covered = sum(m.covered_lines for m in result.coverage_metrics.values())
        total_lines = sum(m.total_lines for m in result.coverage_metrics.values())
        if total_lines > 0:
            coverage_total = total_covered / total_lines * 100
    
    print(f"Overall Coverage: {coverage_total:.2f}%")
    print(f"Coverage Threshold: {args.min_coverage:.2f}%")
    print(f"Coverage Pass: {'Yes' if result.coverage_pass else 'No'}")
    
    # Print report locations
    print("\n=== Reports ===")
    for report_name, report_path in result.reports.items():
        print(f"{report_name.title()} Report: {report_path}")
    
    return 0 if result.coverage_pass else 1


def generate_ci_config(args):
    """Generate CI pipeline configuration."""
    # Create CI configuration
    config = CIConfig(
        platform=args.platform,
        language=args.language,
        test_command=args.test_command,
        coverage_threshold=args.coverage_threshold,
        security_scan=args.security_scan,
        environment_vars={"PYTHONPATH": ",".join(args.source_dirs)}
    )
    
    # Generate configuration
    generator = CIPipelineGenerator(config)
    
    # Determine output file
    output_file = args.output_file
    if not output_file:
        if args.platform == "github":
            output_file = ".github/workflows/testing.yml"
        elif args.platform == "gitlab":
            output_file = ".gitlab-ci.yml"
        elif args.platform == "jenkins":
            output_file = "Jenkinsfile"
        else:  # azure
            output_file = "azure-pipelines.yml"
    
    # Generate configuration
    generator.generate_pipeline_config(output_file)
    print(f"Generated {args.platform} CI configuration at: {output_file}")
    
    return 0


async def main():
    """Main entry point."""
    args = parse_args()
    
    if args.command == "test":
        return await run_testing_pipeline(args)
    elif args.command == "ci":
        return generate_ci_config(args)
    else:
        print("Error: Missing command. Use 'test' or 'ci'.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))