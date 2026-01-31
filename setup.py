"""
Setup script for Zen AI Pentest
Q3 2026: PyPI Package
"""

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='zen-ai-pentest',
    version='2.0.0',
    description='Autonomous AI-Powered Penetration Testing Framework',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='SHAdd0WTAka',
    author_email='security@zen-ai-pentest.dev',
    url='https://github.com/SHAdd0WTAka/zen-ai-pentest',
    packages=find_packages(exclude=['tests*', 'docs*', 'web_ui*']),
    include_package_data=True,
    install_requires=[
        'requests>=2.31.0',
        'aiohttp>=3.9.0',
        'python-dotenv>=1.0.0',
        'pydantic>=2.0.0',
        'fastapi>=0.104.0',
        'uvicorn>=0.24.0',
        'websockets>=12.0',
        'click>=8.1.0',
        'rich>=13.0.0',
        'colorama>=0.4.6',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.1.0',
            'black>=23.0.0',
            'isort>=5.12.0',
            'flake8>=6.1.0',
            'mypy>=1.5.0',
        ],
        'web': [
            'react',
            'recharts',
            'axios',
        ]
    },
    entry_points={
        'console_scripts': [
            'zen-ai-pentest=zen_ai_pentest:main',
            'zen=zen_ai_pentest:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'Topic :: Security',
        'Topic :: Security :: Pentesting',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
    keywords='pentesting security ai autonomous red-team vulnerability scanning',
    project_urls={
        'Bug Reports': 'https://github.com/SHAdd0WTAka/zen-ai-pentest/issues',
        'Source': 'https://github.com/SHAdd0WTAka/zen-ai-pentest',
        'Documentation': 'https://shadd0wtaka.github.io/zen-ai-pentest',
    },
)
