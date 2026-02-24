"""
Zen-AI-Pentest - AI-Powered Penetration Testing Framework
"""

__version__ = "2.3.4"
__author__ = "SHAdd0WTAka"

# Export Celery app for django-celery style imports
try:
    from tasks import celery_app
    
    __all__ = ["celery_app", "__version__"]
except ImportError:
    __all__ = ["__version__"]
