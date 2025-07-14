"""CI Integration Tests.

This module contains tests for the CI/CD pipeline integration functionality.
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict

from testing_agent.ci_integration import CIConfig, CIPipelineGenerator, CIResultParser

@pytest.fixture
def ci_config():
    """Create a sample CI configuration for testing."""
    return CIConfig(
        platform="github",
        language="python",
        test_command="pytest --cov=src",
        coverage_threshold=90.0,
        security_scan=True,
        environment_vars={
            "PYTHONPATH": "src",
            "ENVIRONMENT": "test"
        }
    )

@pytest.fixture
def pipeline_generator(ci_config):
    """Create a CIPipelineGenerator instance for testing."""
    return CIPipelineGenerator(ci_config)

@pytest.fixture
def sample_test_results():
    """Sample JUnit XML test results for testing."""
    return """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" errors="0" failures="1" skipped="2" tests="10" time="1.234">
    <testcase classname="test_module" name="test_success" time="0.123"/>
    <testcase classname="test_module" name="test_failure" time="0.234">
      <failure message="assertion failed">test failure details</failure>
    </testcase>
    <testcase classname="test_module" name="test_skipped" time="0.0">
      <skipped type="pytest.skip">skipped for testing</skipped>
    </testcase>
  </testsuite>
</testsuites>"""

def test_ci_config_validation():
    """Test CI configuration validation."""
    # Valid configuration
    config = CIConfig(
        platform="github",
        language="python",
        test_command="pytest",
        coverage_threshold=85.0,
        security_scan=True,
        environment_vars={}
    )
    
    # Invalid platform
    with pytest.raises(ValueError) as exc_info:
        CIPipelineGenerator(CIConfig(
            platform="invalid",
            language="python",
            test_command="pytest",
            coverage_threshold=85.0,
            security_scan=True,
            environment_vars={}
        ))
    assert "Unsupported CI platform" in str(exc_info.value)

def test_generate_github_workflow(pipeline_generator, tmp_path):
    """Test generating GitHub Actions workflow configuration."""
    output_file = tmp_path / ".github/workflows/testing.yml"
    pipeline_generator.generate_pipeline_config(output_file)
    
    assert output_file.exists()
    
    # Parse the generated YAML
    config = yaml.safe_load(output_file.read_text())
    
    # Check basic structure
    assert "name" in config
    assert "on" in config
    assert "jobs" in config
    assert "test" in config["jobs"]
    
    # Check trigger events
    assert "push" in config["on"]
    assert "pull_request" in config["on"]
    
    # Check job configuration
    job = config["jobs"]["test"]
    assert job["runs-on"] == "ubuntu-latest"
    
    # Check steps
    steps = job["steps"]
    assert any(step.get("uses") == "actions/checkout@v3" for step in steps)
    assert any(step.get("uses") == "actions/setup-python@v4" for step in steps)
    
    # Check environment variables
    assert job["env"] == pipeline_generator.config.environment_vars

def test_generate_gitlab_ci(pipeline_generator, tmp_path):
    """Test generating GitLab CI configuration."""
    output_file = tmp_path / ".gitlab-ci.yml"
    pipeline_generator.generate_pipeline_config(output_file)
    
    assert output_file.exists()
    
    # Parse the generated YAML
    config = yaml.safe_load(output_file.read_text())
    
    # Check basic structure
    assert "image" in config
    assert "stages" in config
    assert "test" in config
    
    # Check test job configuration
    test_job = config["test"]
    assert "stage" in test_job
    assert "script" in test_job
    assert pipeline_generator.config.test_command in test_job["script"]
    
    # Check coverage artifacts
    assert "artifacts" in test_job
    assert "reports" in test_job["artifacts"]
    assert "coverage_report" in test_job["artifacts"]["reports"]

def test_generate_jenkinsfile(pipeline_generator, tmp_path):
    """Test generating Jenkinsfile configuration."""
    pipeline_generator.config.platform = "jenkins"
    output_file = tmp_path / "Jenkinsfile"
    pipeline_generator.generate_pipeline_config(output_file)
    
    assert output_file.exists()
    content = output_file.read_text()
    
    # Check pipeline structure
    assert "pipeline {" in content
    assert "agent {" in content
    assert "stages {" in content
    assert "stage('Test')" in content
    
    # Check environment variables
    for key, value in pipeline_generator.config.environment_vars.items():
        assert f"{key} = '{value}'" in content
    
    # Check test command
    assert pipeline_generator.config.test_command in content

def test_generate_azure_pipeline(pipeline_generator, tmp_path):
    """Test generating Azure Pipelines configuration."""
    pipeline_generator.config.platform = "azure"
    output_file = tmp_path / "azure-pipelines.yml"
    pipeline_generator.generate_pipeline_config(output_file)
    
    assert output_file.exists()
    
    # Parse the generated YAML
    config = yaml.safe_load(output_file.read_text())
    
    # Check basic structure
    assert "trigger" in config
    assert "pool" in config
    assert "steps" in config
    
    # Check steps
    steps = config["steps"]
    assert any(step.get("task") == "UsePythonVersion@0" for step in steps)
    assert any(pipeline_generator.config.test_command in step.get("script", "") for step in steps)

def test_parse_test_results_junit(sample_test_results, tmp_path):
    """Test parsing JUnit XML test results."""
    parser = CIResultParser("github")
    results_file = tmp_path / "test-results.xml"
    results_file.write_text(sample_test_results)
    
    results = parser.parse_test_results(results_file)
    
    assert results["tests"] == 10
    assert results["failures"] == 1
    assert results["errors"] == 0
    assert results["skipped"] == 2
    assert isinstance(results["time"], float)

def test_parse_test_results_json(tmp_path):
    """Test parsing JSON test results."""
    parser = CIResultParser("github")
    results_file = tmp_path / "test-results.json"
    
    # Create sample JSON results
    json_results = {
        "tests": 5,
        "failures": 1,
        "errors": 0,
        "skipped": 1,
        "time": 0.789
    }
    
    import json
    results_file.write_text(json.dumps(json_results))
    
    results = parser.parse_test_results(results_file)
    assert results == json_results

def test_parse_test_results_invalid_file(tmp_path):
    """Test handling invalid test results file."""
    parser = CIResultParser("github")
    results_file = tmp_path / "invalid-results.xml"
    results_file.write_text("Invalid content")
    
    results = parser.parse_test_results(results_file)
    assert results == {}

def test_parse_coverage_results_cobertura(tmp_path):
    """Test parsing Cobertura coverage results."""
    parser = CIResultParser("github")
    coverage_file = tmp_path / "coverage.xml"
    
    # Create sample Cobertura XML
    coverage_xml = """<?xml version="1.0" ?>
    <coverage line-rate="0.85" branch-rate="0.75" complexity="25">
    </coverage>"""
    coverage_file.write_text(coverage_xml)
    
    results = parser.parse_coverage_results(coverage_file)
    
    assert results["line_rate"] == 85.0
    assert results["branch_rate"] == 75.0
    assert results["complexity"] == 25.0

def test_parse_coverage_results_json(tmp_path):
    """Test parsing JSON coverage results."""
    parser = CIResultParser("github")
    coverage_file = tmp_path / "coverage.json"
    
    coverage_data = {
        "line_rate": 90.5,
        "branch_rate": 85.5,
        "complexity": 30
    }
    
    import json
    coverage_file.write_text(json.dumps(coverage_data))
    
    results = parser.parse_coverage_results(coverage_file)
    assert results == coverage_data

def test_parse_security_results(tmp_path):
    """Test parsing security scan results."""
    parser = CIResultParser("github")
    security_file = tmp_path / "security-report.json"
    
    security_data = {
        "results": [
            {
                "issue_severity": "high",
                "issue_confidence": "high",
                "issue_text": "SQL Injection"
            },
            {
                "issue_severity": "medium",
                "issue_confidence": "medium",
                "issue_text": "Weak Crypto"
            }
        ]
    }
    
    import json
    security_file.write_text(json.dumps(security_data))
    
    results = parser.parse_security_results(security_file)
    
    assert results["total_issues"] == 2
    assert results["severity_counts"]["high"] == 1
    assert results["severity_counts"]["medium"] == 1

def test_parse_security_results_empty(tmp_path):
    """Test parsing security results with no issues."""
    parser = CIResultParser("github")
    security_file = tmp_path / "security-report.json"
    
    security_data = {"results": []}
    
    import json
    security_file.write_text(json.dumps(security_data))
    
    results = parser.parse_security_results(security_file)
    
    assert results["total_issues"] == 0
    assert all(count == 0 for count in results["severity_counts"].values())

def test_generate_pipeline_output_directory(pipeline_generator, tmp_path):
    """Test pipeline generation creates output directory if needed."""
    output_file = tmp_path / "nested/dir/pipeline.yml"
    pipeline_generator.generate_pipeline_config(output_file)
    
    assert output_file.parent.exists()
    assert output_file.exists()

def test_ci_config_defaults():
    """Test CI configuration defaults."""
    minimal_config = CIConfig(
        platform="github",
        language="python",
        test_command="pytest",
        coverage_threshold=80.0,
        security_scan=False,
        environment_vars={}
    )
    
    generator = CIPipelineGenerator(minimal_config)
    assert generator.config.security_scan is False
    assert generator.config.environment_vars == {}

def test_parse_results_invalid_json(tmp_path):
    """Test handling invalid JSON in results parsing."""
    parser = CIResultParser("github")
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("Invalid JSON content")
    
    assert parser.parse_test_results(invalid_file) == {}
    assert parser.parse_coverage_results(invalid_file) == {}
    assert parser.parse_security_results(invalid_file) == {}