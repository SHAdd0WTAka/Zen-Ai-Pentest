# Plugin System Documentation

## Overview

The Zen AI Pentest Plugin System allows developers to extend the framework with custom modules. Plugins can add new scanners, exploits, report generators, and integrate with external tools.

## Features

- **Dynamic Loading** - Load/unload plugins at runtime
- **Hook System** - Register callbacks for framework events
- **Filter System** - Modify data through filter chains
- **Dependency Management** - Automatic dependency resolution
- **Sandboxed Execution** - Isolated plugin environments
- **Configuration** - Schema-based configuration management

## Quick Start

### 1. Create a Plugin

Create a new directory in `plugins/`:

```bash
mkdir plugins/my_plugin
cd plugins/my_plugin
```

### 2. Create Plugin Class

Create `__init__.py`:

```python
from core.plugin_manager import BasePlugin, PluginType

class MyPlugin(BasePlugin):
    NAME = "my_plugin"
    VERSION = "1.0.0"
    DESCRIPTION = "My custom plugin"
    AUTHOR = "Your Name"
    PLUGIN_TYPE = PluginType.TOOL
    
    async def initialize(self) -> bool:
        """Called when plugin is loaded"""
        self.logger.info(f"{self.NAME} initialized")
        return True
    
    async def execute(self, target: str, **kwargs) -> dict:
        """Main functionality"""
        return {
            "target": target,
            "status": "success",
            "data": "Your results here"
        }
    
    async def shutdown(self):
        """Cleanup"""
        pass

plugin_class = MyPlugin
```

### 3. Add Metadata (Optional)

Create `plugin.json`:

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "My custom plugin",
  "author": "Your Name",
  "type": "tool",
  "dependencies": [],
  "hooks": ["scan_complete"],
  "config_schema": {
    "api_key": {
      "type": "string",
      "description": "API key",
      "required": true
    }
  }
}
```

### 4. Use the Plugin

```python
from core.plugin_manager import plugin_manager

# Load plugin
await plugin_manager.load_plugin("my_plugin", config={"api_key": "secret"})

# Execute
result = await plugin_manager.execute_plugin("my_plugin", target="example.com")

# Unload
await plugin_manager.unload_plugin("my_plugin")
```

## Plugin Types

| Type | Description |
|------|-------------|
| `scanner` | Vulnerability scanners |
| `exploit` | Exploit modules |
| `report` | Report generators |
| `osint` | OSINT sources |
| `post` | Post-exploitation |
| `tool` | External tools |
| `notifier` | Notification services |
| `auth` | Authentication providers |

## Hook System

### Available Hooks

| Hook | Description | Parameters |
|------|-------------|------------|
| `scan_start` | Scan initiated | `scan_id` |
| `scan_complete` | Scan finished | `scan_id`, `findings` |
| `finding_discovered` | New finding | `finding` |
| `report_generated` | Report created | `report_path` |

### Registering Hooks

```python
async def on_scan_complete(scan_id: str, findings: int):
    print(f"Scan {scan_id} completed with {findings} findings")

# In your plugin
from core.plugin_manager import register_hook
register_hook("scan_complete", on_scan_complete, priority=10)
```

### Executing Hooks

```python
from core.plugin_manager import execute_hook

results = await execute_hook("scan_complete", "scan_123", 5)
```

## Filter System

### Registering Filters

```python
async def enhance_report(report_data: dict, **kwargs):
    report_data["enhanced"] = True
    return report_data

plugin_manager.hooks.register_filter("generate_report", enhance_report)
```

### Applying Filters

```python
result = await plugin_manager.hooks.apply_filter("generate_report", report_data)
```

## Configuration

### Accessing Config

```python
# In your plugin
api_key = self.get_config("api_key", default="")
timeout = self.get_config("timeout", default=30)
```

### Validation

```python
def validate_config(self) -> bool:
    if not self.get_config("api_key"):
        self.logger.error("API key is required")
        return False
    return True
```

## API Integration

Plugins can add their own API endpoints:

```python
# In your plugin
async def get_routes(self):
    from fastapi import APIRouter
    
    router = APIRouter()
    
    @router.get("/my-plugin/status")
    async def status():
        return {"status": "ok"}
    
    return router
```

## Examples

### Scanner Plugin

```python
from core.plugin_manager import BasePlugin, PluginType
from modules.vuln_scanner import VulnScannerModule

class CustomScanner(BasePlugin):
    NAME = "custom_scanner"
    PLUGIN_TYPE = PluginType.SCANNER
    
    async def execute(self, target: str, **kwargs):
        scanner = VulnScannerModule()
        findings = await scanner.scan(target)
        return {"findings": findings}
```

### Notifier Plugin

```python
from core.plugin_manager import BasePlugin, PluginType

class SlackNotifier(BasePlugin):
    NAME = "slack_notifier"
    PLUGIN_TYPE = PluginType.NOTIFIER
    
    async def on_scan_complete(self, scan_id: str, findings: int):
        webhook = self.get_config("webhook_url")
        # Send Slack notification
        await self.send_notification(webhook, f"Scan {scan_id} completed")
```

### Report Plugin

```python
from core.plugin_manager import BasePlugin, PluginType

class PDFReport(BasePlugin):
    NAME = "pdf_report"
    PLUGIN_TYPE = PluginType.REPORT
    
    async def execute(self, findings: list, **kwargs):
        # Generate PDF report
        pdf_path = f"reports/report_{datetime.now().timestamp()}.pdf"
        # ... generation logic ...
        return {"report_path": pdf_path}
```

## Best Practices

1. **Error Handling** - Always handle exceptions gracefully
2. **Logging** - Use `self.logger` for all log messages
3. **Configuration** - Validate config in `validate_config()`
4. **Cleanup** - Implement `shutdown()` for cleanup
5. **Documentation** - Document your plugin's API
6. **Testing** - Write tests for your plugin

## Distribution

### Package Your Plugin

```bash
cd plugins/my_plugin
zip -r my_plugin.zip .
```

### Install Plugin

```bash
# Extract to plugins directory
unzip my_plugin.zip -d plugins/my_plugin

# Or use API
POST /api/v1/plugins/install
Content-Type: multipart/form-data

file: my_plugin.zip
```

## Troubleshooting

### Plugin Not Loading
- Check `plugin.json` syntax
- Verify class name matches
- Check logs for errors

### Hook Not Called
- Verify hook name is correct
- Check priority order
- Ensure plugin is loaded

### Configuration Issues
- Validate JSON in `plugin.json`
- Check required fields
- Verify types match

## Demo

Run the plugin demo:

```bash
python examples/plugin_demo.py
```

## Reference

- Example plugin: `plugins/example_plugin/`
- Base class: `core/plugin_manager.py`
- API routes: `api/routes/plugins.py`

---

*Extend Zen AI Pentest with your own plugins!*
