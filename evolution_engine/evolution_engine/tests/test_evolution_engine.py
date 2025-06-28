"""
Tests for the Evolution Engine.
"""

import unittest
from unittest.mock import patch, MagicMock

from evolution_engine.evolution_engine import EvolutionEngine
from evolution_engine.code_variant import CodeVariant, FitnessScore

class TestEvolutionEngine(unittest.TestCase):
    """
    Test cases for the Evolution Engine.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.engine = EvolutionEngine(
            population_size=10,
            max_generations=2,
            mutation_rate=0.5
        )

    def test_initialization(self):
        """Test that the engine initializes correctly."""
        self.assertEqual(self.engine.population_size, 10)
        self.assertEqual(self.engine.max_generations, 2)
        self.assertEqual(self.engine.mutation_rate, 0.5)

    @patch('evolution_engine.evolution_engine.FitnessEvaluator')
    def test_optimize_code(self, mock_fitness_evaluator):
        """Test the optimize_code method."""
        # Mock codebase
        codebase = "def example():\n    return 42"

        # Create a mock variant with high fitness score
        mock_variant = MagicMock(spec=CodeVariant)
        mock_variant.codebase = "optimized_code"
        mock_variant.fitness_score = FitnessScore(total_score=1.0)

        # Mock the population initialization and evolution process
        with patch.object(self.engine, 'initialize_population'), \
             patch.object(self.engine, 'evolve'), \
             patch('builtins.max', return_value=mock_variant):

            result = self.engine.optimize_code(codebase)

            self.assertEqual(result.codebase, "optimized_code")

    def test_crossover(self):
        """Test the crossover functionality."""
        # Create two parent variants
        parent1 = CodeVariant("def example():\n    return 42")
        parent2 = CodeVariant("def another_example():\n    return 'hello'")

        # Perform crossover
        child = self.engine._crossover(parent1, parent2)

        # Verify the child is a combination of both parents
        self.assertIsNotNone(child)
        self.assertIsInstance(child, CodeVariant)
        self.assertNotEqual(child.codebase, parent1.codebase)
        self.assertNotEqual(child.codebase, parent2.codebase)

if __name__ == '__main__':
    unittest.main()