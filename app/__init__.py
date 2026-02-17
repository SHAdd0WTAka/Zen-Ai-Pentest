"""
Main Application Module

Integrates all components into a unified application.

Usage:
    from app import create_app
    
    app = create_app()
    app.run()
"""

from .factory import create_app, ApplicationFactory
from .container import DependencyContainer
from .lifecycle import ApplicationLifecycle

__all__ = [
    "create_app",
    "ApplicationFactory", 
    "DependencyContainer",
    "ApplicationLifecycle",
]
