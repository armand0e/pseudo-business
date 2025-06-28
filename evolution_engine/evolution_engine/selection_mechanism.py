"""
Selection Mechanism - Selects the fittest code variants for the next generation.
"""

import logging
import random
from typing import List, Tuple

from .code_variant import CodeVariant

class SelectionMechanism:
    """
    The Selection Mechanism chooses the most optimal code variants
    from a population based on their fitness scores.
    """

    def __init__(self):
        """Initialize the Selection Mechanism."""
        pass

    def select(self, population: List[CodeVariant]) -> List[CodeVariant]:
        """
        Select a subset of the fittest code variants from the population.

        Args:
            population: List of CodeVariant objects to select from.

        Returns:
            A list of selected CodeVariant objects.
        """
        logging.debug(f"Selecting {len(population)} variants from population")

        # Sort by fitness score (descending)
        sorted_population = sorted(population, key=lambda v: v.fitness_score.total_score, reverse=True)

        # Use tournament selection to choose parents
        selected_variants = []
        for _ in range(len(sorted_population)):
            winner = self._tournament_selection(sorted_population)
            selected_variants.append(winner)

        return selected_variants

    def select_two(self, population: List[CodeVariant]) -> Tuple[CodeVariant, CodeVariant]:
        """
        Select two code variants for crossover.

        Args:
            population: List of CodeVariant objects to select from.

        Returns:
            A tuple containing two selected CodeVariant objects.
        """
        logging.debug("Selecting two parents for crossover")
        parent1 = self._tournament_selection(population)
        parent2 = self._tournament_selection(population)

        return parent1, parent2

    def _tournament_selection(self, population: List[CodeVariant]) -> CodeVariant:
        """
        Perform tournament selection to choose a single code variant.

        Args:
            population: List of CodeVariant objects to select from.

        Returns:
            The selected CodeVariant object.
        """
        tournament_size = min(5, len(population))
        tournament = random.sample(population, tournament_size)
        return max(tournament, key=lambda v: v.fitness_score.total_score)

    def _roulette_wheel_selection(self, population: List[CodeVariant]) -> CodeVariant:
        """
        Perform roulette wheel selection to choose a single code variant.

        Args:
            population: List of CodeVariant objects to select from.

        Returns:
            The selected CodeVariant object.
        """
        total_fitness = sum(v.fitness_score.total_score for v in population)
        pick = random.uniform(0, total_fitness)

        current = 0
        for variant in population:
            current += variant.fitness_score.total_score
            if current > pick:
                return variant

        # In case of rounding errors
        return population[-1]