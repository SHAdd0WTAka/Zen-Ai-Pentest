"""
Unit tests for Zen AI Pentest
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports BEFORE any other imports
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))
os.environ["PYTHONPATH"] = str(project_root) + os.pathsep + os.environ.get("PYTHONPATH", "")
