#!/usr/bin/env python3
"""
OpenEvolve Integration for Agentic AI Tech Company

Integrates the OpenEvolve evolutionary coding framework to continuously
improve generated code through iterative optimization.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import ast
import re

logger = logging.getLogger(__name__)

@dataclass
class EvolutionConfig:
    """Configuration for evolutionary optimization"""
    population_size: int = 20
    generations: int = 10
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elite_size: int = 2
    fitness_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.fitness_weights is None:
            self.fitness_weights = {
                "performance": 0.3,
                "readability": 0.2,
                "security": 0.2,
                "maintainability": 0.15,
                "test_coverage": 0.15
            }

@dataclass
class CodeCandidate:
    """Represents a code candidate in the evolution process"""
    id: str
    code: str
    language: str
    fitness_score: float = 0.0
    metrics: Dict[str, float] = None
    test_results: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}

class OpenEvolveIntegration:
    """
    Integration layer for OpenEvolve evolutionary coding
    """
    
    def __init__(self, config: EvolutionConfig = None):
        self.config = config or EvolutionConfig()
        self.openevolve_path = self._find_openevolve_path()
        self.evaluators = {
            "performance": PerformanceEvaluator(),
            "readability": ReadabilityEvaluator(),
            "security": SecurityEvaluator(),
            "maintainability": MaintainabilityEvaluator(),
            "test_coverage": TestCoverageEvaluator()
        }
        
    def _find_openevolve_path(self) -> Optional[Path]:
        """Find OpenEvolve installation path"""
        # Check if OpenEvolve is in the current project
        possible_paths = [
            Path("./Frameworks/openevolve"),
            Path("../openevolve"),
            Path("./openevolve"),
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "openevolve").exists():
                return path
                
        logger.warning("OpenEvolve not found in expected locations")
        return None
    
    async def evolve_code(
        self, 
        initial_code: str, 
        language: str,
        task_description: str,
        test_cases: List[Dict[str, Any]] = None
    ) -> CodeCandidate:
        """
        Evolve code using OpenEvolve framework
        """
        logger.info(f"Starting code evolution for {language} code")
        
        try:
            # Initialize population
            population = await self._initialize_population(
                initial_code, language, task_description
            )
            
            best_candidate = None
            
            for generation in range(self.config.generations):
                logger.info(f"Evolution generation {generation + 1}/{self.config.generations}")
                
                # Evaluate fitness for all candidates
                await self._evaluate_population(population, test_cases)
                
                # Select best candidate
                population.sort(key=lambda x: x.fitness_score, reverse=True)
                current_best = population[0]
                
                if best_candidate is None or current_best.fitness_score > best_candidate.fitness_score:
                    best_candidate = current_best
                
                # Early termination if fitness is high enough
                if current_best.fitness_score >= 0.95:
                    logger.info(f"High fitness achieved ({current_best.fitness_score:.3f}), stopping evolution")
                    break
                
                # Create next generation
                population = await self._create_next_generation(population)
            
            logger.info(f"Evolution completed. Best fitness: {best_candidate.fitness_score:.3f}")
            return best_candidate
            
        except Exception as e:
            logger.error(f"Evolution failed: {str(e)}")
            # Return original code as fallback
            return CodeCandidate(
                id="original",
                code=initial_code,
                language=language,
                fitness_score=0.5
            )
    
    async def _initialize_population(
        self, 
        initial_code: str, 
        language: str, 
        task_description: str
    ) -> List[CodeCandidate]:
        """Initialize population with code variations"""
        population = []
        
        # Add original code
        population.append(CodeCandidate(
            id="original",
            code=initial_code,
            language=language
        ))
        
        # Generate variations using LLM-based mutations
        for i in range(self.config.population_size - 1):
            variation = await self._generate_code_variation(
                initial_code, language, task_description, i
            )
            population.append(CodeCandidate(
                id=f"variant_{i}",
                code=variation,
                language=language
            ))
        
        return population
    
    async def _generate_code_variation(
        self, 
        base_code: str, 
        language: str, 
        task_description: str, 
        variant_index: int
    ) -> str:
        """Generate code variation using LLM"""
        # This would integrate with LocalAI to generate variations
        # For now, implementing basic mutations
        
        mutations = [
            self._optimize_performance,
            self._improve_readability,
            self._enhance_security,
            self._add_error_handling,
            self._optimize_memory_usage,
            self._improve_naming,
            self._add_type_hints,
            self._refactor_functions
        ]
        
        mutation = mutations[variant_index % len(mutations)]
        return await mutation(base_code, language)
    
    async def _optimize_performance(self, code: str, language: str) -> str:
        """Apply performance optimizations"""
        if language == "python":
            # Example optimizations for Python
            optimizations = [
                (r'for i in range\(len\((.+?)\)\):', r'for i, item in enumerate(\1):'),
                (r'\.append\((.+?)\)', r'.extend([\1])'),
                (r'if (.+?) in (.+?):', r'if \1 in set(\2):')
            ]
            
            optimized_code = code
            for pattern, replacement in optimizations:
                optimized_code = re.sub(pattern, replacement, optimized_code)
            
            return optimized_code
        
        return code
    
    async def _improve_readability(self, code: str, language: str) -> str:
        """Improve code readability"""
        if language == "python":
            # Add docstrings, improve variable names, etc.
            lines = code.split('\n')
            improved_lines = []
            
            for line in lines:
                # Add type hints where missing
                if 'def ' in line and '->' not in line and ':' in line:
                    line = line.replace(':', ' -> Any:')
                
                improved_lines.append(line)
            
            return '\n'.join(improved_lines)
        
        return code
    
    async def _enhance_security(self, code: str, language: str) -> str:
        """Add security improvements"""
        if language == "python":
            # Add input validation, sanitization, etc.
            security_patterns = [
                (r'input\((.+?)\)', r'validate_input(input(\1))'),
                (r'eval\((.+?)\)', r'safe_eval(\1)'),
                (r'exec\((.+?)\)', r'safe_exec(\1)')
            ]
            
            secure_code = code
            for pattern, replacement in security_patterns:
                secure_code = re.sub(pattern, replacement, secure_code)
            
            return secure_code
        
        return code
    
    async def _add_error_handling(self, code: str, language: str) -> str:
        """Add comprehensive error handling"""
        if language == "python":
            # Wrap risky operations in try-catch blocks
            lines = code.split('\n')
            enhanced_lines = []
            
            for line in lines:
                if any(keyword in line for keyword in ['open(', 'requests.', 'json.loads']):
                    indent = len(line) - len(line.lstrip())
                    enhanced_lines.extend([
                        ' ' * indent + 'try:',
                        ' ' * (indent + 4) + line.strip(),
                        ' ' * indent + 'except Exception as e:',
                        ' ' * (indent + 4) + 'logger.error(f"Error: {e}")',
                        ' ' * (indent + 4) + 'raise'
                    ])
                else:
                    enhanced_lines.append(line)
            
            return '\n'.join(enhanced_lines)
        
        return code
    
    async def _optimize_memory_usage(self, code: str, language: str) -> str:
        """Optimize memory usage"""
        # Implementation for memory optimizations
        return code
    
    async def _improve_naming(self, code: str, language: str) -> str:
        """Improve variable and function naming"""
        # Implementation for naming improvements
        return code
    
    async def _add_type_hints(self, code: str, language: str) -> str:
        """Add type hints"""
        # Implementation for adding type hints
        return code
    
    async def _refactor_functions(self, code: str, language: str) -> str:
        """Refactor functions for better modularity"""
        # Implementation for function refactoring
        return code
    
    async def _evaluate_population(
        self, 
        population: List[CodeCandidate], 
        test_cases: List[Dict[str, Any]] = None
    ) -> None:
        """Evaluate fitness of all candidates in population"""
        tasks = []
        
        for candidate in population:
            task = self._evaluate_candidate(candidate, test_cases)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def _evaluate_candidate(
        self, 
        candidate: CodeCandidate, 
        test_cases: List[Dict[str, Any]] = None
    ) -> None:
        """Evaluate fitness of a single candidate"""
        metrics = {}
        
        # Run all evaluators
        for evaluator_name, evaluator in self.evaluators.items():
            try:
                score = await evaluator.evaluate(candidate.code, candidate.language, test_cases)
                metrics[evaluator_name] = score
            except Exception as e:
                logger.warning(f"Evaluator {evaluator_name} failed: {str(e)}")
                metrics[evaluator_name] = 0.0
        
        # Calculate weighted fitness score
        fitness_score = sum(
            metrics.get(metric, 0.0) * weight
            for metric, weight in self.config.fitness_weights.items()
        )
        
        candidate.metrics = metrics
        candidate.fitness_score = fitness_score
    
    async def _create_next_generation(self, population: List[CodeCandidate]) -> List[CodeCandidate]:
        """Create next generation through selection, crossover, and mutation"""
        # Sort by fitness
        population.sort(key=lambda x: x.fitness_score, reverse=True)
        
        next_generation = []
        
        # Keep elite candidates
        next_generation.extend(population[:self.config.elite_size])
        
        # Generate remaining candidates through crossover and mutation
        while len(next_generation) < self.config.population_size:
            # Selection
            parent1 = self._tournament_selection(population)
            parent2 = self._tournament_selection(population)
            
            # Crossover
            if np.random.random() < self.config.crossover_rate:
                child = await self._crossover(parent1, parent2)
            else:
                child = parent1
            
            # Mutation
            if np.random.random() < self.config.mutation_rate:
                child = await self._mutate(child)
            
            next_generation.append(child)
        
        return next_generation
    
    def _tournament_selection(self, population: List[CodeCandidate], tournament_size: int = 3) -> CodeCandidate:
        """Tournament selection for parent selection"""
        tournament = np.random.choice(population, tournament_size, replace=False)
        return max(tournament, key=lambda x: x.fitness_score)
    
    async def _crossover(self, parent1: CodeCandidate, parent2: CodeCandidate) -> CodeCandidate:
        """Crossover operation between two parents"""
        # Simple line-based crossover for now
        lines1 = parent1.code.split('\n')
        lines2 = parent2.code.split('\n')
        
        # Ensure both have same number of lines for crossover
        max_lines = max(len(lines1), len(lines2))
        
        # Pad shorter code with empty lines
        while len(lines1) < max_lines:
            lines1.append('')
        while len(lines2) < max_lines:
            lines2.append('')
        
        # Random crossover point
        crossover_point = np.random.randint(1, max_lines)
        
        child_lines = lines1[:crossover_point] + lines2[crossover_point:]
        child_code = '\n'.join(child_lines).strip()
        
        return CodeCandidate(
            id=f"crossover_{parent1.id}_{parent2.id}",
            code=child_code,
            language=parent1.language
        )
    
    async def _mutate(self, candidate: CodeCandidate) -> CodeCandidate:
        """Mutate a candidate"""
        # Simple mutation - randomly apply one of the improvement functions
        mutations = [
            self._optimize_performance,
            self._improve_readability,
            self._enhance_security,
            self._add_error_handling
        ]
        
        mutation_func = np.random.choice(mutations)
        mutated_code = await mutation_func(candidate.code, candidate.language)
        
        return CodeCandidate(
            id=f"mutated_{candidate.id}",
            code=mutated_code,
            language=candidate.language
        )

# Evaluator Classes
class BaseEvaluator:
    """Base class for fitness evaluators"""
    
    async def evaluate(self, code: str, language: str, test_cases: List[Dict[str, Any]] = None) -> float:
        """Evaluate code and return fitness score (0.0 to 1.0)"""
        raise NotImplementedError

class PerformanceEvaluator(BaseEvaluator):
    """Evaluates code performance"""
    
    async def evaluate(self, code: str, language: str, test_cases: List[Dict[str, Any]] = None) -> float:
        # Analyze algorithmic complexity, identify performance bottlenecks
        score = 0.8  # Placeholder
        
        # Penalty for known performance anti-patterns
        if 'nested loops' in self._analyze_complexity(code):
            score -= 0.2
        
        if 'inefficient operations' in self._analyze_operations(code):
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _analyze_complexity(self, code: str) -> List[str]:
        """Analyze algorithmic complexity"""
        issues = []
        
        # Check for nested loops
        lines = code.split('\n')
        loop_depth = 0
        max_depth = 0
        
        for line in lines:
            if 'for ' in line or 'while ' in line:
                loop_depth += 1
                max_depth = max(max_depth, loop_depth)
            elif line.strip() == '':
                continue
            elif not line.startswith(' ') and loop_depth > 0:
                loop_depth = 0
        
        if max_depth >= 3:
            issues.append('nested loops')
        
        return issues
    
    def _analyze_operations(self, code: str) -> List[str]:
        """Analyze for inefficient operations"""
        issues = []
        
        # Check for inefficient patterns
        inefficient_patterns = [
            r'\.append\(.+?\) in loop',  # Should use extend or list comprehension
            r'string concatenation in loop',  # Should use join
            r'repeated function calls'  # Should cache results
        ]
        
        for pattern in inefficient_patterns:
            if re.search(pattern, code):
                issues.append('inefficient operations')
                break
        
        return issues

class ReadabilityEvaluator(BaseEvaluator):
    """Evaluates code readability"""
    
    async def evaluate(self, code: str, language: str, test_cases: List[Dict[str, Any]] = None) -> float:
        score = 0.8  # Base score
        
        # Check for comments and docstrings
        if '"""' in code or "'''" in code or '#' in code:
            score += 0.1
        
        # Check for meaningful variable names
        if self._has_meaningful_names(code):
            score += 0.1
        else:
            score -= 0.2
        
        # Check function length
        if self._check_function_length(code):
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _has_meaningful_names(self, code: str) -> bool:
        """Check for meaningful variable names"""
        # Simple heuristic - check for common bad patterns
        bad_names = ['a', 'b', 'c', 'x', 'y', 'z', 'tmp', 'temp', 'data']
        
        for bad_name in bad_names:
            if f' {bad_name} ' in code or f' {bad_name}=' in code:
                return False
        
        return True
    
    def _check_function_length(self, code: str) -> bool:
        """Check if functions are too long"""
        lines = code.split('\n')
        current_function_length = 0
        max_function_length = 0
        
        for line in lines:
            if line.strip().startswith('def '):
                current_function_length = 1
            elif line.strip() == '' or not line.startswith(' '):
                max_function_length = max(max_function_length, current_function_length)
                current_function_length = 0
            elif current_function_length > 0:
                current_function_length += 1
        
        return max_function_length > 50  # Functions longer than 50 lines

class SecurityEvaluator(BaseEvaluator):
    """Evaluates code security"""
    
    async def evaluate(self, code: str, language: str, test_cases: List[Dict[str, Any]] = None) -> float:
        score = 1.0
        
        # Check for security vulnerabilities
        vulnerabilities = self._check_vulnerabilities(code)
        score -= len(vulnerabilities) * 0.2
        
        # Check for input validation
        if not self._has_input_validation(code):
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _check_vulnerabilities(self, code: str) -> List[str]:
        """Check for common security vulnerabilities"""
        vulnerabilities = []
        
        # Check for dangerous functions
        dangerous_patterns = [
            r'eval\(',
            r'exec\(',
            r'subprocess\.call\(',
            r'os\.system\(',
            r'pickle\.loads\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                vulnerabilities.append(f"Dangerous function: {pattern}")
        
        return vulnerabilities
    
    def _has_input_validation(self, code: str) -> bool:
        """Check if code has input validation"""
        validation_patterns = [
            r'isinstance\(',
            r'type\(.+?\)',
            r'assert ',
            r'if .+? is None',
            r'validate'
        ]
        
        return any(re.search(pattern, code) for pattern in validation_patterns)

class MaintainabilityEvaluator(BaseEvaluator):
    """Evaluates code maintainability"""
    
    async def evaluate(self, code: str, language: str, test_cases: List[Dict[str, Any]] = None) -> float:
        score = 0.8
        
        # Check for modularity
        if self._is_modular(code):
            score += 0.1
        
        # Check for separation of concerns
        if self._has_separation_of_concerns(code):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _is_modular(self, code: str) -> bool:
        """Check if code is properly modularized"""
        # Count functions and classes
        function_count = len(re.findall(r'def ', code))
        class_count = len(re.findall(r'class ', code))
        
        total_lines = len([line for line in code.split('\n') if line.strip()])
        
        # Good modularity: reasonable number of functions relative to code size
        return function_count > 0 and (total_lines / max(function_count, 1)) < 30
    
    def _has_separation_of_concerns(self, code: str) -> bool:
        """Check for separation of concerns"""
        # This is a simplified check
        # In reality, this would be more sophisticated
        return 'class ' in code or 'import ' in code

class TestCoverageEvaluator(BaseEvaluator):
    """Evaluates test coverage"""
    
    async def evaluate(self, code: str, language: str, test_cases: List[Dict[str, Any]] = None) -> float:
        if test_cases is None:
            return 0.5  # Neutral score if no tests provided
        
        # Run tests and calculate coverage
        try:
            coverage = await self._run_tests_and_calculate_coverage(code, test_cases, language)
            return coverage
        except Exception as e:
            logger.warning(f"Test coverage evaluation failed: {str(e)}")
            return 0.0
    
    async def _run_tests_and_calculate_coverage(
        self, 
        code: str, 
        test_cases: List[Dict[str, Any]], 
        language: str
    ) -> float:
        """Run tests and calculate coverage"""
        if language != "python":
            return 0.5  # Placeholder for other languages
        
        # Create temporary files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "code.py"
            test_file = Path(temp_dir) / "test_code.py"
            
            # Write code to file
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Generate test file
            test_content = self._generate_test_file(test_cases)
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            # Run tests with coverage
            try:
                result = subprocess.run([
                    'python', '-m', 'pytest', '--cov=code', '--cov-report=json',
                    str(test_file)
                ], capture_output=True, text=True, cwd=temp_dir)
                
                if result.returncode == 0:
                    # Parse coverage report
                    coverage_file = Path(temp_dir) / "coverage.json"
                    if coverage_file.exists():
                        with open(coverage_file) as f:
                            coverage_data = json.load(f)
                            return coverage_data.get('totals', {}).get('percent_covered', 0.0) / 100.0
                
                return 0.0
                
            except Exception as e:
                logger.warning(f"Coverage calculation failed: {str(e)}")
                return 0.0
    
    def _generate_test_file(self, test_cases: List[Dict[str, Any]]) -> str:
        """Generate test file from test cases"""
        test_content = """
import pytest
import sys
sys.path.append('.')
from code import *

"""
        
        for i, test_case in enumerate(test_cases):
            test_content += f"""
def test_case_{i}():
    # Test case: {test_case.get('description', 'No description')}
    {test_case.get('code', 'pass')}
"""
        
        return test_content

# Usage example
async def main():
    """Example usage of OpenEvolve integration"""
    
    # Example code to evolve
    initial_code = """
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

def main():
    result = fibonacci(10)
    print(f"Fibonacci(10) = {result}")

if __name__ == "__main__":
    main()
"""
    
    # Test cases
    test_cases = [
        {
            "description": "Test fibonacci base cases",
            "code": "assert fibonacci(0) == 0\nassert fibonacci(1) == 1"
        },
        {
            "description": "Test fibonacci recursive cases",
            "code": "assert fibonacci(5) == 5\nassert fibonacci(10) == 55"
        }
    ]
    
    # Initialize evolution
    config = EvolutionConfig(
        population_size=10,
        generations=5,
        mutation_rate=0.2,
        crossover_rate=0.8
    )
    
    evolution = OpenEvolveIntegration(config)
    
    # Evolve the code
    evolved_candidate = await evolution.evolve_code(
        initial_code,
        "python",
        "Implement efficient fibonacci function",
        test_cases
    )
    
    print(f"Evolution completed!")
    print(f"Fitness score: {evolved_candidate.fitness_score:.3f}")
    print(f"Metrics: {evolved_candidate.metrics}")
    print(f"\nEvolved code:\n{evolved_candidate.code}")

if __name__ == "__main__":
    asyncio.run(main()) 