"""Security Scanner Tests.

This module contains tests for the SecurityScanner class and related functionality.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from typing import List, Dict

from testing_agent.security_scanner import SecurityScanner, SecurityIssue

@pytest.fixture
def security_scanner():
    """Create a SecurityScanner instance for testing."""
    return SecurityScanner()

@pytest.fixture
def sample_bandit_output():
    """Sample Bandit JSON output for testing."""
    return {
        "results": [
            {
                "issue_severity": "HIGH",
                "issue_confidence": "HIGH",
                "issue_text": "Possible SQL injection vector",
                "more_info": "SQL injection vulnerability detected",
                "filename": "app/database.py",
                "line_number": 42,
                "code": "cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")",
                "fix": "Use parameterized queries"
            },
            {
                "issue_severity": "MEDIUM",
                "issue_confidence": "MEDIUM",
                "issue_text": "Use of weak cryptographic key",
                "more_info": "Insufficient key length for security",
                "filename": "app/crypto.py",
                "line_number": 23,
                "code": "key = generate_key(size=64)",
                "fix": "Increase key size to at least 128 bits"
            }
        ]
    }

@pytest.fixture
def sample_zap_output():
    """Sample OWASP ZAP JSON output for testing."""
    return [
        {
            "risk": "High",
            "confidence": "Medium",
            "alert": "Cross Site Scripting (XSS)",
            "description": "Cross-site Scripting (XSS) is an attack technique...",
            "url": "http://example.com/page",
            "attack": "<script>alert(1)</script>",
            "solution": "Properly encode all user input"
        },
        {
            "risk": "Medium",
            "confidence": "High",
            "alert": "Missing Security Headers",
            "description": "Missing HTTP security headers detected",
            "url": "http://example.com/api",
            "solution": "Add recommended security headers"
        }
    ]

@pytest.fixture
def sample_python_file():
    """Sample Python file content with security issues."""
    return """
import os
import subprocess

def execute_command(cmd):
    # Unsafe command execution
    return subprocess.call(cmd, shell=True)

def get_user_data(user_id):
    # Potential SQL injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)
"""

def test_scan_python_code_success(security_scanner, sample_bandit_output):
    """Test successful Python code security scanning."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            stdout=json.dumps(sample_bandit_output),
            stderr='',
            returncode=0
        )
        
        issues = security_scanner.scan_python_code('src')
        
        assert len(issues) == 2
        assert any(issue.severity == "HIGH" for issue in issues)
        assert any(issue.issue_type == "Possible SQL injection vector" for issue in issues)

def test_scan_python_code_no_issues(security_scanner):
    """Test Python code scan with no security issues."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            stdout=json.dumps({"results": []}),
            stderr='',
            returncode=0
        )
        
        issues = security_scanner.scan_python_code('src')
        assert len(issues) == 0

def test_scan_python_code_error(security_scanner):
    """Test handling of Python code scan errors."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception("Bandit scan failed")
        
        issues = security_scanner.scan_python_code('src')
        assert len(issues) == 0

def test_scan_web_application_success(security_scanner, sample_zap_output):
    """Test successful web application security scanning."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            stdout=json.dumps(sample_zap_output),
            stderr='',
            returncode=0
        )
        
        issues = security_scanner.scan_web_application('http://example.com')
        
        assert len(issues) == 2
        assert any(issue.severity == "High" for issue in issues)
        assert any(issue.issue_type == "Cross Site Scripting (XSS)" for issue in issues)

def test_scan_web_application_error(security_scanner):
    """Test handling of web application scan errors."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception("ZAP scan failed")
        
        issues = security_scanner.scan_web_application('http://example.com')
        assert len(issues) == 0

def test_generate_security_report(security_scanner, tmp_path):
    """Test generating security report from scan results."""
    issues = [
        SecurityIssue(
            tool="bandit",
            severity="HIGH",
            confidence="HIGH",
            issue_type="SQL Injection",
            description="SQL injection vulnerability",
            file_path="app/db.py",
            line_number=42,
            code="execute_query(user_input)",
            recommendation="Use parameterized queries"
        ),
        SecurityIssue(
            tool="owasp_zap",
            severity="MEDIUM",
            confidence="HIGH",
            issue_type="XSS",
            description="Cross-site scripting vulnerability",
            file_path="http://example.com/page",
            line_number=0,
            code="<script>alert(1)</script>",
            recommendation="Encode user input"
        )
    ]
    
    output_file = tmp_path / "security_report.md"
    security_scanner.generate_security_report(issues, output_file)
    
    assert output_file.exists()
    content = output_file.read_text()
    
    # Check report content
    assert "# Security Scan Report" in content
    assert "## Summary" in content
    assert "Total Issues: 2" in content
    assert "High Severity: 1" in content
    assert "Medium Severity: 1" in content
    assert "SQL Injection" in content
    assert "XSS" in content
    assert "parameterized queries" in content
    assert "encode user input" in content

def test_configure_zap_path(security_scanner):
    """Test configuring OWASP ZAP path."""
    test_path = "/usr/local/bin/zap"
    security_scanner.configure_zap_path(test_path)
    assert security_scanner.zap_path == test_path

def test_security_issue_creation():
    """Test creating SecurityIssue instances."""
    issue = SecurityIssue(
        tool="bandit",
        severity="HIGH",
        confidence="MEDIUM",
        issue_type="Unsafe Import",
        description="Use of unsafe module",
        file_path="app/utils.py",
        line_number=15,
        code="import pickle",
        recommendation="Use safer alternatives"
    )
    
    assert issue.tool == "bandit"
    assert issue.severity == "HIGH"
    assert issue.confidence == "MEDIUM"
    assert issue.issue_type == "Unsafe Import"
    assert issue.line_number == 15
    assert "pickle" in issue.code
    assert "safer alternatives" in issue.recommendation

def test_handle_invalid_bandit_output(security_scanner):
    """Test handling invalid Bandit output format."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            stdout="Invalid JSON",
            stderr='',
            returncode=0
        )
        
        issues = security_scanner.scan_python_code('src')
        assert len(issues) == 0

def test_handle_invalid_zap_output(security_scanner):
    """Test handling invalid OWASP ZAP output format."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            stdout="Invalid JSON",
            stderr='',
            returncode=0
        )
        
        issues = security_scanner.scan_web_application('http://example.com')
        assert len(issues) == 0