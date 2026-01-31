"""
Real Tool Calling Framework für Zen-AI-Pentest
Issue #19: Real Tool Calling Framework

Ermöglicht dynamisches Laden und Ausführen von Tools mit:
- Async Unterstützung
- Error Handling
- Timeout Management
- Result Validation
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from .tool_registry import ToolRegistry, ToolSafetyLevel, RegisteredTool

logger = logging.getLogger(__name__)


@dataclass
class ToolCallResult:
    """Ergebnis eines Tool-Aufrufs"""
    success: bool
    result: Any
    execution_time: float
    error: Optional[str] = None
    tool_name: str = ""
    safety_level: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result if self.success else None,
            "execution_time": round(self.execution_time, 2),
            "error": self.error,
            "tool_name": self.tool_name,
            "safety_level": self.safety_level
        }


class ToolCaller:
    """
    Echter Tool Calling Framework mit:
    - Async Execution
    - Timeout Management  
    - Thread Pool für blocking Tools
    - Result Validation
    """
    
    def __init__(self, registry: ToolRegistry = None, max_workers: int = 5):
        self.registry = registry or ToolRegistry()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.default_timeout = 300  # 5 Minuten
        
        logger.info(f"ToolCaller initialisiert mit {max_workers} workers")
    
    async def call_tool(
        self, 
        tool_name: str, 
        args: Dict[str, Any], 
        timeout: int = None,
        validate_result: bool = True
    ) -> ToolCallResult:
        """
        Ruft ein Tool asynchron auf
        
        Args:
            tool_name: Name des Tools in der Registry
            args: Argumente für das Tool
            timeout: Timeout in Sekunden (default: 300)
            validate_result: Soll das Ergebnis validiert werden?
            
        Returns:
            ToolCallResult mit Ergebnis oder Fehler
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        # Tool aus Registry holen
        registered = self.registry.get(tool_name)
        if not registered:
            return ToolCallResult(
                success=False,
                result=None,
                execution_time=0,
                error=f"Tool '{tool_name}' nicht in Registry gefunden",
                tool_name=tool_name
            )
        
        if not registered.enabled:
            return ToolCallResult(
                success=False,
                result=None,
                execution_time=0,
                error=f"Tool '{tool_name}' ist deaktiviert",
                tool_name=tool_name,
                safety_level=registered.metadata.safety_level.value
            )
        
        tool = registered.tool
        
        try:
            # Async oder Sync execution
            if asyncio.iscoroutinefunction(tool.func):
                # Tool ist async
                logger.debug(f"[ASYNC] Rufe {tool_name} auf")
                result = await asyncio.wait_for(
                    tool.ainvoke(args),
                    timeout=timeout
                )
            else:
                # Tool ist sync - im Thread Pool ausführen
                logger.debug(f"[SYNC] Rufe {tool_name} im Thread Pool auf")
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(self.executor, lambda: tool.invoke(args)),
                    timeout=timeout
                )
            
            execution_time = time.time() - start_time
            
            # Record invocation
            self.registry.record_invocation(tool_name, execution_time)
            
            # Validate result
            if validate_result and not self._validate_result(result):
                return ToolCallResult(
                    success=False,
                    result=result,
                    execution_time=execution_time,
                    error="Ergebnis-Validierung fehlgeschlagen",
                    tool_name=tool_name,
                    safety_level=registered.metadata.safety_level.value
                )
            
            return ToolCallResult(
                success=True,
                result=result,
                execution_time=execution_time,
                tool_name=tool_name,
                safety_level=registered.metadata.safety_level.value
            )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.error(f"Timeout bei {tool_name} nach {timeout}s")
            return ToolCallResult(
                success=False,
                result=None,
                execution_time=execution_time,
                error=f"Timeout nach {timeout} Sekunden",
                tool_name=tool_name,
                safety_level=registered.metadata.safety_level.value
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Fehler bei {tool_name}: {e}")
            return ToolCallResult(
                success=False,
                result=None,
                execution_time=execution_time,
                error=str(e),
                tool_name=tool_name,
                safety_level=registered.metadata.safety_level.value
            )
    
    async def call_tools_parallel(
        self, 
        tool_calls: List[tuple],
        timeout: int = None
    ) -> Dict[str, ToolCallResult]:
        """
        Ruft mehrere Tools parallel auf
        
        Args:
            tool_calls: Liste von (tool_name, args) Tupeln
            timeout: Timeout pro Tool
            
        Returns:
            Dict mapping tool_name -> ToolCallResult
        """
        tasks = []
        tool_names = []
        
        for tool_name, args in tool_calls:
            task = self.call_tool(tool_name, args, timeout)
            tasks.append(task)
            tool_names.append(tool_name)
        
        # Alle parallel ausführen
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Ergebnisse zuordnen
        output = {}
        for name, result in zip(tool_names, results):
            if isinstance(result, Exception):
                output[name] = ToolCallResult(
                    success=False,
                    result=None,
                    execution_time=0,
                    error=f"Unhandled exception: {result}",
                    tool_name=name
                )
            else:
                output[name] = result
        
        return output
    
    def _validate_result(self, result: Any) -> bool:
        """Validiert das Tool-Ergebnis"""
        # Basis-Validierung: Nicht None und nicht leer
        if result is None:
            return False
        
        if isinstance(result, (str, list, dict)) and len(result) == 0:
            return False
        
        # TODO: Erweiterte Validierung je nach Tool-Typ
        return True
    
    async def get_tool_status(self, tool_name: str) -> Dict[str, Any]:
        """Gibt den Status eines Tools zurück"""
        registered = self.registry.get(tool_name)
        if not registered:
            return {"error": f"Tool '{tool_name}' nicht gefunden"}
        
        return {
            "name": tool_name,
            "enabled": registered.enabled,
            "safety_level": registered.metadata.safety_level.value,
            "category": registered.metadata.category.value,
            "invocation_count": registered.metadata.invocation_count,
            "avg_execution_time": registered.metadata.avg_execution_time,
            "last_used": registered.metadata.last_used,
            "requires_approval": registered.metadata.requires_approval
        }
    
    async def get_all_tool_status(self) -> List[Dict[str, Any]]:
        """Gibt Status aller Tools zurück"""
        tools = self.registry.list_tools(enabled_only=False)
        return [tool.to_dict() for tool in tools]
    
    def shutdown(self):
        """Shutdown des Thread Pools"""
        self.executor.shutdown(wait=True)
        logger.info("ToolCaller heruntergefahren")


# Convenience Funktionen

async def call_tool(tool_name: str, **kwargs) -> ToolCallResult:
    """
    Convenience Funktion für einfachen Tool-Aufruf
    
    Usage:
        result = await call_tool("scan_ports", target="scanme.nmap.org")
    """
    caller = ToolCaller()
    return await caller.call_tool(tool_name, kwargs)


async def call_tools_batch(calls: List[tuple]) -> Dict[str, ToolCallResult]:
    """
    Convenience Funktion für parallele Tool-Aufrufe
    
    Usage:
        results = await call_tools_batch([
            ("scan_ports", {"target": "scanme.nmap.org"}),
            ("scan_vulnerabilities", {"target": "scanme.nmap.org"})
        ])
    """
    caller = ToolCaller()
    return await caller.call_tools_parallel(calls)


# Singleton
_default_caller = None

def get_tool_caller() -> ToolCaller:
    """Gibt den default ToolCaller zurück"""
    global _default_caller
    if _default_caller is None:
        _default_caller = ToolCaller()
    return _default_caller


if __name__ == "__main__":
    # Test
    import asyncio
    
    async def test():
        # Test mit Mock-Tool
        from langchain_core.tools import tool
        
        @tool
        def test_tool(name: str) -> str:
            """Test tool"""
            return f"Hello {name}"
        
        registry = ToolRegistry()
        registry.register(
            tool=test_tool,
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE
        )
        
        caller = ToolCaller(registry)
        result = await caller.call_tool("test_tool", {"name": "World"})
        print(f"Result: {result}")
        
        caller.shutdown()
    
    asyncio.run(test())
