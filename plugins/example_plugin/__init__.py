"""
Example Plugin for Zen AI Pentest

Demonstrates how to create a custom plugin.
"""

from core.plugin_manager import BasePlugin, PluginType


class ExamplePlugin(BasePlugin):
    """
    Example plugin showing the plugin structure.

    This plugin demonstrates:
    - Configuration handling
    - Hook registration
    - Execution flow
    """

    # Required metadata
    NAME = "example_plugin"
    VERSION = "1.0.0"
    DESCRIPTION = "Example plugin demonstrating the plugin system"
    AUTHOR = "SHAdd0WTAka"
    PLUGIN_TYPE = PluginType.TOOL

    async def initialize(self) -> bool:
        """Called when plugin is loaded"""
        self.logger.info(f"Initializing {self.NAME} v{self.VERSION}")

        # Access configuration
        api_key = self.get_config("api_key")
        if not api_key:
            self.logger.warning("No API key configured")

        return True

    async def execute(self, target: str, **kwargs) -> dict:
        """
        Main plugin functionality.

        Args:
            target: Target to analyze
            **kwargs: Additional parameters

        Returns:
            Analysis results
        """
        self.logger.info(f"Running example plugin on {target}")

        # Simulate work
        result = {
            "target": target,
            "plugin": self.NAME,
            "version": self.VERSION,
            "findings": [
                {"type": "info", "message": f"Example finding for {target}"}
            ],
        }

        return result

    async def shutdown(self):
        """Called when plugin is unloaded"""
        self.logger.info(f"Shutting down {self.NAME}")

    def validate_config(self) -> bool:
        """Validate plugin configuration"""
        # Example: require certain config keys
        required = []
        for key in required:
            if not self.get_config(key):
                self.logger.error(f"Missing required config: {key}")
                return False
        return True

    # Hook callback example
    async def on_scan_complete(self, scan_results: dict):
        """Called when a scan completes (if hook is registered)"""
        self.logger.info(f"Scan completed: {scan_results.get('scan_id')}")


# Plugin entry point
plugin_class = ExamplePlugin
