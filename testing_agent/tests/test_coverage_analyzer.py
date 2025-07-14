"""Coverage Analyzer Tests.

This module contains tests for the CoverageAnalyzer class and related functionality.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import xml.etree.ElementTree as ET
from typing import Dict

from testing_agent.coverage_analyzer import CoverageAnalyzer, CoverageMetrics

@pytest.fixture
def coverage_analyzer():
    """Create a CoverageAnalyzer instance for testing."""
    return CoverageAnalyzer()

@pytest.fixture
def sample_coverage_xml():
    """Sample coverage XML output for testing."""
    return """<?xml version="1.0" ?>
<coverage version="6.4.4" timestamp="1627884800" lines-valid="100" lines-covered="85" line-rate="0.85" branches-covered="17" branches-valid="20" branch-rate="0.85" complexity="25">
    <packages>
        <package name="app" line-rate="0.85" branch-rate="0.85" complexity="25">
            <classes>
                <class name="app.main" filename="app/main.py" line-rate="0.90" branch-rate="0.88" complexity="12">
                    <lines>
                        <line number="1" hits="1" branch="false"/>
                        <line number="2" hits="1" branch="false"/>
                        <line number="3" hits="0" branch="true"/>
                        <line number="4" hits="1" branch="true"/>
                    </lines>
                </class>
                <class name="app.utils" filename="app/utils.py" line-rate="0.80" branch-rate="0.82" complexity="8">
                    <lines>
                        <line number="1" hits="1" branch="false"/>
                        <line number="2" hits="0" branch="true"/>
                        <line number="3" hits="1" branch="false"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>
"""

@pytest.fixture
def sample_coverage_json():
    """Sample coverage JSON output for testing."""
    return {
        "meta": {
            "version": "6.4.4",
            "timestamp": "1627884800",
            "branch_coverage": True
        },
        "files": {
            "app/main.py": {
                "executed_lines": [1, 2, 4],
                "missing_lines": [3],
                "excluded_lines": [],
                "executed_branches": [4],
                "missing_branches": [3],
                "summary": {
                    "covered_lines": 3,
                    "num_statements": 4,
                    "percent_covered": 90.0,
                    "missing_lines": 1,
                    "excluded_lines": 0
                }
            }
        },
        "totals": {
            "covered_lines": 85,
            "num_statements": 100,
            "percent_covered": 85.0,
            "missing_lines": 15,
            "excluded_lines": 0
        }
    }

def test_setup_coverage_config(coverage_analyzer, tmp_path):
    """Test setting up coverage configuration."""
    source_dirs = ['src', 'app']
    coverage_analyzer.setup_coverage_config(source_dirs)
    
    config_path = Path('.coveragerc')
    assert config_path.exists()
    
    content = config_path.read_text()
    assert '[run]' in content
    assert 'source = src,app' in content
    assert 'branch = True' in content
    assert '[report]' in content
    assert 'pragma: no cover' in content

def test_run_coverage_analysis_success(coverage_analyzer, tmp_path, sample_coverage_xml):
    """Test successful coverage analysis run."""
    output_dir = tmp_path / 'coverage'
    
    with patch('subprocess.run') as mock_run, \
         patch('xml.etree.ElementTree.parse') as mock_parse:
        
        # Mock the coverage run and report generation
        mock_run.return_value = Mock(returncode=0)
        
        # Mock the XML parsing
        mock_tree = Mock()
        mock_tree.getroot.return_value = ET.fromstring(sample_coverage_xml)
        mock_parse.return_value = mock_tree
        
        metrics = coverage_analyzer.run_coverage_analysis('pytest', output_dir)
        
        assert len(metrics) == 2
        assert 'app/main.py' in metrics
        assert 'app/utils.py' in metrics
        
        main_metrics = metrics['app/main.py']
        assert main_metrics.line_rate == 0.90
        assert main_metrics.branch_rate == 0.88
        assert main_metrics.complexity == 12
        assert main_metrics.covered_lines == 3
        assert main_metrics.total_lines == 4

def test_run_coverage_analysis_error(coverage_analyzer, tmp_path):
    """Test handling coverage analysis errors."""
    output_dir = tmp_path / 'coverage'
    
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception('Coverage run failed')
        
        metrics = coverage_analyzer.run_coverage_analysis('pytest', output_dir)
        assert metrics == {}

def test_parse_coverage_data(coverage_analyzer, tmp_path, sample_coverage_xml):
    """Test parsing coverage data from XML report."""
    output_dir = tmp_path / 'coverage'
    output_dir.mkdir(parents=True, exist_ok=True)
    xml_path = output_dir / 'coverage.xml'
    
    # Write sample XML
    xml_path.write_text(sample_coverage_xml)
    
    metrics = coverage_analyzer.parse_coverage_data(output_dir)
    
    assert len(metrics) == 2
    assert all(isinstance(m, CoverageMetrics) for m in metrics.values())
    
    main_metrics = metrics['app/main.py']
    assert main_metrics.line_rate == 0.90
    assert main_metrics.branch_rate == 0.88
    assert main_metrics.complexity == 12
    assert 3 in main_metrics.uncovered_lines  # Line with hits="0"

def test_generate_coverage_report_above_threshold(coverage_analyzer, tmp_path):
    """Test generating coverage report with coverage above threshold."""
    metrics = {
        'app/main.py': CoverageMetrics(
            line_rate=0.95,
            branch_rate=0.90,
            complexity=10,
            covered_lines=95,
            total_lines=100,
            uncovered_lines=[10, 20, 30, 40, 50],
            covered_branches=18,
            total_branches=20,
            file_path='app/main.py'
        ),
        'app/utils.py': CoverageMetrics(
            line_rate=0.90,
            branch_rate=0.85,
            complexity=5,
            covered_lines=45,
            total_lines=50,
            uncovered_lines=[5, 15, 25, 35, 45],
            covered_branches=17,
            total_branches=20,
            file_path='app/utils.py'
        )
    }
    
    output_file = tmp_path / 'coverage_report.md'
    result = coverage_analyzer.generate_coverage_report(
        metrics,
        output_file,
        min_coverage=90.0
    )
    
    assert result is True  # Coverage meets threshold
    assert output_file.exists()
    
    content = output_file.read_text()
    assert '# Code Coverage Report' in content
    assert 'Overall Coverage: 93.33%' in content
    assert 'Files Analyzed: 2' in content
    assert 'Total Lines: 150' in content
    assert 'Coverage Threshold: 90.0%' in content
    assert 'app/main.py' in content
    assert 'Line Coverage: 95.00%' in content
    assert 'Uncovered Lines:' in content
    assert '10, 20, 30, 40, 50' in content

def test_generate_coverage_report_below_threshold(coverage_analyzer, tmp_path):
    """Test generating coverage report with coverage below threshold."""
    metrics = {
        'app/low_coverage.py': CoverageMetrics(
            line_rate=0.70,
            branch_rate=0.65,
            complexity=8,
            covered_lines=70,
            total_lines=100,
            uncovered_lines=list(range(71, 101)),
            covered_branches=13,
            total_branches=20,
            file_path='app/low_coverage.py'
        )
    }
    
    output_file = tmp_path / 'coverage_report.md'
    result = coverage_analyzer.generate_coverage_report(
        metrics,
        output_file,
        min_coverage=90.0
    )
    
    assert result is False  # Coverage below threshold
    assert output_file.exists()
    
    content = output_file.read_text()
    assert 'Overall Coverage: 70.00%' in content
    assert 'Coverage Threshold: 90.0%' in content

def test_export_coverage_badge_high_coverage(coverage_analyzer, tmp_path):
    """Test generating coverage badge for high coverage."""
    metrics = {
        'app/main.py': CoverageMetrics(
            line_rate=0.95,
            branch_rate=0.90,
            complexity=10,
            covered_lines=95,
            total_lines=100,
            uncovered_lines=[],
            covered_branches=18,
            total_branches=20,
            file_path='app/main.py'
        )
    }
    
    output_file = tmp_path / 'coverage-badge.svg'
    
    with patch('subprocess.run') as mock_run:
        coverage_analyzer.export_coverage_badge(metrics, output_file)
        
        mock_run.assert_called_once()
        command = mock_run.call_args[0][0]
        assert 'coverage-95.0%25-success' in command[2]

def test_export_coverage_badge_low_coverage(coverage_analyzer, tmp_path):
    """Test generating coverage badge for low coverage."""
    metrics = {
        'app/low.py': CoverageMetrics(
            line_rate=0.60,
            branch_rate=0.55,
            complexity=5,
            covered_lines=60,
            total_lines=100,
            uncovered_lines=[],
            covered_branches=11,
            total_branches=20,
            file_path='app/low.py'
        )
    }
    
    output_file = tmp_path / 'coverage-badge.svg'
    
    with patch('subprocess.run') as mock_run:
        coverage_analyzer.export_coverage_badge(metrics, output_file)
        
        mock_run.assert_called_once()
        command = mock_run.call_args[0][0]
        assert 'coverage-60.0%25-red' in command[2]

def test_metrics_calculation_empty_files(coverage_analyzer, tmp_path):
    """Test coverage metrics calculation with no files."""
    metrics = {}
    output_file = tmp_path / 'coverage_report.md'
    
    result = coverage_analyzer.generate_coverage_report(
        metrics,
        output_file,
        min_coverage=90.0
    )
    
    assert result is False
    assert output_file.exists()
    content = output_file.read_text()
    assert 'Overall Coverage: 0.00%' in content
    assert 'Files Analyzed: 0' in content

def test_handle_invalid_coverage_xml(coverage_analyzer, tmp_path):
    """Test handling invalid coverage XML data."""
    output_dir = tmp_path / 'coverage'
    output_dir.mkdir(parents=True, exist_ok=True)
    xml_path = output_dir / 'coverage.xml'
    
    # Write invalid XML
    xml_path.write_text('Invalid XML content')
    
    metrics = coverage_analyzer.parse_coverage_data(output_dir)
    assert metrics == {}

def test_coverage_metrics_dataclass():
    """Test CoverageMetrics dataclass creation and access."""
    metrics = CoverageMetrics(
        line_rate=0.85,
        branch_rate=0.80,
        complexity=15,
        covered_lines=85,
        total_lines=100,
        uncovered_lines=[1, 2, 3],
        covered_branches=16,
        total_branches=20,
        file_path='test.py'
    )
    
    assert metrics.line_rate == 0.85
    assert metrics.branch_rate == 0.80
    assert metrics.complexity == 15
    assert metrics.covered_lines == 85
    assert metrics.total_lines == 100
    assert metrics.uncovered_lines == [1, 2, 3]
    assert metrics.covered_branches == 16
    assert metrics.total_branches == 20
    assert metrics.file_path == 'test.py'