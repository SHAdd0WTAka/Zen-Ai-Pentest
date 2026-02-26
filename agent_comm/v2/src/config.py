"""
Configuration for gRPC Agent Communication v2.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GRPCServerConfig:
    """Configuration for gRPC server.
    
    Attributes:
        bind_address: Address to bind the server to (default: "[::]:50051")
        max_workers: Maximum number of worker threads (default: 10)
        use_tls: Whether to use TLS encryption (default: True)
        tls_cert_path: Path to TLS certificate file
        tls_key_path: Path to TLS key file
        tls_ca_path: Path to TLS CA certificate file
        max_message_size: Maximum message size in bytes (default: 10MB)
        keepalive_time_ms: Keepalive time in milliseconds
        keepalive_timeout_ms: Keepalive timeout in milliseconds
        enable_reflection: Enable gRPC reflection (default: True)
        enable_compression: Enable compression (default: True)
    """
    
    bind_address: str = "[::]:50051"
    max_workers: int = 10
    use_tls: bool = True
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    tls_ca_path: Optional[str] = None
    max_message_size: int = 10 * 1024 * 1024  # 10MB
    keepalive_time_ms: int = 10000
    keepalive_timeout_ms: int = 5000
    enable_reflection: bool = True
    enable_compression: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if self.max_message_size < 1024:
            raise ValueError("max_message_size must be at least 1KB")


@dataclass  
class GRPCClientConfig:
    """Configuration for gRPC client.
    
    Attributes:
        server_address: Address of the gRPC server
        use_tls: Whether to use TLS encryption
        tls_cert_path: Path to TLS certificate file
        tls_ca_path: Path to TLS CA certificate file
        timeout_seconds: Default timeout for RPC calls
        max_retries: Maximum number of retries for failed calls
        retry_delay_seconds: Delay between retries
    """
    
    server_address: str = "localhost:50051"
    use_tls: bool = True
    tls_cert_path: Optional[str] = None
    tls_ca_path: Optional[str] = None
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.server_address:
            raise ValueError("server_address is required")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
