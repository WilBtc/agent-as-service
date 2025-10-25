"""
Setup script for AaaS Client (hosted service client only)

This lightweight package is for customers using the hosted AaaS service.
It includes only the client library without server dependencies.

Install with: pip install aaas-client
"""

from setuptools import setup, find_packages

# Read README
with open("CLIENT_README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aaas-client",
    version="2.0.0",
    author="WilBtc",
    author_email="contact@wilbtc.com",
    description="Python client for Agent as a Service (AaaS) hosted platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/WilBtc/agent-as-service",
    project_urls={
        "Documentation": "https://github.com/WilBtc/agent-as-service/blob/main/docs/HOSTED_SERVICE.md",
        "Source": "https://github.com/WilBtc/agent-as-service",
        "Support": "https://t.me/wilbtc",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        # Client-only dependencies (no server/SDK dependencies)
        "httpx>=0.26.0",
        "pydantic>=2.5.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "black>=23.12.1",
            "ruff>=0.1.11",
        ],
    },
    entry_points={
        # No CLI for client-only package
    },
    keywords=[
        "ai",
        "agents",
        "claude",
        "automation",
        "api",
        "client",
        "hosted-service",
        "saas",
    ],
    include_package_data=True,
)
