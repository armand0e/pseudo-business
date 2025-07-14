from setuptools import setup, find_packages

setup(
    name="devops_agent",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "docker>=6.0.0",
        "boto3>=1.26.0",
        "requests>=2.28.0",
        "pyyaml>=6.0",
        "python-terraform>=0.10.1",
        "prometheus-client>=0.16.0",
        "elasticsearch>=8.6.0", 
        "kubernetes>=26.1.0",
    ],
    entry_points={
        "console_scripts": [
            "devops-agent=devops_agent.cli:main",
        ],
    },
)