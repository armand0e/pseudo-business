"""
Setup script for the Evolution Engine package.
"""

from setuptools import setup, find_packages

setup(
    name="evolution-engine",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "astor",  # For AST to source code conversion
    ],
    entry_points={
        "console_scripts": [
            "evolution-engine=evolution_engine.cli:main",
        ],
    },
)