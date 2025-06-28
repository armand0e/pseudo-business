"""
Setup script for Backend Agent package
"""
from setuptools import setup, find_packages

setup(
    name="backend-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.78.0",
        "uvicorn[standard]>=0.17.6",
        "sqlalchemy>=1.4.39",
        "pydantic>=1.9.1",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "aiohttp>=3.8.1"
    ],
    entry_points={
        "console_scripts": [
            "backend-agent=backend_agent.main:app",
        ],
    },
)