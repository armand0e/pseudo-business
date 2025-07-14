"""Testing Agent Tests.

This module contains tests for the main Testing Agent class that coordinates
test generation, security scanning, and coverage analysis.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, call
from typing import List, Dict, Any

from testing_agent.agent import TestingAgent, TestingConfig, TestingResult
from testing_agent.test_generator import TestSpec
from testing_agent.security_scanner import SecurityIssue
from testing_agent.coverage_analyzer import CoverageMetrics

pytestmark = pytest.mark.asyncio  # Mark all tests as async

@pytest.fixture
def testing_config():
    """Create a testing configuration for tests."""
    return TestingConfig(
        source_dirs=['src', 'tests'],
        test_output_dir='test_output',
        security_output_dir='security_output',
        coverage_output_dir='coverage_output',
        min_coverage=90.0,
        enable_security_scan=True,
        zap_path='/usr/local/bin/zap'
    )

@pytest.fixture
def testing_agent(testing_config):
    """Create a TestingAgent instance for testing."""
    return TestingAgent(testing_config)

@pytest.fixture
def sample_test_specs():
    """Create sample test specifications."""
    return [
        TestSpec(
            name='test_function',
            description='Test basic function',
            test_type='unit',
            dependencies=[],
            inputs={'param': 'str'},
            expected_outputs={'result': 'success'}
        ),
        TestSpec(
            name='test_api_endpoint',
            description='Test API endpoint',
            test_type='integration',
            dependencies=['api_module'],
            inputs={'endpoint': '/api/data'},
            expected_outputs={'status_code': '200'}
        )
    ]

@pytest.fixture
def sample_security_issues():
    """Create sample security issues."""
    return [
        SecurityIssue(
            tool='bandit',
            severity='HIGH',
            confidence='HIGH',
            issue_type='SQL Injection',
            description='SQL injection vulnerability detected',
            file_path='src/database.py',
            line_number=42,
            code='execute_query(user_input)',
            recommendation='Use parameterized queries'
        ),
        SecurityIssue(
            tool='owasp_zap',
            severity='MEDIUM',
            confidence='HIGH',
            issue_type='XSS',
            description='Cross-site scripting vulnerability',
            file_path='http://example.com/page',
            line_number=0,
            code='<script>alert(1)</script>',
            recommendation='Encode user input'
        )
    ]

@pytest.fixture
def sample_coverage_metrics():
    """Create sample coverage metrics."""
    return {
        'src/module1.py': CoverageMetrics(
            line_rate=0.95,
            branch_rate=0.90,
            complexity=10,
            covered_lines=95,
            total_lines=100,
            uncovered_lines=[10, 20, 30, 40, 50],
            covered_branches=18,
            total_branches=20,
            file_path='src/module1.py'
        ),
        'src/module2.py': CoverageMetrics(
            line_rate=0.85,
            branch_rate=0.80,
            complexity=8,
            covered_lines=85,
            total_lines=100,
            uncovered_lines=[15, 25, 35, 45, 55],
            covered_branches=16,
            total_branches=20,
            file_path='src/module2.py'
        )
    }

def test_agent_initialization(testing_agent, testing_config):
    """Test TestingAgent initialization."""
    assert testing_agent.config == testing_config
    assert testing_agent.test_generator is not None
    assert testing_agent.security_scanner is not None
    assert testing_agent.coverage_analyzer is not None

async def test_execute_testing_pipeline_success(
    testing_agent,
    sample_test_specs,
    sample_security_issues,
    sample_coverage_metrics,
    tmp_path
):
    """Test successful execution of the testing pipeline."""
    # Configure test directories
    test_dir = tmp_path / 'test_output'
    security_dir = tmp_path / 'security_output'
    coverage_dir = tmp_path / 'coverage_output'
    testing_agent.config.test_output_dir = str(test_dir)
    testing_agent.config.security_output_dir = str(security_dir)
    testing_agent.config.coverage_output_dir = str(coverage_dir)

    # Mock test generation
    with patch.object(
        testing_agent.test_generator,
        'generate_unit_tests',
        return_value=sample_test_specs
    ) as mock_generate_tests, \
    patch.object(
        testing_agent.security_scanner,
        'scan_python_code',
        return_value=sample_security_issues
    ) as mock_security_scan, \
    patch.object(
        testing_agent.coverage_analyzer,
        'run_coverage_analysis',
        return_value=sample_coverage_metrics
    ) as mock_coverage_analysis, \
    patch.object(
        testing_agent.coverage_analyzer,
        'generate_coverage_report',
        return_value=True
    ) as mock_coverage_report:
        
        result = await testing_agent.execute_testing_pipeline()
        
        # Verify the result
        assert isinstance(result, TestingResult)
        assert result.test_specs == sample_test_specs
        assert result.security_issues == sample_security_issues
        assert result.coverage_metrics == sample_coverage_metrics
        assert result.coverage_pass is True
        
        # Verify reports were generated
        assert result.reports['test'].exists()
        assert result.reports['security'].exists()
        assert result.reports['coverage'].exists()
        assert result.reports['coverage_badge'].exists()

async def test_execute_testing_pipeline_with_security_disabled(
    testing_agent,
    sample_test_specs,
    sample_coverage_metrics,
    tmp_path
):
    """Test testing pipeline execution with security scanning disabled."""
    testing_agent.config.enable_security_scan = False
    test_dir = tmp_path / 'test_output'
    security_dir = tmp_path / 'security_output'
    coverage_dir = tmp_path / 'coverage_output'
    testing_agent.config.test_output_dir = str(test_dir)
    testing_agent.config.security_output_dir = str(security_dir)
    testing_agent.config.coverage_output_dir = str(coverage_dir)

    with patch.object(
        testing_agent.test_generator,
        'generate_unit_tests',
        return_value=sample_test_specs
    ), \
    patch.object(
        testing_agent.security_scanner,
        'scan_python_code'
    ) as mock_security_scan, \
    patch.object(
        testing_agent.coverage_analyzer,
        'run_coverage_analysis',
        return_value=sample_coverage_metrics
    ), \
    patch.object(
        testing_agent.coverage_analyzer,
        'generate_coverage_report',
        return_value=True
    ):
        result = await testing_agent.execute_testing_pipeline()
        
        # Verify security scan was not called
        mock_security_scan.assert_not_called()
        assert len(result.security_issues) == 0

async def test_generate_tests_for_python_files(testing_agent, tmp_path):
    """Test test generation for Python files."""
    # Create sample Python files
    source_dir = tmp_path / 'src'
    source_dir.mkdir()
    (source_dir / 'main.py').write_text('def example(): pass')
    (source_dir / 'test_existing.py').write_text('def test_something(): pass')

    testing_agent.config.source_dirs = [str(source_dir)]

    with patch.object(
        testing_agent.test_generator,
        'generate_unit_tests'
    ) as mock_generate_tests, \
    patch.object(
        testing_agent.test_generator,
        'generate_integration_tests'
    ) as mock_generate_integration_tests:
        
        result = await testing_agent._generate_tests()
        
        # Verify only non-test files were processed
        mock_generate_tests.assert_called_once()
        assert 'main.py' in str(mock_generate_tests.call_args[0][0])
        assert 'test_existing.py' not in str(mock_generate_tests.call_args[0][0])

async def test_generate_tests_with_api_endpoints(testing_agent, tmp_path):
    """Test test generation for API endpoints."""
    # Create sample API router files
    api_dir = tmp_path / 'src' / 'routers'
    api_dir.mkdir(parents=True)
    (api_dir / 'users.py').write_text('''
    from fastapi import APIRouter
    router = APIRouter()
    @router.get("/users")
    def get_users(): pass
    ''')

    testing_agent.config.source_dirs = [str(tmp_path / 'src')]

    with patch.object(
        testing_agent.test_generator,
        'generate_unit_tests'
    ) as mock_generate_tests, \
    patch.object(
        testing_agent.test_generator,
        'generate_integration_tests'
    ) as mock_generate_integration_tests:
        
        result = await testing_agent._generate_tests()
        
        # Verify integration tests were generated for API endpoints
        mock_generate_integration_tests.assert_called_once()
        call_args = mock_generate_integration_tests.call_args[0]
        assert len(call_args[0]) > 0  # Source files
        assert '/api/users' in call_args[1]  # Endpoints

async def test_run_security_scans(testing_agent, tmp_path):
    """Test running security scans."""
    source_dir = tmp_path / 'src'
    source_dir.mkdir()
    (source_dir / 'app.py').write_text('print("example")')

    testing_agent.config.source_dirs = [str(source_dir)]

    with patch.object(
        testing_agent.security_scanner,
        'scan_python_code'
    ) as mock_scan_python:
        
        issues = await testing_agent._run_security_scans()
        
        # Verify each source directory was scanned
        mock_scan_python.assert_called_once_with(source_dir)

async def test_analyze_coverage(testing_agent, tmp_path):
    """Test running coverage analysis."""
    coverage_dir = tmp_path / 'coverage'
    testing_agent.config.coverage_output_dir = str(coverage_dir)

    with patch.object(
        testing_agent.coverage_analyzer,
        'run_coverage_analysis'
    ) as mock_coverage_analysis:
        
        metrics = await testing_agent._analyze_coverage()
        
        # Verify coverage analysis was run
        mock_coverage_analysis.assert_called_once_with(
            'pytest',
            coverage_dir
        )

def test_extract_endpoints(testing_agent):
    """Test extracting API endpoints from files."""
    api_files = [
        Path('routers/users.py'),
        Path('routers/auth.py'),
        Path('controllers/items.py')
    ]
    
    endpoints = testing_agent._extract_endpoints(api_files)
    
    # Verify common endpoints are included
    assert '/api/health' in endpoints
    assert '/api/v1/users' in endpoints
    assert '/api/v1/projects' in endpoints
    assert '/api/v1/tasks' in endpoints

def test_load_workflow_specs(testing_agent):
    """Test loading end-to-end workflow specifications."""
    specs = testing_agent._load_workflow_specs()
    
    # Verify workflow specs are loaded
    assert len(specs) == 2
    assert any(spec['name'] == 'user_registration' for spec in specs)
    assert any(spec['name'] == 'project_creation' for spec in specs)
    
    # Verify workflow spec structure
    for spec in specs:
        assert 'name' in spec
        assert 'description' in spec
        assert 'steps' in spec
        assert len(spec['steps']) > 0

def test_generate_test_summary(testing_agent, sample_test_specs, tmp_path):
    """Test generating test summary report."""
    output_file = tmp_path / 'test_report.md'
    
    testing_agent._generate_test_summary(sample_test_specs, output_file)
    
    assert output_file.exists()
    content = output_file.read_text()
    
    # Verify report content
    assert '# Test Generation Summary' in content
    assert '## Overview' in content
    assert 'Total Tests: 2' in content
    assert 'Unit Tests: 1' in content
    assert 'Integration Tests: 1' in content
    assert 'test_function' in content
    assert 'test_api_endpoint' in content

async def test_execute_testing_pipeline_coverage_fail(
    testing_agent,
    sample_test_specs,
    sample_security_issues,
    sample_coverage_metrics,
    tmp_path
):
    """Test testing pipeline execution with failed coverage threshold."""
    test_dir = tmp_path / 'test_output'
    security_dir = tmp_path / 'security_output'
    coverage_dir = tmp_path / 'coverage_output'
    testing_agent.config.test_output_dir = str(test_dir)
    testing_agent.config.security_output_dir = str(security_dir)
    testing_agent.config.coverage_output_dir = str(coverage_dir)

    with patch.object(
        testing_agent.test_generator,
        'generate_unit_tests',
        return_value=sample_test_specs
    ), \
    patch.object(
        testing_agent.security_scanner,
        'scan_python_code',
        return_value=sample_security_issues
    ), \
    patch.object(
        testing_agent.coverage_analyzer,
        'run_coverage_analysis',
        return_value=sample_coverage_metrics
    ), \
    patch.object(
        testing_agent.coverage_analyzer,
        'generate_coverage_report',
        return_value=False  # Coverage below threshold
    ):
        result = await testing_agent.execute_testing_pipeline()
        
        # Verify result indicates coverage failure
        assert result.coverage_pass is False

def test_testing_config_validation():
    """Test TestingConfig validation."""
    # Valid configuration
    config = TestingConfig(
        source_dirs=['src', 'tests'],
        test_output_dir='test_output',
        security_output_dir='security_output',
        coverage_output_dir='coverage_output',
        min_coverage=90.0,
        enable_security_scan=True,
        zap_path='/usr/local/bin/zap'
    )
    assert config.min_coverage == 90.0
    
    # Invalid coverage threshold
    with pytest.raises(ValueError) as exc_info:
        TestingConfig(
            source_dirs=['src'],
            test_output_dir='test_output',
            security_output_dir='security_output',
            coverage_output_dir='coverage_output',
            min_coverage=101.0  # Invalid value
        )
    assert "Coverage threshold must be between 0 and 100" in str(exc_info.value)