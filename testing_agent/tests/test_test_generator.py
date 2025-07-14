"""Test Generator Tests.

This module contains tests for the TestGenerator class and related functionality.
"""

import pytest
from pathlib import Path
from typing import List, Dict
from unittest.mock import Mock, patch, mock_open
import ast

from testing_agent.test_generator import TestGenerator, TestSpec

@pytest.fixture
def test_generator():
    """Create a TestGenerator instance for testing."""
    return TestGenerator()

@pytest.fixture
def sample_function_code():
    """Sample Python function code for testing."""
    return '''
def calculate_total(items: list, tax_rate: float = 0.1) -> float:
    """Calculate total cost with tax."""
    subtotal = sum(items)
    return subtotal * (1 + tax_rate)
'''

@pytest.fixture
def sample_api_code():
    """Sample FastAPI router code for testing."""
    return '''
from fastapi import APIRouter, Depends
from typing import List

router = APIRouter()

@router.get("/items")
async def get_items() -> List[dict]:
    return [{"id": 1, "name": "Item 1"}]

@router.post("/items")
async def create_item(item: dict) -> dict:
    return {"id": 2, **item}
'''

def test_analyze_source_file(test_generator, sample_function_code):
    """Test analyzing Python source code."""
    with patch('builtins.open', mock_open(read_data=sample_function_code)):
        ast_tree = test_generator.analyze_source_file('test.py')
    assert isinstance(ast_tree, ast.AST)
    assert any(
        isinstance(node, ast.FunctionDef) and node.name == 'calculate_total'
        for node in ast.walk(ast_tree)
    )

def test_generate_unit_tests(test_generator, sample_function_code):
    """Test generating unit tests from Python code."""
    with patch('builtins.open', mock_open(read_data=sample_function_code)):
        test_specs = test_generator.generate_unit_tests('test.py')
    
    assert len(test_specs) == 1
    spec = test_specs[0]
    assert spec.name == 'test_calculate_total'
    assert spec.test_type == 'unit'
    assert len(spec.inputs) == 2
    assert 'items' in spec.inputs
    assert 'tax_rate' in spec.inputs

def test_generate_integration_tests(test_generator, sample_api_code):
    """Test generating integration tests for API endpoints."""
    with patch('builtins.open', mock_open(read_data=sample_api_code)):
        source_files = [Path('router.py')]
        endpoints = ['/api/items']
        test_specs = test_generator.generate_integration_tests(source_files, endpoints)
    
    assert len(test_specs) == 1
    spec = test_specs[0]
    assert spec.name == 'test_integration_api_items'
    assert spec.test_type == 'integration'
    assert spec.inputs['endpoint'] == '/api/items'
    assert spec.expected_outputs['status_code'] == '200'

def test_generate_e2e_tests(test_generator):
    """Test generating end-to-end tests from workflow specs."""
    workflow_specs = [{
        'name': 'user_registration',
        'description': 'Test user registration flow',
        'dependencies': ['auth_service', 'email_service'],
        'inputs': {'username': 'testuser', 'email': 'test@example.com'},
        'expected_outputs': {'status': 'success'}
    }]

    test_specs = test_generator.generate_e2e_tests(workflow_specs)
    
    assert len(test_specs) == 1
    spec = test_specs[0]
    assert spec.name == 'test_e2e_user_registration'
    assert spec.test_type == 'e2e'
    assert len(spec.dependencies) == 2
    assert spec.inputs['username'] == 'testuser'
    assert spec.expected_outputs['status'] == 'success'

def test_extract_function_params(test_generator):
    """Test extracting function parameters with type annotations."""
    code = '''
def process_data(items: List[dict], config: Dict[str, str], debug: bool = False) -> dict:
    pass
'''
    tree = ast.parse(code)
    function_def = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    
    params = test_generator._extract_function_params(function_def)
    
    assert len(params) == 3
    assert params['items'] == 'List'  # Note: Gets only base type
    assert params['config'] == 'Dict'
    assert params['debug'] == 'bool'

def test_generate_pytest_file(test_generator, tmp_path):
    """Test generating a pytest file from test specifications."""
    test_specs = [
        TestSpec(
            name='test_example',
            description='Example test case',
            test_type='unit',
            dependencies=['module.function'],
            inputs={'param1': 'str'},
            expected_outputs={'result': 'success'}
        )
    ]
    
    output_file = tmp_path / 'test_output.py'
    test_generator.generate_pytest_file(test_specs, output_file)
    
    assert output_file.exists()
    content = output_file.read_text()
    
    # Check for key components
    assert 'import pytest' in content
    assert 'from unittest.mock import Mock, patch' in content
    assert '@pytest.fixture' in content
    assert 'def test_example(mock_dependencies):' in content
    assert "with patch('module.function')" in content

def test_generate_test_function(test_generator):
    """Test generating a pytest function from a test specification."""
    spec = TestSpec(
        name='test_feature',
        description='Test important feature',
        test_type='unit',
        dependencies=['service.feature'],
        inputs={'input1': 'value1'},
        expected_outputs={'result': 'success'}
    )
    
    function_lines = test_generator._generate_test_function(spec)
    
    assert any(line.startswith('def test_feature') for line in function_lines)
    assert any('"""Test important feature"""' in line for line in function_lines)
    assert any("with patch('service.feature')" in line for line in function_lines)
    assert any('# Arrange' in line for line in function_lines)
    assert any('# Act' in line for line in function_lines)
    assert any('# Assert' in line for line in function_lines)

def test_generate_unit_test_impl(test_generator):
    """Test generating unit test implementation."""
    spec = TestSpec(
        name='test_calculation',
        description='Test calculation function',
        test_type='unit',
        dependencies=[],
        inputs={'x': 'int', 'y': 'int'},
        expected_outputs={'result': '10'}
    )
    
    impl_lines = test_generator._generate_unit_test_impl(spec)
    
    assert '# Arrange' in impl_lines
    assert 'expected_result = None' in impl_lines
    assert '# Act' in impl_lines
    assert 'result = None' in impl_lines
    assert '# Assert' in impl_lines
    assert 'assert result == expected_result' in impl_lines

def test_generate_integration_test_impl(test_generator):
    """Test generating integration test implementation."""
    spec = TestSpec(
        name='test_api_endpoint',
        description='Test API endpoint',
        test_type='integration',
        dependencies=[],
        inputs={'endpoint': '/api/data'},
        expected_outputs={'status_code': '200'}
    )
    
    impl_lines = test_generator._generate_integration_test_impl(spec)
    
    assert '# Arrange' in impl_lines
    assert 'response = None' in impl_lines
    assert 'assert response.status_code == 200' in impl_lines

def test_generate_e2e_test_impl(test_generator):
    """Test generating end-to-end test implementation."""
    spec = TestSpec(
        name='test_workflow',
        description='Test complete workflow',
        test_type='e2e',
        dependencies=[],
        inputs={'action': 'start'},
        expected_outputs={'status': 'completed'}
    )
    
    impl_lines = test_generator._generate_e2e_test_impl(spec)
    
    assert '# Arrange' in impl_lines
    assert '# TODO: Set up end-to-end test context' in impl_lines
    assert '# TODO: Execute workflow steps' in impl_lines
    assert '# TODO: Verify workflow results' in impl_lines