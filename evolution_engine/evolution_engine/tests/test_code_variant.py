"""
Tests for the Code Variant.
"""

import unittest

from evolution_engine.code_variant import CodeVariant, FitnessScore

class TestCodeVariant(unittest.TestCase):
    """
    Test cases for the Code Variant.
    """

    def test_initialization(self):
        """Test that a code variant initializes correctly."""
        code = "def example():\n    return 42"
        variant = CodeVariant(code)

        self.assertEqual(variant.codebase, code)
        self.assertIsInstance(variant.fitness_score, FitnessScore)

    def test_clone(self):
        """Test cloning a code variant."""
        original = CodeVariant("def example():\n    return 42")
        clone = original.clone()

        # Verify the clone is a new object with the same content
        self.assertIsNot(original, clone)
        self.assertEqual(original.codebase, clone.codebase)

    def test_crossover(self):
        """Test crossover between two code variants."""
        parent1 = CodeVariant("def example():\n    return 42")
        parent2 = CodeVariant("def another_example():\n    return 'hello'")

        child = parent1.crossover(parent2)

        # Verify the child is a new variant with combined content
        self.assertIsInstance(child, CodeVariant)
        self.assertNotEqual(child.codebase, parent1.codebase)
        self.assertNotEqual(child.codebase, parent2.codebase)

if __name__ == '__main__':
    unittest.main()