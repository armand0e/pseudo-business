"""Security Scanner Module.

This module is responsible for performing security scans using tools like Bandit and OWASP ZAP
to identify potential vulnerabilities in the codebase.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Union, Any
from dataclasses import dataclass

@dataclass
class SecurityIssue:
    """Represents a security vulnerability found during scanning."""
    tool: str
    severity: str
    confidence: str
    issue_type: str
    description: str
    file_path: str
    line_number: int
    code: str
    recommendation: str

class SecurityScanner:
    """Performs security vulnerability scanning on codebase."""

    def __init__(self):
        self.bandit_path = "bandit"
        self.zap_path = "zap-cli"

    def scan_python_code(self, source_dir: Union[str, Path]) -> List[SecurityIssue]:
        """Scan Python code using Bandit for security vulnerabilities."""
        source_dir = Path(source_dir)
        
        # Run Bandit scan
        try:
            result = subprocess.run(
                [
                    self.bandit_path,
                    "-r",
                    str(source_dir),
                    "-f",
                    "json"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse Bandit output
            issues = []
            bandit_results = json.loads(result.stdout)
            
            for result in bandit_results.get("results", []):
                issue = SecurityIssue(
                    tool="bandit",
                    severity=result["issue_severity"],
                    confidence=result["issue_confidence"],
                    issue_type=result["issue_text"],
                    description=result.get("more_info", ""),
                    file_path=result["filename"],
                    line_number=result["line_number"],
                    code=result.get("code", ""),
                    recommendation=result.get("fix", "Review and fix the identified security issue")
                )
                issues.append(issue)
            
            return issues
            
        except subprocess.CalledProcessError as e:
            print(f"Error running Bandit scan: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing Bandit output: {e}")
            return []

    def scan_web_application(
        self,
        target_url: str,
        context_name: str = "default"
    ) -> List[SecurityIssue]:
        """Scan web application using OWASP ZAP."""
        try:
            # Start ZAP scan
            scan_result = subprocess.run(
                [
                    self.zap_path,
                    "--zap-path", "/path/to/zap",
                    "quick-scan",
                    "--self-contained",
                    "--spider",
                    "--start",
                    target_url
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get alerts from ZAP
            alerts_result = subprocess.run(
                [
                    self.zap_path,
                    "--zap-path", "/path/to/zap",
                    "alerts", "-f", "json"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse ZAP alerts
            issues = []
            zap_results = json.loads(alerts_result.stdout)
            
            for alert in zap_results:
                issue = SecurityIssue(
                    tool="owasp_zap",
                    severity=alert["risk"],
                    confidence=alert["confidence"],
                    issue_type=alert["alert"],
                    description=alert["description"],
                    file_path=alert["url"],
                    line_number=0,  # ZAP doesn't provide line numbers
                    code=alert.get("attack", ""),
                    recommendation=alert.get("solution", "")
                )
                issues.append(issue)
            
            return issues
            
        except subprocess.CalledProcessError as e:
            print(f"Error running OWASP ZAP scan: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing OWASP ZAP output: {e}")
            return []

    def generate_security_report(
        self,
        issues: List[SecurityIssue],
        output_file: Union[str, Path]
    ) -> None:
        """Generate a detailed security report from scan results."""
        output_file = Path(output_file)
        
        # Group issues by severity
        severity_groups = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        for issue in issues:
            severity = issue.severity.lower()
            if severity in severity_groups:
                severity_groups[severity].append(issue)
        
        # Generate report content
        report_lines = [
            "# Security Scan Report\n",
            "## Summary\n",
            f"- Total Issues: {len(issues)}",
            f"- High Severity: {len(severity_groups['high'])}",
            f"- Medium Severity: {len(severity_groups['medium'])}",
            f"- Low Severity: {len(severity_groups['low'])}\n"
        ]
        
        # Add detailed findings
        for severity in ["high", "medium", "low"]:
            if severity_groups[severity]:
                report_lines.extend([
                    f"## {severity.title()} Severity Issues\n"
                ])
                
                for issue in severity_groups[severity]:
                    report_lines.extend([
                        f"### {issue.issue_type}\n",
                        f"- **Tool**: {issue.tool}",
                        f"- **Confidence**: {issue.confidence}",
                        f"- **Location**: {issue.file_path}:{issue.line_number}",
                        f"- **Description**: {issue.description}",
                        "- **Affected Code**:",
                        "```",
                        issue.code,
                        "```",
                        f"- **Recommendation**: {issue.recommendation}\n"
                    ])
        
        # Write report to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

    def configure_zap_path(self, path: str) -> None:
        """Configure the path to OWASP ZAP installation."""
        self.zap_path = path