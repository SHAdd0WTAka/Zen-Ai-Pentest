"""
Setup script for Zen AI Pentest
Q3 2026: PyPI Package
"""

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Core dependencies
install_requires = [
    "requests>=2.32.0",  # SECURITY FIX: CVE-2024-35195
    "aiohttp>=3.13.3  # SECURITY FIX: CVE-2025-69223",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "websockets>=12.0",
    "click>=8.1.0",
    "rich>=13.0.0",
    "colorama>=0.4.6",
    "typer>=0.9.0",
    "cryptography>=43.0.1",  # SECURITY FIX: CVE-2024-26130, CVE-2024-41985
    "python-jose>=3.4.0  # SECURITY FIX: CVE-2024-33663",
    "passlib>=1.7.4",
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "aiosqlite>=0.19.0",
    "jinja2>=3.1.5",  # SECURITY FIX: CVE-2024-56201, CVE-2024-56326, CVE-2024-34064
    "markdown>=3.5.0",
    "pyyaml>=6.0.1",
    "tenacity>=8.2.0",
    "python-dateutil>=2.8.0",
    "aiofiles>=23.0.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
]

# Development dependencies
dev_requires = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-xdist>=3.3.0",
    "pytest-mock>=3.11.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.1.0",
    "mypy>=1.5.0",
    "bandit>=1.7.0",
    "safety>=2.3.0",
    "sphinx>=7.0.0",
    "sphinx-rtd-theme>=1.3.0",
    "pre-commit>=3.4.0",
]

# Optional features
extras_require = {
    "dev": dev_requires,
    "docker": ["docker>=6.1.0"],
    "playwright": ["playwright>=1.40.0"],
    "benchmarks": ["matplotlib>=3.8.0", "seaborn>=0.13.0", "plotly>=5.18.0"],
    "ml": ["scikit-learn>=1.3.0"],
    "all": [
        "docker>=6.1.0",
        "playwright>=1.40.0",
        "matplotlib>=3.8.0",
        "seaborn>=0.13.0",
        "plotly>=5.18.0",
        "scikit-learn>=1.3.0",
        "jupyter>=1.0.0",
        "ipython>=8.16.0",
    ],
    "pdf": ['weasyprint>=60.0; platform_system != "Windows"'],
}

setup(
    name="zen-ai-pentest",
    version="2.3.9",
    description="Autonomous AI-Powered Penetration Testing Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SHAdd0WTAka",
    author_email="security@zen-ai-pentest.dev",
    url="https://github.com/SHAdd0WTAka/zen-ai-pentest",
    packages=find_packages(exclude=["tests*", "docs*", "web_ui*", "examples*"]),
    include_package_data=True,
    package_data={
        "zen-ai-pentest": [
            "config/*.json",
            "templates/*.html",
            "templates/*.md",
            "data/*.db",
        ],
    },
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "zen-ai-pentest=zen_ai_pentest:main",
            "zen=zen_ai_pentest:main",
            "zen-pentest=zen_ai_pentest:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Security :: Pentesting",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
        "Framework :: AsyncIO",
    ],
    python_requires=">=3.9",
    keywords="pentesting security ai autonomous red-team vulnerability scanning exploit-validation",
    project_urls={
        "Bug Reports": "https://github.com/SHAdd0WTAka/zen-ai-pentest/issues",
        "Source": "https://github.com/SHAdd0WTAka/zen-ai-pentest",
        "Documentation": "https://shadd0wtaka.github.io/zen-ai-pentest",
        "Changelog": "https://github.com/SHAdd0WTAka/zen-ai-pentest/blob/main/CHANGELOG.md",
    },
    zip_safe=False,
)
