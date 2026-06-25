"""Smoke tests for virtualization/ modules"""

import pytest

from virtualization.cloud_vm_manager import (
    AWSProvider,
    CloudProviderBase,
    CloudVMConfig,
    CloudVMManager,
    create_aws_manager,
    create_gcp_manager,
)
from virtualization.vm_manager import PentestSandbox, VirtualBoxManager, VMConfig, get_vm_manager


class TestCloudVMConfig:
    def test_minimal(self):
        cfg = CloudVMConfig(
            provider="aws",
            instance_type="t3.medium",
            image_id="ami-12345",
            region="us-east-1",
            ssh_key_name="my-key",
        )
        assert cfg.provider == "aws"
        assert cfg.auto_shutdown_after_hours == 4

    def test_with_tags(self):
        cfg = CloudVMConfig(
            provider="gcp",
            instance_type="e2-medium",
            image_id="family/kali-linux",
            region="us-central1",
            ssh_key_name="key",
            tags={"Environment": "pentest"},
        )
        assert cfg.tags["Environment"] == "pentest"


class TestCloudProviderBase:
    def test_abstract(self):
        with pytest.raises(TypeError):
            CloudProviderBase()


class TestCloudVMManager:
    def test_init(self):
        manager = CloudVMManager()
        assert manager.providers == {}
        assert manager.active_instances == {}

    def test_add_provider(self):
        manager = CloudVMManager()
        provider = AWSProvider.__new__(AWSProvider)
        manager.add_provider("aws", provider)
        assert "aws" in manager.providers

    def test_create_instance_no_provider(self):
        manager = CloudVMManager()
        with pytest.raises(ValueError, match="nicht konfiguriert"):
            manager.create_instance("nonexistent", None, "test-vm")

    def test_list_all_empty(self):
        manager = CloudVMManager()
        assert manager.list_all_instances() == []


class TestAWSProvider:
    def test_init_requires_boto3(self):
        with pytest.raises(RuntimeError, match="boto3"):
            AWSProvider("key", "secret", "us-east-1")


class TestFactoryFunctions:
    def test_create_aws_manager_requires_boto3(self):
        with pytest.raises(RuntimeError, match="boto3"):
            create_aws_manager("key", "secret")

    def test_create_gcp_manager_requires_google(self):
        with pytest.raises(RuntimeError):
            create_gcp_manager("project", "/nonexistent/path.json")


class TestVMConfig:
    def test_minimal(self):
        cfg = VMConfig(name="kali-vm", os_type="kali", vm_path="kali-pentest")
        assert cfg.name == "kali-vm"
        assert cfg.memory_mb == 4096

    def test_custom(self):
        cfg = VMConfig(name="win-vm", os_type="windows", vm_path="win10", memory_mb=8192, cpus=4)
        assert cfg.cpus == 4


class TestVirtualBoxManager:
    def test_init_requires_vbox(self):
        with pytest.raises(RuntimeError, match="VBoxManage"):
            VirtualBoxManager()


class TestPentestSandbox:
    def test_init_delayed_fail(self):
        with pytest.raises(RuntimeError, match="VBoxManage"):
            vm = VirtualBoxManager()
            PentestSandbox(vm)


class TestGetVmManager:
    def test_fails_without_vbox(self):
        with pytest.raises(RuntimeError, match="VBoxManage"):
            get_vm_manager()
