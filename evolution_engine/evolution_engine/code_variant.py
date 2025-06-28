"""
Code Variant - Represents an individual in the evolution population.
"""

import copy
import random
from dataclasses import dataclass, field

@dataclass
class FitnessScore:
    """
    Represents a fitness score for a code variant.

    Attributes:
        performance_score: Score for performance (0-1)
        security_score: Score for security (0-1)
        maintainability_score: Score for maintainability (0-1)
        test_coverage_score: Score for test coverage (0-1)
        total_score: Combined score from all metrics
    """
    performance_score: float = 0.0
    security_score: float = 0.0
    maintainability_score: float = 0.0
    test_coverage_score: float = 0.0
    total_score: float = 0.0

class CodeVariant:
    """
    Represents a code variant in the evolution population.
    """

    def __init__(self, codebase: str):
        """Initialize a new code variant."""
        self.codebase = codebase
        self.fitness_score = FitnessScore()

    def clone(self) -> 'CodeVariant':
        """
        Create a deep copy of this code variant.

        Returns:
            A new CodeVariant with the same code and fitness score.
        """
        return copy.deepcopy(self)

    def crossover(self, other: 'CodeVariant') -> 'CodeVariant':
        """
        Perform crossover between two code variants to create a child.

        Args:
            other: The parent code variant to cross with.

        Returns:
            A new CodeVariant that combines elements from both parents.
        """
        # Simple line-based crossover
        lines1 = self.codebase.split('\n')
        lines2 = other.codebase.split('\n')

        # Choose a random crossover point
        crossover_point = random.randint(0, min(len(lines1), len(lines2)))

        # Create child with mixed content
        child_lines = lines1[:crossover_point] + lines2[crossover_point:]

        return CodeVariant('\n'.join(child_lines))