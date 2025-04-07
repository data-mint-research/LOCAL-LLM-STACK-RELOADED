#!/usr/bin/env python3
"""Setup script for LOCAL-LLM-STACK-RELOADED."""

from setuptools import find_packages, setup

setup(
    name="llm-stack",
    version="0.1.0",
    description="Eine moderne, wartbare und performante Python-Implementierung des LOCAL-LLM-STACK",
    author="Data Mint Research",
    author_email="info@example.com",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0,<9.0.0",
        "docker>=6.0.0,<7.0.0",
        "pyyaml>=6.0,<7.0",
        "rich>=12.0.0,<13.0.0",
        "pydantic>=2.0.0,<3.0.0",
        "neo4j>=5.0.0,<6.0.0",
        "jinja2>=3.0.0,<4.0.0",
        "requests>=2.0.0,<3.0.0",
        "pyupgrade>=3.0.0,<4.0.0",
        "isort>=5.0.0,<6.0.0",
        "black>=23.0.0,<24.0.0",
        "vulture>=2.0.0,<3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "llm=llm_stack.cli:main",
        ],
    },
    python_requires=">=3.8",
)
