"""
Application Lifecycle Management

Manages startup and shutdown sequences with proper ordering.
"""

import asyncio
from typing import List, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LifecyclePhase(Enum):
    """Lifecycle phases"""
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class LifecycleHook:
    """A lifecycle hook"""
    name: str
    callback: Callable
    priority: int = 100  # Lower = earlier
    async_mode: bool = True


class ApplicationLifecycle:
    """
    Manages application lifecycle with ordered hooks
    
    Ensures components start and stop in the correct order.
    
    Example:
        lifecycle = ApplicationLifecycle()
        
        # Register startup hooks
        lifecycle.on_start("db", init_database, priority=10)
        lifecycle.on_start("api", start_api, priority=20)
        
        # Register shutdown hooks
        lifecycle.on_stop("api", stop_api, priority=10)
        lifecycle.on_stop("db", close_database, priority=20)
        
        # Execute
        await lifecycle.start()
        await lifecycle.stop()
    """
    
    def __init__(self):
        self.phase = LifecyclePhase.INITIALIZING
        self._startup_hooks: List[LifecycleHook] = []
        self._shutdown_hooks: List[LifecycleHook] = []
        self._components: Dict[str, Any] = {}
        self._startup_order: List[str] = []
    
    def on_start(
        self,
        name: str,
        callback: Callable,
        priority: int = 100
    ) -> None:
        """
        Register a startup hook
        
        Args:
            name: Hook name
            callback: Function to call on startup
            priority: Execution priority (lower = earlier)
        """
        hook = LifecycleHook(
            name=name,
            callback=callback,
            priority=priority,
            async_mode=asyncio.iscoroutinefunction(callback)
        )
        
        self._startup_hooks.append(hook)
        self._startup_hooks.sort(key=lambda h: h.priority)
        
        logger.debug(f"Registered startup hook: {name} (priority={priority})")
    
    def on_stop(
        self,
        name: str,
        callback: Callable,
        priority: int = 100
    ) -> None:
        """
        Register a shutdown hook
        
        Args:
            name: Hook name
            callback: Function to call on shutdown
            priority: Execution priority (lower = earlier)
        """
        hook = LifecycleHook(
            name=name,
            callback=callback,
            priority=priority,
            async_mode=asyncio.iscoroutinefunction(callback)
        )
        
        self._shutdown_hooks.append(hook)
        # Sort in reverse for shutdown (higher priority = earlier shutdown)
        self._shutdown_hooks.sort(key=lambda h: h.priority, reverse=True)
        
        logger.debug(f"Registered shutdown hook: {name} (priority={priority})")
    
    async def start(self) -> Dict[str, Any]:
        """
        Execute all startup hooks
        
        Returns:
            Results from each hook
        """
        if self.phase not in [LifecyclePhase.INITIALIZING, LifecyclePhase.STOPPED]:
            logger.warning(f"Cannot start from phase: {self.phase}")
            return {}
        
        self.phase = LifecyclePhase.STARTING
        results = {}
        
        logger.info("=" * 60)
        logger.info("Starting application components...")
        logger.info("=" * 60)
        
        for hook in self._startup_hooks:
            try:
                logger.info(f"Starting {hook.name}...")
                
                if hook.async_mode:
                    result = await hook.callback()
                else:
                    result = hook.callback()
                
                results[hook.name] = {"success": True, "result": result}
                self._components[hook.name] = result
                self._startup_order.append(hook.name)
                
                logger.info(f"✅ {hook.name} started")
                
            except Exception as e:
                results[hook.name] = {"success": False, "error": str(e)}
                logger.error(f"❌ {hook.name} failed: {e}")
                
                # Continue with other components but record the error
        
        self.phase = LifecyclePhase.RUNNING
        
        logger.info("=" * 60)
        logger.info(f"Started {sum(1 for r in results.values() if r['success'])}/{len(results)} components")
        logger.info("=" * 60)
        
        return results
    
    async def stop(self) -> Dict[str, Any]:
        """
        Execute all shutdown hooks
        
        Returns:
            Results from each hook
        """
        if self.phase not in [LifecyclePhase.RUNNING, LifecyclePhase.STARTING]:
            logger.warning(f"Cannot stop from phase: {self.phase}")
            return {}
        
        self.phase = LifecyclePhase.STOPPING
        results = {}
        
        logger.info("=" * 60)
        logger.info("Stopping application components...")
        logger.info("=" * 60)
        
        # Execute shutdown hooks in priority order
        for hook in self._shutdown_hooks:
            try:
                logger.info(f"Stopping {hook.name}...")
                
                if hook.async_mode:
                    result = await hook.callback()
                else:
                    result = hook.callback()
                
                results[hook.name] = {"success": True, "result": result}
                logger.info(f"✅ {hook.name} stopped")
                
            except Exception as e:
                results[hook.name] = {"success": False, "error": str(e)}
                logger.error(f"❌ {hook.name} failed to stop: {e}")
        
        self.phase = LifecyclePhase.STOPPED
        self._components.clear()
        
        logger.info("=" * 60)
        logger.info(f"Stopped {sum(1 for r in results.values() if r['success'])}/{len(results)} components")
        logger.info("=" * 60)
        
        return results
    
    def get_component(self, name: str) -> Any:
        """Get a started component"""
        return self._components.get(name)
    
    def is_running(self) -> bool:
        """Check if application is running"""
        return self.phase == LifecyclePhase.RUNNING
    
    def get_status(self) -> Dict[str, Any]:
        """Get lifecycle status"""
        return {
            "phase": self.phase.value,
            "components": list(self._components.keys()),
            "startup_order": self._startup_order,
            "startup_hooks": len(self._startup_hooks),
            "shutdown_hooks": len(self._shutdown_hooks)
        }


class GracefulShutdown:
    """
    Handles graceful shutdown on signals
    
    Example:
        shutdown = GracefulShutdown(lifecycle)
        shutdown.setup_signal_handlers()
    """
    
    def __init__(self, lifecycle: ApplicationLifecycle):
        self.lifecycle = lifecycle
        self._shutdown_event = asyncio.Event()
    
    def setup_signal_handlers(self):
        """Setup OS signal handlers"""
        import signal
        
        def handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
        
        logger.info("Signal handlers registered")
    
    async def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        await self._shutdown_event.wait()
        await self.lifecycle.stop()
