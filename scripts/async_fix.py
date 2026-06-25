"""
Windows Asyncio Fix für ResourceWarnings
Verhindert 'unclosed transport' Fehler auf Windows
"""

import sys

if sys.platform == "win32":
    # Fix für Proactor Event Loop Warnings
    def silence_asyncio_warnings():
        """Silence unclosed transport warnings on Windows"""
        import warnings

        warnings.filterwarnings("ignore", message="unclosed transport", category=ResourceWarning)

    silence_asyncio_warnings()

    # Alternativ: Use SelectorEventLoop on Windows (more stable)
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
