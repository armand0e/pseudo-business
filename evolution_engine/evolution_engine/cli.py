import argparse
from evolution_engine.evolution_engine import EvolutionEngine

def main():
    """
    Command-line interface for the Evolution Engine.
    """
    parser = argparse.ArgumentParser(description="Evolution Engine CLI")
    parser.add_argument("file_path", help="Path to the Python file to optimize.")
    parser.add_argument("--population-size", type=int, default=50, help="Size of the population.")
    parser.add_argument("--generations", type=int, default=100, help="Number of generations to run.")
    
    args = parser.parse_args()

    try:
        with open(args.file_path, 'r') as f:
            initial_code = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {args.file_path}")
        return

    engine = EvolutionEngine(
        codebase=initial_code,
        population_size=args.population_size,
        generations=args.generations
    )

    print("Starting evolution...")
    best_variant = engine.evolve()
    print("Evolution finished.")
    
    print("\n--- Initial Code ---")
    print(initial_code)
    
    print("\n--- Optimized Code ---")
    print(best_variant.code)
    
    print(f"\nBest fitness score: {best_variant.fitness.get('total', 0):.4f}")

if __name__ == "__main__":
    main()