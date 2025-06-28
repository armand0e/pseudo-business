"""
Tests for the Selection Mechanism.
"""

import unittest

from evolution_engine.code_variant import CodeVariant, FitnessScore
from evolution_engine.selection_mechanism import SelectionMechanism

class TestSelectionMechanism(unittest.TestCase):
    """
    Test cases for the Selection Mechanism.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.selector = SelectionMechanism()

    def test_select(self):
        """Test the select method."""
        # Create a population with variants of different fitness
        population = []
        for i in range(10):
            variant = CodeVariant(f"def example{i}():\n    return {i}")
            variant.fitness_score.total_score = i / 10.0  # Scores from 0 to 1
            population.append(variant)

        selected = self.selector.select(population)

        # Verify we get the same number of variants back
        self.assertEqual(len(selected), len(population))

        # Verify selection favors higher fitness scores
        average_score = sum(v.fitness_score.total_score for v in selected) / len(selected)
        self.assertGreater(average_score, 0.5)  # Should be above the population average

    def test_select_two(self):
        """Test selecting two parents for crossover."""
        # Create a population with variants of different fitness
        population = []
        for i in range(10):
            variant = CodeVariant(f"def example{i}():\n    return {i}")
            variant.fitness_score.total_score = i / 10.0
            population.append(variant)

        parent1, parent2 = self.selector.select_two(population)

        # Verify we get two different variants
        self.assertIsNotNone(parent1)
        self.assertIsNotNone(parent2)
        self.assertNotEqual(parent1, parent2)

if __name__ == '__main__':
    unittest.main()