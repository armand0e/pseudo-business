from setuptools import setup, find_packages

setup(
    name="testing_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "bandit>=1.7.5",
        "selenium>=4.10.0",
        "python-owasp-zap-v2.4>=0.0.20",
        "coverage>=7.2.0",
        "ast2json>=0.3.0",
        "pytest-asyncio>=0.21.0",
    ],
    python_requires=">=3.11",
)