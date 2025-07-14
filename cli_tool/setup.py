from setuptools import setup, find_packages

setup(
    name="cli_tool",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
        "keyring>=24.3.0",
        "rich>=13.7.0"
    ],
    entry_points={
        'console_scripts': [
            'agentic-cli=cli_tool.main:cli'
        ],
    },
)