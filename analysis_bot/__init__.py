"""
Zen-AI-Pentest Analysis Bot

Autonomous vulnerability analysis system with:
- Vulnerability Analyzer (840 lines)
- Risk Scorer (712 lines)  
- Exploitability Checker (822 lines)
- Recommendation Engine (894 lines)

Total: 4,095 lines of production-ready code
"""

__version__ = "1.0.0"
__author__ = "Zen-AI-Pentest Team"

from .analysis_bot import AnalysisBot, AnalysisConfig, AnalysisResult

__all__ = [
    "AnalysisBot",
    "AnalysisConfig", 
    "AnalysisResult",
]
