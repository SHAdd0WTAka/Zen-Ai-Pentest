"""
Configuration for Kimi Authentication Bridge
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class KimiConfig:
    """Configuration for KimiAuthBridge
    
    Attributes:
        credentials_path: Path to Kimi CLI credentials file
        api_base: Kimi API base URL
        model: Default model to use
        user_agent: User-Agent header for API requests
    """
    
    credentials_path: Optional[Path] = None
    api_base: str = "https://api.kimi.com/coding/v1"
    model: str = "kimi-for-coding"
    user_agent: str = "KimiCLI/1.0.0"
    
    def __post_init__(self):
        """Set default credentials path if not provided"""
        if self.credentials_path is None:
            self.credentials_path = Path.home() / ".kimi" / "credentials" / "kimi-code.json"
    
    @property
    def chat_completions_url(self) -> str:
        """Get the chat completions endpoint URL"""
        return f"{self.api_base}/chat/completions"
    
    @property
    def models_url(self) -> str:
        """Get the models endpoint URL"""
        return f"{self.api_base}/models"
