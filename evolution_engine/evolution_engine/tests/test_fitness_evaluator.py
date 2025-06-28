"""
Tests for the Fitness Evaluator.
"""

import unittest

from evolution_engine.code_variant import CodeVariant, FitnessScore
from evolution_engine.fitness_evaluator import FitnessEvaluator

class TestFitnessEvaluator(unittest.TestCase):
    """
    Test cases for the Fitness Evaluator.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.evaluator = FitnessEvaluator()
        self.code_variant = CodeVariant("def example():\n    return 42")

    def test_evaluate(self):
        """Test the evaluate method."""
        score = self.evaluator.evaluate(self.code_variant)

        # Verify the score is a FitnessScore object
        self.assertIsInstance(score, FitnessScore)
        self.assertTrue(0.0 <= score.total_score <= 1.0)

    def test_evaluate_population(self):
        """Test evaluating a population of code variants."""
        population = [
            CodeVariant("def example1():\n    return 42"),
            CodeVariant("def example2():\n    return 'hello'")
        ]

        self.evaluator.evaluate_population(population)

        # Verify all variants have fitness scores
        for variant in population:
            self.assertIsInstance(variant.fitness_score, FitnessScore)
            self.assertTrue(0.0 <= variant.fitness_score.total_score <= 1.0)

if __name__ == '__main__':
    unittest.main()