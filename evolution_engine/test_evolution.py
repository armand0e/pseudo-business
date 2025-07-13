import os
import subprocess

def create_test_file():
    """Creates a simple Python file for testing."""
    content = """
def inefficient_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

if __name__ == "__main__":
    my_numbers = [1, 2, 3, 4, 5]
    result = inefficient_sum(my_numbers)
    print(f"The sum is: {result}")
"""
    with open("test_code.py", "w") as f:
        f.write(content)

def run_evolution_test():
    """
    Runs the evolution engine on the test file.
    """
    create_test_file()
    
    command = [
        "python",
        "-m",
        "evolution_engine.cli",
        "test_code.py",
        "--population-size",
        "10",
        "--generations",
        "5"
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    print("--- CLI Output ---")
    print(result.stdout)
    if result.stderr:
        print("--- CLI Errors ---")
        print(result.stderr)

    # Clean up the test file
    os.remove("test_code.py")

if __name__ == "__main__":
    run_evolution_test()