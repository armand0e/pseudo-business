"""Test Generator Module.

This module is responsible for generating various types of tests (unit, integration, end-to-end)
based on the analyzed codebase.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Union
import ast2json

@dataclass
class TestSpec:
    """Specification for a test case."""
    name: str
    description: str
    test_type: str  # "unit", "integration", "e2e"
    dependencies: List[str]
    inputs: Dict[str, str]
    expected_outputs: Dict[str, str]

class TestGenerator:
    """Generates test suites for different testing levels."""

    def __init__(self):
        self.analyzed_files: Dict[str, ast.AST] = {}

    def analyze_source_file(self, file_path: Union[str, Path]) -> ast.AST:
        """Analyze a source file and create its AST."""
        file_path = Path(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        return ast.parse(source)

    def generate_unit_tests(self, source_file: Union[str, Path]) -> List[TestSpec]:
        """Generate unit tests for a given source file."""
        ast_tree = self.analyze_source_file(source_file)
        test_specs = []

        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                test_spec = self._create_unit_test_spec(node)
                test_specs.append(test_spec)

        return test_specs

    def generate_integration_tests(
        self, 
        source_files: List[Union[str, Path]], 
        endpoints: List[str]
    ) -> List[TestSpec]:
        """Generate integration tests for a set of components."""
        test_specs = []
        
        for endpoint in endpoints:
            test_spec = TestSpec(
                name=f"test_integration_{endpoint.replace('/', '_')}",
                description=f"Integration test for endpoint {endpoint}",
                test_type="integration",
                dependencies=[str(f) for f in source_files],
                inputs={"endpoint": endpoint},
                expected_outputs={"status_code": "200"}
            )
            test_specs.append(test_spec)

        return test_specs

    def generate_e2e_tests(
        self, 
        workflow_specs: List[Dict[str, str]]
    ) -> List[TestSpec]:
        """Generate end-to-end tests for user workflows."""
        test_specs = []

        for spec in workflow_specs:
            test_spec = TestSpec(
                name=f"test_e2e_{spec['name']}",
                description=f"End-to-end test for {spec['description']}",
                test_type="e2e",
                dependencies=spec.get('dependencies', []),
                inputs=spec.get('inputs', {}),
                expected_outputs=spec.get('expected_outputs', {})
            )
            test_specs.append(test_spec)

        return test_specs

    def _create_unit_test_spec(self, node: ast.FunctionDef) -> TestSpec:
        """Create a test specification for a function."""
        return TestSpec(
            name=f"test_{node.name}",
            description=f"Unit test for function {node.name}",
            test_type="unit",
            dependencies=[],
            inputs=self._extract_function_params(node),
            expected_outputs={"result": "expected_value"}  # Placeholder
        )

    def _extract_function_params(self, node: ast.FunctionDef) -> Dict[str, str]:
        """Extract function parameters and their types."""
        params = {}
        for arg in node.args.args:
            arg_type = "Any"  # Default type
            if arg.annotation and isinstance(arg.annotation, ast.Name):
                arg_type = arg.annotation.id
            params[arg.arg] = arg_type
        return params

    def generate_pytest_file(self, test_specs: List[TestSpec], output_file: Union[str, Path]) -> None:
        """Generate a pytest file from test specifications."""
        output_file = Path(output_file)
        template = []
        
        # Add imports
        template.append("import pytest")
        template.append("from unittest.mock import Mock, patch")
        template.append("")
        
        # Add fixtures if needed
        template.append("@pytest.fixture")
        template.append("def mock_dependencies():")
        template.append("    return Mock()")
        template.append("")
        
        # Add test functions
        for spec in test_specs:
            template.extend(self._generate_test_function(spec))
            template.append("")
        
        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(template))

    def _generate_test_function(self, spec: TestSpec) -> List[str]:
        """Generate a pytest function from a test specification."""
        function_lines = []
        
        # Add function definition
        function_lines.append(f"def {spec.name}(mock_dependencies):")
        
        # Add docstring
        function_lines.append(f'    """{spec.description}"""')
        
        # Add mock setup if needed
        if spec.dependencies:
            function_lines.append("    # Mock dependencies")
            for dep in spec.dependencies:
                function_lines.append(f"    with patch('{dep}') as mock:")
                function_lines.append("        mock.return_value = Mock()")
        
        # Add test implementation
        if spec.test_type == "unit":
            function_lines.extend(self._generate_unit_test_impl(spec))
        elif spec.test_type == "integration":
            function_lines.extend(self._generate_integration_test_impl(spec))
        else:  # e2e
            function_lines.extend(self._generate_e2e_test_impl(spec))
        
        return function_lines

    def _generate_unit_test_impl(self, spec: TestSpec) -> List[str]:
        """Generate unit test implementation."""
        return [
            "    # Arrange",
            "    expected_result = None  # TODO: Set expected result",
            "",
            "    # Act",
            "    result = None  # TODO: Call function under test",
            "",
            "    # Assert",
            "    assert result == expected_result"
        ]

    def _generate_integration_test_impl(self, spec: TestSpec) -> List[str]:
        """Generate integration test implementation."""
        return [
            "    # Arrange",
            "    # TODO: Set up integration test context",
            "",
            "    # Act",
            f"    response = None  # TODO: Call endpoint {spec.inputs.get('endpoint')}",
            "",
            "    # Assert",
            "    assert response.status_code == 200"
        ]

    def _generate_e2e_test_impl(self, spec: TestSpec) -> List[str]:
        """Generate end-to-end test implementation."""
        return [
            "    # Arrange",
            "    # TODO: Set up end-to-end test context",
            "",
            "    # Act",
            "    # TODO: Execute workflow steps",
            "",
            "    # Assert",
            "    # TODO: Verify workflow results"
        ]