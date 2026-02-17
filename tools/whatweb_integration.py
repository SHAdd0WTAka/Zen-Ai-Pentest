"""
WhatWeb Integration - Web Technology Detection
Erkennt CMS, Frameworks, Server-Software, etc.
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Technology:
    """Detected technology"""
    name: str
    version: str = ""
    confidence: int = 100
    category: str = ""
    description: str = ""


@dataclass
class WhatWebResult:
    """WhatWeb scan result"""
    success: bool
    url: str = ""
    technologies: List[Technology] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    plugins: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    raw_output: str = ""


class WhatWebIntegration:
    """WhatWeb Technology Detection"""
    
    def __init__(self, aggression: int = 1):
        """
        Args:
            aggression: Aggression level (1=passive, 3=aggressive)
        """
        self.aggression = aggression
        
    async def scan(
        self,
        target: str,
        user_agent: Optional[str] = None
    ) -> WhatWebResult:
        """
        Scan a target for technologies
        
        Args:
            target: Target URL
            user_agent: Custom User-Agent string
        """
        # Validate target
        if not target.startswith(("http://", "https://")):
            target = f"http://{target}"
            
        cmd = [
            "whatweb",
            "--log-json", "-",
            "-a", str(self.aggression),
        ]
        
        if user_agent:
            cmd.extend(["--user-agent", user_agent])
            
        cmd.append(target)
        
        logger.info(f"Starting WhatWeb scan: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"WhatWeb error: {error_msg}")
                return WhatWebResult(success=False, error=error_msg)
                
            # Parse JSON output
            output = stdout.decode().strip()
            technologies = []
            headers = {}
            plugins = {}
            
            try:
                # WhatWeb outputs JSON Lines format
                for line in output.split('\n'):
                    if not line:
                        continue
                    # Clean ANSI escape codes
                    line = self._clean_ansi(line)
                    data = json.loads(line)
                    
                    url = data.get("target", target)
                    plugins_data = data.get("plugins", {})
                    
                    for plugin_name, plugin_info in plugins_data.items():
                        # Clean plugin name from ANSI codes
                        plugin_name = self._clean_ansi(plugin_name)
                        
                        if plugin_name == "Headers":
                            headers = plugin_info.get("string", [{}])[0] if isinstance(plugin_info.get("string"), list) else {}
                            continue
                            
                        version = ""
                        if isinstance(plugin_info, dict):
                            version_strings = plugin_info.get("version", [])
                            if version_strings:
                                version = version_strings[0] if isinstance(version_strings, list) else str(version_strings)
                                # Clean version from ANSI codes
                                version = self._clean_ansi(version)
                                
                        confidence = plugin_info.get("confidence", [100])
                        confidence = confidence[0] if isinstance(confidence, list) else confidence
                        
                        # Skip lines that are clearly parsing errors
                        if len(plugin_name) > 100 or '\n' in plugin_name:
                            continue
                            
                        tech = Technology(
                            name=plugin_name,
                            version=version,
                            confidence=int(confidence),
                            category=self._categorize(plugin_name)
                        )
                        technologies.append(tech)
                        plugins[plugin_name] = plugin_info
                        
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error: {e}")
                # Fallback: parse text output
                technologies = self._parse_text_output(output)
                
            return WhatWebResult(
                success=True,
                url=target,
                technologies=technologies,
                headers=headers,
                plugins=plugins,
                raw_output=output
            )
            
        except asyncio.TimeoutError:
            logger.error("WhatWeb scan timed out")
            return WhatWebResult(success=False, error="Timeout")
        except Exception as e:
            logger.error(f"WhatWeb error: {e}")
            return WhatWebResult(success=False, error=str(e))
            
    def _clean_ansi(self, text: str) -> str:
        """Remove ANSI escape codes from text"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
        
    def _categorize(self, plugin_name: str) -> str:
        """Categorize technology"""
        categories = {
            "Apache": "Web Server",
            "nginx": "Web Server",
            "IIS": "Web Server",
            "PHP": "Programming Language",
            "Python": "Programming Language",
            "Ruby": "Programming Language",
            "Java": "Programming Language",
            "WordPress": "CMS",
            "Drupal": "CMS",
            "Joomla": "CMS",
            "jQuery": "JavaScript Library",
            "React": "JavaScript Framework",
            "Angular": "JavaScript Framework",
            "Bootstrap": "CSS Framework",
            "MySQL": "Database",
            "PostgreSQL": "Database",
        }
        return categories.get(plugin_name, "Other")
        
    def _parse_text_output(self, output: str) -> List[Technology]:
        """Fallback parser for text output"""
        technologies = []
        # Pattern: URL [Technology1][Technology2(Version)]
        matches = re.findall(r'\[([^\]]+)\]', output)
        for match in matches:
            if '(' in match:
                name, version = match.split('(', 1)
                version = version.rstrip(')')
            else:
                name = match
                version = ""
            technologies.append(Technology(name=name, version=version))
        return technologies


# Sync wrapper
def scan_sync(target: str, aggression: int = 1) -> WhatWebResult:
    """Synchronous wrapper"""
    whatweb = WhatWebIntegration(aggression=aggression)
    return asyncio.run(whatweb.scan(target))


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing WhatWeb Integration...")
    print("="*60)
    
    result = scan_sync("http://scanme.nmap.org")
    
    print(f"Success: {result.success}")
    print(f"URL: {result.url}")
    print(f"\nDetected Technologies ({len(result.technologies)}):")
    for tech in result.technologies:
        version_str = f" ({tech.version})" if tech.version else ""
        print(f"  • {tech.name}{version_str} [{tech.confidence}%]")
