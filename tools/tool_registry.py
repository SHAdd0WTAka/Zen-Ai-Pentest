"""
Tool Registry für Zen-AI-Pentest
Dynamische Tool-Registrierung und Discovery für Issue #19
"""

from typing import Dict, List, Optional, Callable, Any, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import logging
import importlib
import inspect

from langchain_core.tools import BaseTool, Tool

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Kategorien für Tools"""
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"
    UTILITY = "utility"


class ToolSafetyLevel(Enum):
    """Sicherheitsstufen für Tools"""
    SAFE = "safe"  # Read-only, keine Gefahr
    NORMAL = "normal"  # Standard-Scans
    DANGEROUS = "dangerous"  # Könnte Systeme beeinflussen
    CRITICAL = "critical"  # Exploits, Payloads


@dataclass
class ToolMetadata:
    """Metadaten für ein registriertes Tool"""
    name: str
    description: str
    category: ToolCategory
    safety_level: ToolSafetyLevel
    requires_approval: bool = False
    supported_platforms: List[str] = field(default_factory=lambda: ["linux", "windows", "macos"])
    author: str = ""
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    
    # Runtime info
    invocation_count: int = 0
    avg_execution_time: float = 0.0
    last_used: Optional[str] = None


@dataclass  
class RegisteredTool:
    """Ein registriertes Tool mit all seinen Metadaten"""
    tool: BaseTool
    metadata: ToolMetadata
    enabled: bool = True
    
    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary für API/Frontend"""
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "category": self.metadata.category.value,
            "safety_level": self.metadata.safety_level.value,
            "requires_approval": self.metadata.requires_approval,
            "supported_platforms": self.metadata.supported_platforms,
            "enabled": self.enabled,
            "invocation_count": self.metadata.invocation_count,
            "tags": self.metadata.tags,
            "version": self.metadata.version
        }


class ToolRegistry:
    """
    Zentrale Tool Registry für dynamische Tool-Verwaltung
    
    Features:
    - Dynamische Tool-Registrierung
    - Tool Discovery nach Kategorie/Sicherheitsstufe
    - Runtime-Statistiken
    - Conditional Loading
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton Pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._tools: Dict[str, RegisteredTool] = {}
        self._categories: Dict[ToolCategory, List[str]] = {cat: [] for cat in ToolCategory}
        self._initialized = True
        
        logger.info("Tool Registry initialisiert")
    
    def register(
        self,
        tool: BaseTool,
        category: ToolCategory,
        safety_level: ToolSafetyLevel = ToolSafetyLevel.NORMAL,
        requires_approval: bool = False,
        supported_platforms: List[str] = None,
        author: str = "",
        version: str = "1.0.0",
        tags: List[str] = None,
        enabled: bool = True
    ) -> RegisteredTool:
        """
        Registriert ein neues Tool
        
        Args:
            tool: Das LangChain Tool
            category: Tool-Kategorie
            safety_level: Sicherheitsstufe
            requires_approval: Benötigt menschliche Freigabe?
            supported_platforms: Liste der unterstützten OS
            author: Tool-Author
            version: Tool-Version
            tags: Tags für Discovery
            enabled: Aktiviert?
            
        Returns:
            RegisteredTool Instanz
        """
        name = tool.name
        
        if name in self._tools:
            logger.warning(f"Tool '{name}' wird überschrieben")
        
        metadata = ToolMetadata(
            name=name,
            description=tool.description or "",
            category=category,
            safety_level=safety_level,
            requires_approval=requires_approval,
            supported_platforms=supported_platforms or ["linux", "windows", "macos"],
            author=author,
            version=version,
            tags=tags or []
        )
        
        registered = RegisteredTool(
            tool=tool,
            metadata=metadata,
            enabled=enabled
        )
        
        self._tools[name] = registered
        self._categories[category].append(name)
        
        logger.info(f"Tool registriert: {name} ({category.value}, {safety_level.value})")
        return registered
    
    def unregister(self, name: str) -> bool:
        """Entfernt ein Tool aus der Registry"""
        if name not in self._tools:
            return False
        
        tool = self._tools[name]
        self._categories[tool.metadata.category].remove(name)
        del self._tools[name]
        
        logger.info(f"Tool entfernt: {name}")
        return True
    
    def get(self, name: str) -> Optional[RegisteredTool]:
        """Holt ein Tool by Name"""
        return self._tools.get(name)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Holt das LangChain Tool by Name"""
        registered = self._tools.get(name)
        return registered.tool if registered and registered.enabled else None
    
    def list_tools(
        self,
        category: ToolCategory = None,
        safety_level: ToolSafetyLevel = None,
        enabled_only: bool = True,
        tags: List[str] = None
    ) -> List[RegisteredTool]:
        """
        Listet Tools mit Filtern
        
        Args:
            category: Filter nach Kategorie
            safety_level: Filter nach Sicherheitsstufe
            enabled_only: Nur aktivierte Tools?
            tags: Filter nach Tags (AND logic)
        """
        results = []
        
        for tool in self._tools.values():
            # Enabled Filter
            if enabled_only and not tool.enabled:
                continue
            
            # Category Filter
            if category and tool.metadata.category != category:
                continue
            
            # Safety Level Filter
            if safety_level and tool.metadata.safety_level != safety_level:
                continue
            
            # Tags Filter
            if tags:
                if not all(tag in tool.metadata.tags for tag in tags):
                    continue
            
            results.append(tool)
        
        return results
    
    def get_tools_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """Holt alle Tools einer Kategorie"""
        tool_names = self._categories.get(category, [])
        return [
            self._tools[name].tool 
            for name in tool_names 
            if name in self._tools and self._tools[name].enabled
        ]
    
    def get_safe_tools(self) -> List[BaseTool]:
        """Holt alle 'sicheren' Tools (keine Approval nötig)"""
        return [
            t.tool for t in self._tools.values()
            if t.enabled and not t.metadata.requires_approval
        ]
    
    def get_dangerous_tools(self) -> List[RegisteredTool]:
        """Holt alle 'gefährlichen' Tools (Approval nötig)"""
        return [
            t for t in self._tools.values()
            if t.metadata.safety_level in (ToolSafetyLevel.DANGEROUS, ToolSafetyLevel.CRITICAL)
            or t.metadata.requires_approval
        ]
    
    def enable_tool(self, name: str) -> bool:
        """Aktiviert ein Tool"""
        if name in self._tools:
            self._tools[name].enabled = True
            logger.info(f"Tool aktiviert: {name}")
            return True
        return False
    
    def disable_tool(self, name: str) -> bool:
        """Deaktiviert ein Tool"""
        if name in self._tools:
            self._tools[name].enabled = False
            logger.info(f"Tool deaktiviert: {name}")
            return True
        return False
    
    def record_invocation(self, name: str, execution_time: float):
        """Recorded eine Tool-Ausführung für Statistiken"""
        if name not in self._tools:
            return
        
        meta = self._tools[name].metadata
        meta.invocation_count += 1
        meta.last_used = datetime.now().isoformat()
        
        # Running average
        if meta.avg_execution_time == 0:
            meta.avg_execution_time = execution_time
        else:
            meta.avg_execution_time = (
                meta.avg_execution_time * (meta.invocation_count - 1) + execution_time
            ) / meta.invocation_count
    
    def get_all_tools(self) -> List[BaseTool]:
        """Holt alle aktivierten Tools als LangChain Tools"""
        return [t.tool for t in self._tools.values() if t.enabled]
    
    def get_registry_stats(self) -> dict:
        """Gibt Statistiken über die Registry"""
        total = len(self._tools)
        enabled = sum(1 for t in self._tools.values() if t.enabled)
        
        by_category = {
            cat.value: len(names) for cat, names in self._categories.items()
        }
        
        by_safety = {}
        for tool in self._tools.values():
            level = tool.metadata.safety_level.value
            by_safety[level] = by_safety.get(level, 0) + 1
        
        total_invocations = sum(
            t.metadata.invocation_count for t in self._tools.values()
        )
        
        return {
            "total_tools": total,
            "enabled_tools": enabled,
            "disabled_tools": total - enabled,
            "by_category": by_category,
            "by_safety_level": by_safety,
            "total_invocations": total_invocations
        }
    
    def discover_tools(self, module_path: str) -> List[RegisteredTool]:
        """
        Auto-Discovery von Tools in einem Modul
        
        Sucht nach Funktionen/Klassen mit @tool Decorator
        """
        discovered = []
        
        try:
            module = importlib.import_module(module_path)
            
            for name, obj in inspect.getmembers(module):
                if isinstance(obj, BaseTool):
                    # Tool gefunden, registriere mit Default-Metadaten
                    registered = self.register(
                        tool=obj,
                        category=ToolCategory.UTILITY,
                        safety_level=ToolSafetyLevel.NORMAL
                    )
                    discovered.append(registered)
                    
        except Exception as e:
            logger.error(f"Fehler beim Discovery in {module_path}: {e}")
        
        return discovered
    
    def clear(self):
        """Löscht alle registrierten Tools (für Testing)"""
        self._tools.clear()
        for cat in self._categories:
            self._categories[cat] = []


# Globale Registry Instanz
registry = ToolRegistry()


def register_tool(
    category: ToolCategory,
    safety_level: ToolSafetyLevel = ToolSafetyLevel.NORMAL,
    requires_approval: bool = False,
    **metadata_kwargs
):
    """
    Decorator für einfache Tool-Registrierung
    
    Usage:
        @register_tool(category=ToolCategory.SCANNING, safety_level=ToolSafetyLevel.SAFE)
        def my_scanner(target: str) -> str:
            return "result"
    """
    def decorator(func):
        # Erstelle LangChain Tool
        tool = Tool(
            name=func.__name__,
            description=func.__doc__ or "",
            func=func
        )
        
        # Registriere
        registry.register(
            tool=tool,
            category=category,
            safety_level=safety_level,
            requires_approval=requires_approval,
            **metadata_kwargs
        )
        
        return func
    return decorator


# Import hier um circular imports zu vermeiden
from datetime import datetime


if __name__ == "__main__":
    # Test
    from langchain_core.tools import tool as langchain_tool
    
    @langchain_tool
def example_scan(target: str) -> str:
    """Example scanning tool"""
    return f"Scanned {target}"

    
    # Manuelle Registrierung
    registry.register(
        tool=example_scan,
        category=ToolCategory.SCANNING,
        safety_level=ToolSafetyLevel.SAFE,
        tags=["example", "test"]
    )
    
    print("Registry Stats:", registry.get_registry_stats())
    print("Tools:", [t.name for t in registry.list_tools()])
