"""Smoke tests for core/port_manager_integration.py"""

import pytest

from core.port_manager_integration import (
    PentestPortAllocator,
    SecurePortManager,
    ServiceRegistration,
    ServiceType,
    get_secure_port_manager,
)


class TestServiceType:
    def test_values(self):
        assert ServiceType.NATIVE.value == "native"
        assert ServiceType.DOCKER.value == "docker"
        assert ServiceType.PYTHON.value == "python"
        assert ServiceType.NODE.value == "node"


class TestServiceRegistration:
    def test_creation(self):
        reg = ServiceRegistration(
            name="nmap-api",
            command="docker run -p {port}:8080 nmap-api",
            service_type=ServiceType.DOCKER,
        )
        assert reg.name == "nmap-api"
        assert reg.service_type == ServiceType.DOCKER
        assert reg.port is None
        assert reg.security_level == "standard"


class TestSecurePortManager:
    def test_init(self):
        pm = SecurePortManager()
        assert pm.proxy_port == 1355
        assert pm.enable_kill_switch is True
        assert pm._services == {}

    def test_list_services_empty(self):
        pm = SecurePortManager()
        assert pm.list_services() == []

    def test_get_service_url_nonexistent(self):
        pm = SecurePortManager()
        assert pm.get_service_url("nonexistent") is None

    def test_check_security(self):
        pm = SecurePortManager()
        status = pm.check_security()
        assert "lpm_available" in status
        assert "vpn_active" in status
        assert "kill_switch_enabled" in status
        assert "docker_safe" in status

    def test_detect_service_type_docker(self):
        pm = SecurePortManager()
        assert pm._detect_service_type("docker run nmap") == ServiceType.DOCKER

    def test_detect_service_type_python(self):
        pm = SecurePortManager()
        assert pm._detect_service_type("python app.py") == ServiceType.PYTHON

    def test_detect_service_type_native(self):
        pm = SecurePortManager()
        assert pm._detect_service_type("some_binary --flag") == ServiceType.NATIVE


class TestPentestPortAllocator:
    def test_init(self):
        allocator = PentestPortAllocator()
        assert allocator._next_port == 9000
        assert allocator._fallback_ports == {}


class TestGetSecurePortManager:
    def test_returns_secure_port_manager(self):
        pm = get_secure_port_manager()
        assert isinstance(pm, SecurePortManager)
