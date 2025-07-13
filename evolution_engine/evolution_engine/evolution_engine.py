from typing import List
from .fitness_evaluator import FitnessEvaluator
from .mutation_operator import MutationOperator
from .selection_mechanism import SelectionMechanism
from .code_variant import CodeVariant

class EvolutionEngine:
    """
    Orchestrates the evolutionary process to optimize a codebase.
    """

    def __init__(self, codebase: str, population_size: int = 50, generations: int = 100):
        self.codebase = codebase
        self.population_size = population_size
        self.generations = generations
        self.fitness_evaluator = FitnessEvaluator()
        self.mutation_operator = MutationOperator()
        self.selection_mechanism = SelectionMechanism()
        self.population: List[CodeVariant] = []

    def initialize_population(self):
        """
        Initializes the population with variants of the original codebase.
        """
        self.population = [CodeVariant(self.codebase) for _ in range(self.population_size)]

    def evolve(self) -> CodeVariant:
        """
        Runs the evolutionary algorithm to find the optimal code variant.
        """
        self.initialize_population()

        for generation in range(self.generations):
            # Evaluate fitness
            for variant in self.population:
                variant.fitness = self.fitness_evaluator.evaluate(variant)

            print(f"Generation {generation + 1}/{self.generations} - Best Fitness: {self.get_best_variant().fitness.get('total', 0):.4f}")

            # Select the best
            parents = self.selection_mechanism.select(self.population, self.population_size)

            # Create the next generation
            next_population = []
            for parent in parents:
                child = self.mutation_operator.mutate(parent)
                next_population.append(child)
            
            self.population = next_population

        # Evaluate the final population before returning the best
        for variant in self.population:
            variant.fitness = self.fitness_evaluator.evaluate(variant)

        return self.get_best_variant()

    def get_best_variant(self) -> CodeVariant:
        """
        Returns the best variant from the current population.
        """
        return max(self.population, key=lambda v: v.fitness.get('total', 0))
