"""
Command-line interface for the Evolution Engine.
"""

import argparse
import logging

from .evolution_engine import EvolutionEngine

def main():
    """
    Main entry point for the Evolution Engine CLI.
    """
    parser = argparse.ArgumentParser(description="Evolution Engine CLI")
    parser.add_argument("codefile", help="Path to the code file to optimize")
    parser.add_argument("--population-size", type=int, default=100, help="Number of variants in each generation")
    parser.add_argument("--generations", type=int, default=50, help="Maximum number of generations")
    parser.add_argument("--mutation-rate", type=float, default=0.1, help="Probability of mutation")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Read the code file
    with open(args.codefile, "r") as f:
        codebase = f.read()

    # Initialize and run the evolution engine
    engine = EvolutionEngine(
        population_size=args.population_size,
        max_generations=args.generations,
        mutation_rate=args.mutation_rate
    )

    best_variant = engine.optimize_code(codebase)

    # Output the optimized code
    output_file = f"optimized_{args.codefile}"
    with open(output_file, "w") as f:
        f.write(best_variant.codebase)

    print(f"Optimization complete. Saved to {output_file}")