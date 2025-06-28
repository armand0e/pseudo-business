"""
AST Utilities - Helper functions for AST manipulation in code evolution.
"""

import ast
import logging

class ASTUtils:
    """
    Utility class for working with Abstract Syntax Trees (ASTs) in Python code.
    """

    @staticmethod
    def parse_code(code: str) -> ast.AST:
        """
        Parse a string of Python code into an AST.

        Args:
            code: The Python code to parse.

        Returns:
            An AST object representing the code structure.
        """
        try:
            return ast.parse(code)
        except SyntaxError as e:
            logging.error(f"Syntax error in code: {e}")
            raise

    @staticmethod
    def unparse_tree(tree: ast.AST) -> str:
        """
        Convert an AST back into Python source code.

        Args:
            tree: The AST to convert.

        Returns:
            A string containing the Python source code.
        """
        try:
            return ast.unparse(tree)
        except Exception as e:
            logging.error(f"Error unparsing AST: {e}")
            raise

    @staticmethod
    def find_nodes_by_type(tree: ast.AST, node_type: type) -> list:
        """
        Find all nodes of a specific type in an AST.

        Args:
            tree: The AST to search.
            node_type: The type of node to find (e.g., ast.FunctionDef).

        Returns:
            A list of nodes matching the specified type.
        """
        return [node for node in ast.walk(tree) if isinstance(node, node_type)]

    @staticmethod
    def replace_node(original_tree: ast.AST, old_node: ast.AST, new_node: ast.AST) -> ast.AST:
        """
        Replace a node in an AST with a new node.

        Args:
            original_tree: The original AST.
            old_node: The node to replace.
            new_node: The replacement node.

        Returns:
            A new AST with the node replaced.
        """
        # Create a deep copy of the tree
        tree_copy = ast.parse(ast.unparse(original_tree))

        # Replace the node
        for node in ast.walk(tree_copy):
            if node == old_node:
                # Replace the node's parent's reference to it
                parent = ASTUtils._get_parent_map(tree_copy)[old_node]
                ASTUtils._replace_in_parent(parent, old_node, new_node)

        return tree_copy

    @staticmethod
    def _get_parent_map(tree: ast.AST) -> dict:
        """
        Create a mapping of each node to its parent in the AST.

        Args:
            tree: The AST to process.

        Returns:
            A dictionary mapping nodes to their parent nodes.
        """
        parent_map = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parent_map[child] = node
        return parent_map

    @staticmethod
    def _replace_in_parent(parent: ast.AST, old_node: ast.AST, new_node: ast.AST):
        """
        Replace a child node in a parent node.

        Args:
            parent: The parent node.
            old_node: The child node to replace.
            new_node: The replacement node.
        """
        # Handle different parent-child relationships
        for field_name, field_value in ast.iter_fields(parent):
            if isinstance(field_value, list):
                try:
                    index = field_value.index(old_node)
                    field_value[index] = new_node
                except ValueError:
                    pass  # Node not found in this list
            elif field_value is old_node:
                setattr(parent, field_name, new_node)

    @staticmethod
    def extract_function_definitions(tree: ast.AST) -> list:
        """
        Extract all function definitions from an AST.

        Args:
            tree: The AST to search.

        Returns:
            A list of FunctionDef nodes.
        """
        return ASTUtils.find_nodes_by_type(tree, ast.FunctionDef)

    @staticmethod
    def extract_class_definitions(tree: ast.AST) -> list:
        """
        Extract all class definitions from an AST.

        Args:
            tree: The AST to search.

        Returns:
            A list of ClassDef nodes.
        """
        return ASTUtils.find_nodes_by_type(tree, ast.ClassDef)