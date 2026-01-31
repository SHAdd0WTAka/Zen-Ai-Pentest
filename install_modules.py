#!/usr/bin/env python3
"""Install Zen AI modules in development mode"""
import subprocess
import sys
import os

os.chdir(r'C:\Users\Ataka\zen-ai-pentest')

# Install the package in development mode
subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'], check=False)

# Also add to Python path
import site
print(f"Site packages: {site.getsitepackages()}")
