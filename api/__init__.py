"""
Zen AI Pentest - REST API Module
A production-ready API for penetration testing operations.
Built with FastAPI for high performance and automatic documentation.

Performance Optimizations:
- Lazy loading of heavy dependencies
- Conditional imports for optional components
- Deferred middleware initialization

Author: SHAdd0WTAka + Kimi AI
Version: 1.0.0
"""

__version__ = "1.0.0"
__all__ = ["app", "create_app"]


# Lazy import to avoid loading FastAPI on module import
def _lazy_import(name: str):
    """Lazy import helper"""
    import importlib

    return importlib.import_module(name)


# Create lazy app getter
_app = None


def app():
    """Get the FastAPI app (lazy loaded)"""
    global _app
    if _app is None:
        from api.main import app as _app_instance

        _app = _app_instance
    return _app


def create_app(**kwargs):
    """Create a new FastAPI app instance with custom config"""
    from api.main import create_app as _create_app

    return _create_app(**kwargs)
