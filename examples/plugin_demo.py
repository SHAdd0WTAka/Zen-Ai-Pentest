#!/usr/bin/env python3
"""
Plugin System Demo

Demonstrates the plugin architecture:
- Plugin discovery
- Loading and unloading
- Hook system
- Plugin execution
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.plugin_manager import PluginManager


async def demo_plugin_system():
    """Demonstrate plugin system capabilities"""
    print("\n" + "=" * 60)
    print("  Zen AI Pentest - Plugin System Demo")
    print("=" * 60 + "\n")

    # Initialize plugin manager
    manager = PluginManager(plugin_dirs=["plugins", "custom_plugins"])

    # =================================================================
    # 1. Plugin Discovery
    # =================================================================
    print("[1] Discovering plugins...")
    discovered = manager.discover_plugins()

    print(f"    Found {len(discovered)} plugin(s):\n")
    for plugin in discovered:
        print(f"    - {plugin.name} v{plugin.version}")
        print(f"      Type: {plugin.plugin_type.value}")
        print(f"      Author: {plugin.author}")
        print(f"      Description: {plugin.description}")
        print()

    # =================================================================
    # 2. Load Plugins
    # =================================================================
    print("[2] Loading plugins...\n")

    for plugin_info in discovered:
        print(f"    Loading {plugin_info.name}...")
        success = await manager.load_plugin(plugin_info.name)

        if success:
            print(f"    ✓ {plugin_info.name} loaded successfully")
        else:
            print(f"    ✗ Failed to load {plugin_info.name}")
            if plugin_info.error_message:
                print(f"      Error: {plugin_info.error_message}")

    # =================================================================
    # 3. List Loaded Plugins
    # =================================================================
    print("\n[3] Loaded plugins:\n")

    all_plugins = manager.get_all_plugins()
    for name, info in all_plugins.items():
        status_icon = "✓" if info.status.value == "loaded" else "✗"
        print(f"    {status_icon} {name} v{info.version} - {info.status.value}")

    # =================================================================
    # 4. Execute Plugin
    # =================================================================
    print("\n[4] Executing plugins:\n")

    for name, plugin in manager.plugins.items():
        print(f"    Executing {name}...")
        try:
            result = await manager.execute_plugin(name, target="example.com", options={"aggressive": False})
            print(f"    Result: {result}")
        except Exception as e:
            print(f"    Error: {e}")

    # =================================================================
    # 5. Hook System Demo
    # =================================================================
    print("\n[5] Hook system demonstration:\n")

    # Define a hook callback
    async def on_scan_start(scan_id: str):
        print(f"    [Hook] Scan started: {scan_id}")
        return {"hook": "scan_start", "scan_id": scan_id}

    async def on_scan_complete(scan_id: str, findings: int):
        print(f"    [Hook] Scan completed: {scan_id} with {findings} findings")
        return {"hook": "scan_complete", "scan_id": scan_id, "findings": findings}

    # Register hooks
    manager.hooks.register_hook("scan_start", on_scan_start, priority=1)
    manager.hooks.register_hook("scan_complete", on_scan_complete, priority=1)

    # Execute hooks
    print("    Executing 'scan_start' hook...")
    results = await manager.hooks.execute_hook("scan_start", "scan_123")
    print(f"    Hook results: {results}\n")

    print("    Executing 'scan_complete' hook...")
    results = await manager.hooks.execute_hook("scan_complete", "scan_123", 5)
    print(f"    Hook results: {results}")

    # =================================================================
    # 6. Filter System Demo
    # =================================================================
    print("\n[6] Filter system demonstration:\n")

    # Define filters
    async def add_prefix(data: str, **kwargs):
        return f"[FILTERED] {data}"

    async def uppercase(data: str, **kwargs):
        return data.upper()

    # Register filters
    manager.hooks.register_filter("process_data", add_prefix, priority=1)
    manager.hooks.register_filter("process_data", uppercase, priority=2)

    # Apply filters
    input_data = "example data"
    print(f"    Input: {input_data}")
    result = await manager.hooks.apply_filter("process_data", input_data)
    print(f"    Output: {result}")

    # =================================================================
    # 7. Unload Plugins
    # =================================================================
    print("\n[7] Unloading plugins:\n")

    for name in list(manager.plugins.keys()):
        print(f"    Unloading {name}...")
        await manager.unload_plugin(name)
        print(f"    ✓ {name} unloaded")

    print("\n" + "=" * 60)
    print("  Plugin System Demo Complete!")
    print("=" * 60)

    print(
        """
Plugin System Features:
✅ Dynamic plugin discovery
✅ Runtime loading/unloading
✅ Hook system for events
✅ Filter system for data processing
✅ Dependency management
✅ Configuration management
✅ Priority-based execution

To create your own plugin:
1. Create a directory in plugins/
2. Add __init__.py with your plugin class
3. Inherit from BasePlugin
4. Implement initialize() and execute()
5. Optionally add plugin.json for metadata

See plugins/example_plugin/ for reference implementation.
"""
    )


if __name__ == "__main__":
    try:
        asyncio.run(demo_plugin_system())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
