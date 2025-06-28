"""
Tests for the AST Utilities.
"""

import unittest
import ast

from evolution_engine.utils.ast_utils import ASTUtils

class TestASTUtils(unittest.TestCase):
    """
    Test cases for the AST Utilities.
    """

    def test_parse_code(self):
        """Test parsing code into an AST."""
        code = "def example():\n    return 42"
        tree = ASTUtils.parse_code(code)

        self.assertIsInstance(tree, ast.AST)
        self.assertEqual(len(tree.body), 1)
        self.assertIsInstance(tree.body[0], ast.FunctionDef)

    def test_unparse_tree(self):
        """Test converting an AST back to code."""
        code = "def example():\n    return 42"
        tree = ast.parse(code)
        unparsed = ASTUtils.unparse_tree(tree)

        self.assertEqual(unparsed, code)

    def test_find_nodes_by_type(self):
        """Test finding nodes of a specific type in an AST."""
        code = """
def func1():
    pass

class Class1:
    def method1(self):
        pass
"""
        tree = ast.parse(code)
        functions = ASTUtils.find_nodes_by_type(tree, ast.FunctionDef)

        self.assertEqual(len(functions), 2)
        classes = ASTUtils.find_nodes_by_type(tree, ast.ClassDef)
        self.assertEqual(len(classes), 1)

    def test_replace_node(self):
        """Test replacing a node in an AST."""
        code = "def example():\n    return 42"
        tree = ast.parse(code)

        # Find the return statement
        for node in ast.walk(tree):
            if isinstance(node, ast.Return):
                old_return = node

        # Create a new return statement
        new_return = ast.Return(value=ast.Constant(value="hello"))

        # Replace the node
        new_tree = ASTUtils.replace_node(tree, old_return, new_return)
        unparsed = ASTUtils.unparse_tree(new_tree)

        self.assertEqual(unparsed, "def example():\n    return 'hello'")

if __name__ == '__main__':
    unittest.main()