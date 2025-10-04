#!/usr/bin/env python3
"""Setup script for Capibara Core."""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="capibara-core",
    version="0.1.0",
    author="Capibara Team",
    author_email="team@capibara.dev",
    description="Secure AI-powered script generation and execution",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/kvothesson/capibara-core",
    project_urls={
        "Bug Reports": "https://github.com/kvothesson/capibara-core/issues",
        "Source": "https://github.com/kvothesson/capibara-core",
        "Documentation": "https://capibara.dev/docs",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.11",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
            "mkdocstrings>=0.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "capibara=capibara.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai, llm, code-generation, docker, security, automation",
)
