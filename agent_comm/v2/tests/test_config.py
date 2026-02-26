"""
Comprehensive tests for agent_comm/v2/src/config.py
Target: 80%+ Coverage
"""

import pytest
from agent_comm.v2.src.config import GRPCServerConfig, GRPCClientConfig


class TestGRPCServerConfig:
    """Tests for GRPCServerConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = GRPCServerConfig()
        
        assert config.bind_address == "[::]:50051"
        assert config.max_workers == 10
        assert config.use_tls is True
        assert config.tls_cert_path is None
        assert config.tls_key_path is None
        assert config.tls_ca_path is None
        assert config.max_message_size == 10 * 1024 * 1024
        assert config.keepalive_time_ms == 10000
        assert config.keepalive_timeout_ms == 5000
        assert config.enable_reflection is True
        assert config.enable_compression is True
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = GRPCServerConfig(
            bind_address="0.0.0.0:8080",
            max_workers=20,
            use_tls=False,
            tls_cert_path="/path/to/cert.pem",
            tls_key_path="/path/to/key.pem",
            max_message_size=50 * 1024 * 1024,
            enable_reflection=False
        )
        
        assert config.bind_address == "0.0.0.0:8080"
        assert config.max_workers == 20
        assert config.use_tls is False
        assert config.tls_cert_path == "/path/to/cert.pem"
        assert config.tls_key_path == "/path/to/key.pem"
        assert config.max_message_size == 50 * 1024 * 1024
        assert config.enable_reflection is False
    
    def test_validation_max_workers_zero(self):
        """Test validation for max_workers=0."""
        with pytest.raises(ValueError, match="max_workers must be at least 1"):
            GRPCServerConfig(max_workers=0)
    
    def test_validation_max_workers_negative(self):
        """Test validation for negative max_workers."""
        with pytest.raises(ValueError, match="max_workers must be at least 1"):
            GRPCServerConfig(max_workers=-1)
    
    def test_validation_max_message_size_too_small(self):
        """Test validation for too small max_message_size."""
        with pytest.raises(ValueError, match="max_message_size must be at least 1KB"):
            GRPCServerConfig(max_message_size=500)


class TestGRPCClientConfig:
    """Tests for GRPCClientConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = GRPCClientConfig()
        
        assert config.server_address == "localhost:50051"
        assert config.use_tls is True
        assert config.tls_cert_path is None
        assert config.tls_ca_path is None
        assert config.timeout_seconds == 30.0
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 1.0
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = GRPCClientConfig(
            server_address="192.168.1.100:50051",
            use_tls=False,
            timeout_seconds=60.0,
            max_retries=5,
            retry_delay_seconds=2.0
        )
        
        assert config.server_address == "192.168.1.100:50051"
        assert config.use_tls is False
        assert config.timeout_seconds == 60.0
        assert config.max_retries == 5
        assert config.retry_delay_seconds == 2.0
    
    def test_validation_empty_server_address(self):
        """Test validation for empty server_address."""
        with pytest.raises(ValueError, match="server_address is required"):
            GRPCClientConfig(server_address="")
    
    def test_validation_zero_timeout(self):
        """Test validation for zero timeout."""
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            GRPCClientConfig(timeout_seconds=0)
    
    def test_validation_negative_timeout(self):
        """Test validation for negative timeout."""
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            GRPCClientConfig(timeout_seconds=-1.0)
    
    def test_validation_negative_retries(self):
        """Test validation for negative retries."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            GRPCClientConfig(max_retries=-1)
    
    def test_validation_zero_retries_allowed(self):
        """Test that zero retries is allowed."""
        config = GRPCClientConfig(max_retries=0)
        assert config.max_retries == 0
