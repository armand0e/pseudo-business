"""
Evolution Engine - Core module for code optimization using evolutionary algorithms.
"""

import logging
from typing import List, Optional

from .code_variant import CodeVariant
from .fitness_evaluator import FitnessEvaluator
from .mutation_operator import MutationOperator
from .selection_mechanism import SelectionMechanism

class EvolutionEngine:
    """
    The Evolution Engine optimizes code using evolutionary algorithms.
    It applies fitness evaluation, mutation operators, and selection mechanisms
    to improve code quality with respect to performance, security,
    maintainability, and test coverage.
    """

    def __init__(
        self,
        population_size: int = 100,
        max_generations: int = 50,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.2
    ):
        """
        Initialize the Evolution Engine.

        Args:
            population_size: Number of code variants in each generation.
            max_generations: Maximum number of generations to evolve.
            mutation_rate: Probability of applying a mutation to a code variant.
            crossover_rate: Probability of applying crossover between variants.
        """
        self.population_size = population_size
        self.max_generations = max_generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate

        self.fitness_evaluator = FitnessEvaluator()
        self.mutation_operator = MutationOperator(mutation_rate)
        self.selection_mechanism = SelectionMechanism()

        self.population: List[CodeVariant] = []
        self.generation = 0
        self.best_variant: Optional[CodeVariant] = None

    def optimize_code(self, codebase: str) -> CodeVariant:
        """
        Optimize the given codebase using evolutionary algorithms.

        Args:
            codebase: The initial code to be optimized.

        Returns:
            The best code variant found during evolution.
        """
        self.initialize_population(codebase)
        self.evolve()

        return self.best_variant

    def initialize_population(self, codebase: str):
        """
        Generate an initial population of code variants from the given codebase.
        """
        logging.info(f"Initializing population with {self.population_size} variants")
        for _ in range(self.population_size):
            variant = CodeVariant(codebase)
            self.population.append(variant)

    def evolve(self):
        """
        Execute the evolution process, including fitness evaluation,
        selection, and mutation.
        """
        logging.info(f"Starting evolution process for {self.max_generations} generations")

        for generation in range(1, self.max_generations + 1):
            self.generation = generation
            logging.debug(f"Generation {generation}: Evaluating fitness")

            # Evaluate fitness of each variant
            self.fitness_evaluator.evaluate_population(self.population)

            # Track the best variant so far
            self.best_variant = max(self.population, key=lambda v: v.fitness_score.total_score)
            logging.debug(f"Best score in generation {generation}: {self.best_variant.fitness_score.total_score}")

            # Select parents for next generation
            parents = self.selection_mechanism.select(self.population)

            # Create new population through crossover and mutation
            new_population = []
            for _ in range(self.population_size):
                parent1, parent2 = self._select_parents(parents)
                child = self._crossover(parent1, parent2) if self._should_crossover() else parent1.clone()
                if self._should_mutate():
                    self.mutation_operator.mutate(child)

                new_population.append(child)

            # Replace old population with new generation
            self.population = new_population

        logging.info(f"Evolution completed after {self.max_generations} generations")
        logging.info(f"Best variant score: {self.best_variant.fitness_score.total_score}")

    def _select_parents(self, parents: List[CodeVariant]) -> (CodeVariant, CodeVariant):
        """
        Select two parent code variants for reproduction.
        """
        return self.selection_mechanism.select_two(parents)

    def _crossover(self, parent1: CodeVariant, parent2: CodeVariant) -> CodeVariant:
        """
        Perform crossover between two parent code variants to create a child variant.
        """
        logging.debug("Performing crossover between parents")
        # Simple implementation - could be enhanced with more sophisticated strategies
        return parent1.crossover(parent2)

    def _should_crossover(self) -> bool:
        """
        Determine if crossover should be applied based on the crossover rate.
        """
        return self._random_float() < self.crossover_rate

    def _should_mutate(self) -> bool:
        """
        Determine if mutation should be applied based on the mutation rate.
        """
        return self._random_float() < self.mutation_rate

    @staticmethod
    def _random_float() -> float:
        """
        Generate a random float between 0 and 1.
        """
        import random
        return random.random()