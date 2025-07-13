from typing import Dict

class CodeVariant:
    """
    Represents an individual code variant within the population.
    """

    def __init__(self, code: str, fitness: Dict[str, float] = None):
        """
        Initializes a new CodeVariant.

        Args:
            code: The source code of the variant.
            fitness: The fitness scores of the variant.
        """
        self.code = code
        self.fitness = fitness if fitness is not None else {}

    def __repr__(self):
        return f"CodeVariant(fitness={self.fitness.get('total', 0):.4f})"