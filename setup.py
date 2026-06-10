"""
Sport OS Core — Package setup.
"""

from setuptools import setup, find_packages

setup(
    name="sport-os-core",
    version="2.4.0",
    description="Sport OS Core — Management platform for sports competitions",
    author="Sport OS Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "sqlalchemy>=2.0.25",
        "alembic>=1.13.1",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "prometheus-client>=0.19.0",
        "psutil>=5.9.6",
        "httpx>=0.26.0",
        "email-validator>=2.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=24.1.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
        "test": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "locust>=2.20.1",
        ],
    },
)
