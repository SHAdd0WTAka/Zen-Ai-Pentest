"""
Python 3.13 Windows AsyncIO Fix
Issue #10: Python 3.13 Windows AsyncIO Fix permanent lösen

Fix für bekannte Probleme:
- ProactorEventLoop issues on Windows
- asyncio.run() hanging
- Task cancellation problems
- Event loop policy conflicts
"""

import sys
import asyncio
import platform
import warnings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def is_windows() -> bool:
    """Check if running on Windows"""
    return platform.system() == "Windows"


def is_python_313_or_higher() -> bool:
    """Check if Python 3.13 or higher"""
    return sys.version_info >= (3, 13)


def apply_windows_asyncio_fix():
    """
    Wendet Windows-spezifische AsyncIO Fixes an
    
    Muss vor der ersten asyncio Nutzung aufgerufen werden!
    """
    if not is_windows():
        return
    
    logger.info("Applying Windows AsyncIO fixes...")
    
    # Fix 1: SelectorEventLoop für Windows (statt Proactor)
    # Python 3.13 hat Proactor-Probleme auf Windows
    try:
        if is_python_313_or_higher():
            # Nutze SelectorEventLoop als Workaround
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            logger.info("Set WindowsSelectorEventLoopPolicy")
    except Exception as e:
        logger.warning(f"Could not set SelectorEventLoopPolicy: {e}")
    
    # Fix 2: Erhöhe Stack-Size für recursive coroutines
    try:
        import threading
        threading.stack_size(2 * 1024 * 1024)  # 2MB stack
    except Exception:
        pass  # Nicht kritisch
    
    logger.info("Windows AsyncIO fixes applied")


class SafeAsyncioRunner:
    """
    Sicherer AsyncIO Runner für Windows Python 3.13+
    
    Workaround für hängende asyncio.run() Aufrufe
    """
    
    def __init__(self, timeout: Optional[float] = None):
        self.timeout = timeout
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def run(self, coro):
        """
        Führt eine Coroutine sicher aus
        
        Args:
            coro: Die auszuführende Coroutine
            
        Returns:
            Das Ergebnis der Coroutine
        """
        # Fix anwenden falls nötig
        if is_windows() and is_python_313_or_higher():
            return self._run_with_fix(coro)
        else:
            return asyncio.run(coro)
    
    def _run_with_fix(self, coro):
        """Interne Run-Methode mit Windows Fixes"""
        # Erstelle neuen Loop statt asyncio.run()
        loop = asyncio.new_event_loop()
        
        try:
            asyncio.set_event_loop(loop)
            
            # Setze exception handler
            def exception_handler(loop, context):
                logger.error(f"AsyncIO Exception: {context}")
            
            loop.set_exception_handler(exception_handler)
            
            # Führe coroutine aus
            if self.timeout:
                return loop.run_until_complete(
                    asyncio.wait_for(coro, timeout=self.timeout)
                )
            else:
                return loop.run_until_complete(coro)
                
        finally:
            # Cleanup
            try:
                # Cancel pending tasks
                pending = asyncio.all_tasks(loop)
                if pending:
                    for task in pending:
                        task.cancel()
                    
                    # Wait for cancellation
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
                
            except Exception as e:
                logger.warning(f"Error during loop cleanup: {e}")
            
            asyncio.set_event_loop(None)


def safe_asyncio_run(coro, timeout: Optional[float] = None):
    """
    Sicherer Ersatz für asyncio.run()
    
    Usage:
        result = safe_asyncio_run(my_coroutine())
    """
    runner = SafeAsyncioRunner(timeout=timeout)
    return runner.run(coro)


class AsyncIOContext:
    """
    Context Manager für sichere AsyncIO Operationen
    
    Usage:
        async with AsyncIOContext() as ctx:
            result = await ctx.run_task(my_task())
    """
    
    def __init__(self, timeout: Optional[float] = None):
        self.timeout = timeout
        self.loop: Optional[asyncio.AbstractEventLoop] = None
    
    async def __aenter__(self):
        self.loop = asyncio.get_event_loop()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup bei Bedarf
        pass
    
    async def run_task(self, coro):
        """Führt eine Task mit Timeout aus"""
        if self.timeout:
            return await asyncio.wait_for(coro, timeout=self.timeout)
        return await coro


def patch_asyncio_for_windows():
    """
    Hauptfunktion zum Patchen von AsyncIO auf Windows
    
    Sollte ganz am Anfang der Anwendung aufgerufen werden.
    """
    if not is_windows():
        return
    
    # Wende Fixes an
    apply_windows_asyncio_fix()
    
    # Monkey-patch asyncio.run für Python 3.13+
    if is_python_313_or_higher():
        import asyncio
        
        # Speichere Original
        _original_run = asyncio.run
        
        def _patched_run(coro, *, debug=False):
            """Gepatchte asyncio.run()"""
            runner = SafeAsyncioRunner()
            return runner.run(coro)
        
        # Ersetze nur wenn nötig
        if not getattr(asyncio, '_patched', False):
            asyncio.run = _patched_run
            asyncio._patched = True
            logger.info("asyncio.run patched for Windows compatibility")


# Automatisch Fixes anwenden beim Import
patch_asyncio_for_windows()


if __name__ == "__main__":
    # Test
    import time
    
    async def test_coro():
        await asyncio.sleep(0.1)
        return "Success"
    
    print(f"Python version: {sys.version}")
    print(f"Windows: {is_windows()}")
    print(f"Python >= 3.13: {is_python_313_or_higher()}")
    
    result = safe_asyncio_run(test_coro())
    print(f"Result: {result}")
