"""
Tests for the Mutation Operator.
"""

import unittest

from evolution_engine.code_variant import CodeVariant
from evolution_engine.mutation_operator import MutationOperator

class TestMutationOperator(unittest.TestCase):
    """
    Test cases for the Mutation Operator.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.operator = MutationOperator(mutation_rate=1.0)  # Always mutate
        self.code_variant = CodeVariant("def example():\n    return 42")

    def test_mutate(self):
        """Test the mutate method."""
        mutated = self.operator.mutate(self.code_variant)

        # Verify we get a new variant with potentially different code
        self.assertIsInstance(mutated, CodeVariant)
        self.assertIsNot(mutated, self.code_variant)  # Should be a new object

    def test_mutation_types(self):
        """Test that different mutation types are applied."""
        # Test refactoring mutation
        variant1 = CodeVariant("def example():\n    result = 0\n    for i in range(5):\n        result += i\n    return result")
        mutated1 = self.operator.mutate(variant1)
        self.assertNotEqual(mutated1.codebase, variant1.codebase)

        # Test optimization mutation
        variant2 = CodeVariant("def example():\n    result = 0\n    for i in range(5):\n        result += i\n    return result")
        mutated2 = self.operator.mutate(variant2)
        self.assertNotEqual(mutated2.codebase, variant2.codebase)

if __name__ == '__main__':
    unittest.main()