# Testing Agent

The Testing Agent component of the Agentic AI Development Platform ensures system quality by generating comprehensive test suites, performing security scans, and analyzing code coverage.

## Features

- **Test Generation**: Automatically creates unit, integration, and end-to-end tests based on codebase analysis
- **Security Scanning**: Identifies vulnerabilities using tools like Bandit and OWASP ZAP
- **Coverage Analysis**: Tracks and reports code coverage metrics
- **CI/CD Integration**: Seamlessly integrates with CI/CD pipelines like GitHub Actions, GitLab CI, Jenkins, and Azure Pipelines

## Architecture

The Testing Agent consists of several specialized modules:

- **TestGenerator**: Creates test suites for different testing levels
- **SecurityScanner**: Performs static and dynamic security analysis
- **CoverageAnalyzer**: Measures and reports code coverage
- **CIPipelineGenerator**: Generates CI/CD pipeline configurations
- **TestingAgent**: Coordinates all testing operations

## Installation

```bash
pip install -e ./testing_agent
```

## Usage

```python
from testing_agent.agent import TestingAgent, TestingConfig

# Configure testing agent
config = TestingConfig(
    source_dirs=['src', 'app'],
    test_output_dir='test_results',
    security_output_dir='security_results',
    coverage_output_dir='coverage_results',
    min_coverage=90.0,
    enable_security_scan=True
)

# Create and run testing agent
agent = TestingAgent(config)
result = await agent.execute_testing_pipeline()

# Check results
if result.coverage_pass:
    print("Coverage threshold met!")
else:
    print("Coverage below threshold!")

# Access reports
test_report_path = result.reports['test']
security_report_path = result.reports['security']
coverage_report_path = result.reports['coverage']
```

## CI/CD Integration

The Testing Agent can generate CI/CD pipeline configurations for various platforms:

```python
from testing_agent.ci_integration import CIConfig, CIPipelineGenerator

# Configure CI pipeline
ci_config = CIConfig(
    platform="github",  # "github", "gitlab", "jenkins", or "azure"
    language="python",
    test_command="pytest --cov=src",
    coverage_threshold=90.0,
    security_scan=True,
    environment_vars={"PYTHONPATH": "src"}
)

# Generate CI configuration
generator = CIPipelineGenerator(ci_config)
generator.generate_pipeline_config(".github/workflows/testing.yml")
```

## Customization

Each component can be customized for specific project needs:

### Custom Security Scans

```python
from testing_agent.security_scanner import SecurityScanner

scanner = SecurityScanner()
scanner.configure_zap_path("/path/to/zap")
issues = scanner.scan_python_code("src")
```

### Custom Coverage Analysis

```python
from testing_agent.coverage_analyzer import CoverageAnalyzer

analyzer = CoverageAnalyzer()
analyzer.setup_coverage_config(["src", "app"])
metrics = analyzer.run_coverage_analysis("pytest", "coverage")
```

## Dependencies

- pytest, pytest-cov, coverage
- bandit (for Python security scanning)
- python-owasp-zap-v2.4 (for web application security scanning)
- ast2json (for code parsing)
- pyyaml (for CI configuration file generation)