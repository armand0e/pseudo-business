"""
Test script for the Evolution Engine.
"""

from evolution_engine import EvolutionEngine

def main():
    """
    Test the Evolution Engine with a simple code example.
    """
    # Simple code to optimize
    codebase = """
def compute_sum(n):
    result = 0
    for i in range(n):
        result += i
    return result
"""

    print("Initial code:")
    print(codebase)
    print("\nStarting optimization...")

    # Initialize the engine with a small population and few generations for testing
    engine = EvolutionEngine(
        population_size=5,
        max_generations=3,
        mutation_rate=0.8
    )

    # Optimize the code
    best_variant = engine.optimize_code(codebase)

    print("\nOptimized code:")
    print(best_variant.codebase)
    print(f"\nBest variant score: {best_variant.fitness_score.total_score:.4f}")

if __name__ == "__main__":
    main()