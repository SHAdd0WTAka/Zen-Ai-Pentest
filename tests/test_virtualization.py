"""
Tests for Virtualization Module

Covers:
- CloudVMManager
- VMManager (VirtualBox)
- Cloud providers (AWS, Azure, GCP)
"""

import subprocess
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest

# Import virtualization modules
from virtualization.cloud_vm_manager import (
    AWSProvider,
    AzureProvider,
    CloudProviderBase,
    CloudVMConfig,
    CloudVMManager,
    GCPProvider,
    create_aws_manager,
    create_azure_manager,
    create_gcp_manager,
)
from virtualization.vm_manager import PentestSandbox, VirtualBoxManager, VMConfig

# ============================================================================
# CloudVMConfig Tests
# ============================================================================


class TestCloudVMConfig:
    """Test CloudVMConfig dataclass"""

    def test_config_creation(self):
        """Test CloudVMConfig creation"""
        config = CloudVMConfig(
            provider="aws", instance_type="t3.medium", image_id="ami-12345", region="us-east-1", ssh_key_name="test-key"
        )

        assert config.provider == "aws"
        assert config.instance_type == "t3.medium"
        assert config.image_id == "ami-12345"
        assert config.region == "us-east-1"
        assert config.ssh_key_name == "test-key"
        assert config.auto_shutdown_after_hours == 4  # default

    def test_config_with_pentest_options(self):
        """Test CloudVMConfig with pentest-specific options"""
        config = CloudVMConfig(
            provider="aws",
            instance_type="t3.large",
            image_id="ami-kali",
            region="eu-west-1",
            ssh_key_name="pentest-key",
            auto_shutdown_after_hours=8,
            allow_inbound_ports=[22, 80, 443],
            tags={"Purpose": "Pentest", "Team": "Red"},
        )

        assert config.auto_shutdown_after_hours == 8
        assert config.allow_inbound_ports == [22, 80, 443]
        assert config.tags == {"Purpose": "Pentest", "Team": "Red"}


# ============================================================================
# CloudVMManager Tests
# ============================================================================


class TestCloudVMManager:
    """Test CloudVMManager class"""

    @pytest.fixture
    def manager(self):
        """Create a CloudVMManager instance"""
        return CloudVMManager()

    @pytest.fixture
    def mock_provider(self):
        """Create a mock cloud provider"""
        provider = Mock(spec=CloudProviderBase)
        provider.create_instance.return_value = "i-12345"
        provider.start_instance.return_value = True
        provider.stop_instance.return_value = True
        provider.terminate_instance.return_value = True
        provider.get_instance_status.return_value = "running"
        provider.get_instance_ip.return_value = "10.0.0.1"
        provider.list_instances.return_value = [{"id": "i-12345", "name": "test-vm", "state": "running"}]
        return provider

    def test_initialization(self, manager):
        """Test CloudVMManager initialization"""
        assert manager.providers == {}
        assert manager.active_instances == {}

    def test_add_provider(self, manager, mock_provider):
        """Test adding a provider"""
        manager.add_provider("aws", mock_provider)

        assert "aws" in manager.providers
        assert manager.providers["aws"] is mock_provider

    def test_create_instance(self, manager, mock_provider):
        """Test creating an instance"""
        manager.add_provider("aws", mock_provider)

        config = CloudVMConfig(
            provider="aws", instance_type="t3.medium", image_id="ami-12345", region="us-east-1", ssh_key_name="test-key"
        )

        instance_id = manager.create_instance("aws", config, "test-vm")

        assert instance_id == "i-12345"
        assert instance_id in manager.active_instances
        mock_provider.create_instance.assert_called_once_with(config, "test-vm")

    def test_create_instance_unknown_provider(self, manager):
        """Test creating instance with unknown provider"""
        config = CloudVMConfig(
            provider="unknown", instance_type="t3.medium", image_id="ami-12345", region="us-east-1", ssh_key_name="test-key"
        )

        with pytest.raises(ValueError, match="Provider unknown nicht konfiguriert"):
            manager.create_instance("unknown", config, "test-vm")

    def test_get_provider_for_instance(self, manager, mock_provider):
        """Test getting provider for an instance"""
        manager.add_provider("aws", mock_provider)

        config = CloudVMConfig(
            provider="aws", instance_type="t3.medium", image_id="ami-12345", region="us-east-1", ssh_key_name="test-key"
        )

        instance_id = manager.create_instance("aws", config, "test-vm")
        provider = manager.get_provider_for_instance(instance_id)

        assert provider is mock_provider

    def test_get_provider_for_unknown_instance(self, manager):
        """Test getting provider for unknown instance"""
        with pytest.raises(ValueError, match="Instance unknown nicht gefunden"):
            manager.get_provider_for_instance("unknown")

    def test_start_instance(self, manager, mock_provider):
        """Test starting an instance"""
        manager.add_provider("aws", mock_provider)
        config = CloudVMConfig(
            provider="aws", instance_type="t3.medium", image_id="ami-12345", region="us-east-1", ssh_key_name="test-key"
        )
        instance_id = manager.create_instance("aws", config, "test-vm")

        result = manager.start_instance(instance_id)

        assert result is True
        mock_provider.start_instance.assert_called_once_with(instance_id)

    def test_stop_instance(self, manager, mock_provider):
        """Test stopping an instance"""
        manager.add_provider("aws", mock_provider)
        config = CloudVMConfig(
            provider="aws", instance_type="t3.medium", image_id="ami-12345", region="us-east-1", ssh_key_name="test-key"
        )
        instance_id = manager.create_instance("aws", config, "test-vm")

        result = manager.stop_instance(instance_id)

        assert result is True
        mock_provider.stop_instance.assert_called_once_with(instance_id)

    def test_terminate_instance(self, manager, mock_provider):
        """Test terminating an instance"""
        manager.add_provider("aws", mock_provider)
        config = CloudVMConfig(
            provider="aws", instance_type="t3.medium", image_id="ami-12345", region="us-east-1", ssh_key_name="test-key"
        )
        instance_id = manager.create_instance("aws", config, "test-vm")

        result = manager.terminate_instance(instance_id)

        assert result is True
        assert instance_id not in manager.active_instances
        mock_provider.terminate_instance.assert_called_once_with(instance_id)

    def test_get_instance_status(self, manager, mock_provider):
        """Test getting instance status"""
        manager.add_provider("aws", mock_provider)
        config = CloudVMConfig(
            provider="aws", instance_type="t3.medium", image_id="ami-12345", region="us-east-1", ssh_key_name="test-key"
        )
        instance_id = manager.create_instance("aws", config, "test-vm")

        status = manager.get_instance_status(instance_id)

        assert status == "running"
        mock_provider.get_instance_status.assert_called_once_with(instance_id)

    def test_get_instance_ip(self, manager, mock_provider):
        """Test getting instance IP"""
        manager.add_provider("aws", mock_provider)
        config = CloudVMConfig(
            provider="aws", instance_type="t3.medium", image_id="ami-12345", region="us-east-1", ssh_key_name="test-key"
        )
        instance_id = manager.create_instance("aws", config, "test-vm")

        ip = manager.get_instance_ip(instance_id)

        assert ip == "10.0.0.1"
        mock_provider.get_instance_ip.assert_called_once_with(instance_id)

    def test_list_all_instances(self, manager, mock_provider):
        """Test listing all instances across providers"""
        manager.add_provider("aws", mock_provider)

        instances = manager.list_all_instances()

        assert len(instances) == 1
        assert instances[0]["provider"] == "aws"

    def test_execute_ssh_command(self, manager, mock_provider):
        """Test executing SSH command on instance - requires paramiko"""
        # Check if paramiko is available
        try:
            import paramiko
        except ImportError:
            pytest.skip("paramiko not installed")

        # Mock paramiko at module level where it's imported
        with patch.dict("sys.modules", {"paramiko": MagicMock()}):
            with patch("virtualization.cloud_vm_manager.paramiko") as mock_paramiko:
                # Setup mock SSH client
                mock_ssh = Mock()
                mock_paramiko.SSHClient.return_value = mock_ssh
                mock_paramiko.AutoAddPolicy.return_value = Mock()
                mock_stdin = Mock()
                mock_stdout = Mock()
                mock_stderr = Mock()
                mock_stdout.read.return_value = b"command output"
                mock_stderr.read.return_value = b""
                mock_stdout.channel.recv_exit_status.return_value = 0
                mock_ssh.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

                manager.add_provider("aws", mock_provider)
                config = CloudVMConfig(
                    provider="aws",
                    instance_type="t3.medium",
                    image_id="ami-12345",
                    region="us-east-1",
                    ssh_key_name="test-key",
                )
                instance_id = manager.create_instance("aws", config, "test-vm")

                exit_code, stdout, stderr = manager.execute_ssh_command(instance_id, "ls -la", "/path/to/key", "ubuntu")

                assert exit_code == 0
                assert stdout == "command output"

    def test_execute_ssh_command_no_ip(self, manager, mock_provider):
        """Test SSH command when instance has no IP"""
        # Skip if paramiko not installed
        try:
            import paramiko
        except ImportError:
            pytest.skip("paramiko not installed")

        mock_provider.get_instance_ip.return_value = None

        manager.add_provider("aws", mock_provider)
        config = CloudVMConfig(
            provider="aws", instance_type="t3.medium", image_id="ami-12345", region="us-east-1", ssh_key_name="test-key"
        )
        instance_id = manager.create_instance("aws", config, "test-vm")

        exit_code, stdout, stderr = manager.execute_ssh_command(instance_id, "ls -la", "/path/to/key")

        assert exit_code == -1
        assert "Keine IP" in stderr

    def test_auto_cleanup(self, manager, mock_provider):
        """Test automatic cleanup of old instances"""
        manager.add_provider("aws", mock_provider)
        config = CloudVMConfig(
            provider="aws", instance_type="t3.medium", image_id="ami-12345", region="us-east-1", ssh_key_name="test-key"
        )
        instance_id = manager.create_instance("aws", config, "test-vm")

        # Simulate old instance
        manager.active_instances[instance_id]["created_at"] = time.time() - 3600 * 5  # 5 hours ago

        manager.auto_cleanup(max_age_hours=4)

        mock_provider.terminate_instance.assert_called_once_with(instance_id)
        assert instance_id not in manager.active_instances

    def test_create_kali_instance_aws(self, manager, mock_provider):
        """Test creating Kali instance on AWS"""
        manager.add_provider("aws", mock_provider)

        instance_id = manager.create_kali_instance("aws", "us-east-1", "test-kali")

        assert instance_id == "i-12345"
        mock_provider.create_instance.assert_called_once()
        call_args = mock_provider.create_instance.call_args
        config = call_args[0][0]
        assert config.image_id == "ami-0c7ecac5f6e6f09d8"  # Kali AMI


# ============================================================================
# Factory Functions Tests
# ============================================================================


class TestFactoryFunctions:
    """Test factory functions for creating managers"""

    @patch("virtualization.cloud_vm_manager.AWSProvider")
    def test_create_aws_manager(self, mock_aws_class):
        """Test creating AWS manager"""
        mock_aws_instance = Mock(spec=CloudProviderBase)
        mock_aws_class.return_value = mock_aws_instance

        manager = create_aws_manager("AKIA...", "secret...", "us-east-1")

        assert isinstance(manager, CloudVMManager)
        mock_aws_class.assert_called_once_with("AKIA...", "secret...", "us-east-1")

    @patch("virtualization.cloud_vm_manager.AzureProvider")
    def test_create_azure_manager(self, mock_azure_class):
        """Test creating Azure manager"""
        mock_azure_instance = Mock(spec=CloudProviderBase)
        mock_azure_class.return_value = mock_azure_instance

        manager = create_azure_manager("sub-id", "tenant-id", "client-id", "client-secret")

        assert isinstance(manager, CloudVMManager)
        mock_azure_class.assert_called_once_with("sub-id", "tenant-id", "client-id", "client-secret")

    @patch("virtualization.cloud_vm_manager.GCPProvider")
    def test_create_gcp_manager(self, mock_gcp_class):
        """Test creating GCP manager"""
        mock_gcp_instance = Mock(spec=CloudProviderBase)
        mock_gcp_class.return_value = mock_gcp_instance

        manager = create_gcp_manager("project-id", "/path/to/creds.json", "us-central1-a")

        assert isinstance(manager, CloudVMManager)
        mock_gcp_class.assert_called_once_with("project-id", "/path/to/creds.json", "us-central1-a")


# ============================================================================
# VirtualBoxManager Tests
# ============================================================================


class TestVirtualBoxManager:
    """Test VirtualBoxManager class"""

    @pytest.fixture
    def mock_vboxmanage(self):
        """Mock VBoxManage command"""
        with patch("subprocess.run") as mock_run:
            # First call returns version (initialization)
            # Subsequent calls return command results
            mock_run.return_value = Mock(returncode=0, stdout='"TestVM" {12345678-1234-1234-1234-123456789012}\n', stderr="")
            yield mock_run

    @pytest.fixture
    def vbox_manager(self, mock_vboxmanage):
        """Create VirtualBoxManager with mocked VBoxManage"""
        return VirtualBoxManager()

    def test_initialization_finds_vboxmanage(self, mock_vboxmanage):
        """Test initialization finds VBoxManage"""
        manager = VirtualBoxManager()

        assert manager.vbox_manage is not None

    def test_initialization_not_found(self):
        """Test initialization when VBoxManage not found"""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(RuntimeError, match="VBoxManage nicht gefunden"):
                VirtualBoxManager()

    def test_list_vms(self, vbox_manager, mock_vboxmanage):
        """Test listing VMs"""
        vms = vbox_manager.list_vms()

        assert len(vms) == 1
        assert vms[0]["name"] == "TestVM"
        assert vms[0]["uuid"] == "12345678-1234-1234-1234-123456789012"

    def test_list_running_vms(self, vbox_manager, mock_vboxmanage):
        """Test listing running VMs"""
        vbox_manager.list_vms(running_only=True)

        # Verify "runningvms" was passed
        call_args = mock_vboxmanage.call_args
        assert "runningvms" in call_args[0][0]

    def test_vm_exists_true(self, vbox_manager, mock_vboxmanage):
        """Test vm_exists when VM exists"""
        exists = vbox_manager.vm_exists("TestVM")

        assert exists is True

    def test_vm_exists_false(self, vbox_manager, mock_vboxmanage):
        """Test vm_exists when VM doesn't exist"""
        exists = vbox_manager.vm_exists("NonExistentVM")

        assert exists is False

    def test_is_running_true(self, vbox_manager, mock_vboxmanage):
        """Test is_running when VM is running"""
        mock_vboxmanage.return_value = Mock(
            returncode=0, stdout='"TestVM" {12345678-1234-1234-1234-123456789012}\n', stderr=""
        )

        running = vbox_manager.is_running("TestVM")

        assert running is True

    def test_is_running_false(self, vbox_manager, mock_vboxmanage):
        """Test is_running when VM is not running"""
        mock_vboxmanage.return_value = Mock(returncode=0, stdout="", stderr="")

        running = vbox_manager.is_running("TestVM")

        assert running is False

    def test_start_vm_success(self, vbox_manager, mock_vboxmanage):
        """Test starting VM successfully"""
        # Mock vm_exists to return True
        vbox_manager.vm_exists = Mock(return_value=True)
        vbox_manager.is_running = Mock(return_value=False)
        mock_vboxmanage.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch("time.sleep"):  # Skip actual sleep
            result = vbox_manager.start_vm("TestVM", headless=True)

        assert result is True
        call_args = mock_vboxmanage.call_args[0][0]
        assert "startvm" in call_args
        assert "headless" in call_args

    def test_start_vm_already_running(self, vbox_manager, mock_vboxmanage):
        """Test starting VM that's already running"""
        vbox_manager.is_running = Mock(return_value=True)

        # Reset mock to ignore initialization calls
        mock_vboxmanage.reset_mock()

        result = vbox_manager.start_vm("TestVM")

        assert result is True
        # Should not call VBoxManage for startvm (just for version check in init)
        startvm_calls = [call for call in mock_vboxmanage.call_args_list if "startvm" in str(call)]
        assert len(startvm_calls) == 0

    def test_stop_vm_success(self, vbox_manager, mock_vboxmanage):
        """Test stopping VM successfully"""
        vbox_manager.is_running = Mock(return_value=True)
        mock_vboxmanage.return_value = Mock(returncode=0, stdout="", stderr="")

        result = vbox_manager.stop_vm("TestVM")

        assert result is True
        call_args = mock_vboxmanage.call_args[0][0]
        assert "controlvm" in call_args
        assert "acpipowerbutton" in call_args

    def test_stop_vm_force(self, vbox_manager, mock_vboxmanage):
        """Test force stopping VM"""
        vbox_manager.is_running = Mock(return_value=True)
        mock_vboxmanage.return_value = Mock(returncode=0, stdout="", stderr="")

        result = vbox_manager.stop_vm("TestVM", force=True)

        assert result is True
        call_args = mock_vboxmanage.call_args[0][0]
        assert "poweroff" in call_args

    def test_stop_vm_not_running(self, vbox_manager, mock_vboxmanage):
        """Test stopping VM that's not running"""
        vbox_manager.is_running = Mock(return_value=False)

        result = vbox_manager.stop_vm("TestVM")

        assert result is True

    def test_reset_vm(self, vbox_manager, mock_vboxmanage):
        """Test resetting VM"""
        mock_vboxmanage.return_value = Mock(returncode=0, stdout="", stderr="")

        result = vbox_manager.reset_vm("TestVM")

        assert result is True
        call_args = mock_vboxmanage.call_args[0][0]
        assert "reset" in call_args

    def test_create_snapshot(self, vbox_manager, mock_vboxmanage):
        """Test creating snapshot"""
        mock_vboxmanage.return_value = Mock(returncode=0, stdout="", stderr="")

        result = vbox_manager.create_snapshot("TestVM", "clean_state", "Clean state")

        assert result is True
        call_args = mock_vboxmanage.call_args[0][0]
        assert "snapshot" in call_args
        assert "take" in call_args
        assert "clean_state" in call_args

    def test_restore_snapshot(self, vbox_manager, mock_vboxmanage):
        """Test restoring snapshot"""
        vbox_manager.is_running = Mock(return_value=False)
        mock_vboxmanage.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch("time.sleep"):
            result = vbox_manager.restore_snapshot("TestVM", "clean_state")

        assert result is True
        call_args = mock_vboxmanage.call_args[0][0]
        assert "snapshot" in call_args
        assert "restore" in call_args

    def test_list_snapshots(self, vbox_manager, mock_vboxmanage):
        """Test listing snapshots"""
        mock_vboxmanage.return_value = Mock(
            returncode=0, stdout='CurrentSnapshotUUID="abc123"\nSnapshotName="clean_state"', stderr=""
        )

        snapshots = vbox_manager.list_snapshots("TestVM")

        assert len(snapshots) == 1
        assert snapshots[0]["name"] == "clean_state"

    def test_configure_network(self, vbox_manager, mock_vboxmanage):
        """Test configuring network"""
        mock_vboxmanage.return_value = Mock(returncode=0, stdout="", stderr="")

        result = vbox_manager.configure_network("TestVM", mode="bridged", adapter=1)

        assert result is True
        call_args = mock_vboxmanage.call_args[0][0]
        assert "modifyvm" in call_args
        assert "--nic1" in call_args
        assert "bridged" in call_args

    def test_get_vm_info(self, vbox_manager, mock_vboxmanage):
        """Test getting VM info"""
        mock_vboxmanage.return_value = Mock(returncode=0, stdout='name="TestVM"\nmemory="4096"', stderr="")

        info = vbox_manager.get_vm_info("TestVM")

        assert "name" in info
        assert info["name"] == "TestVM"
        assert "memory" in info

    def test_clone_vm(self, vbox_manager, mock_vboxmanage):
        """Test cloning VM"""
        mock_vboxmanage.return_value = Mock(returncode=0, stdout="", stderr="")

        result = vbox_manager.clone_vm("SourceVM", "NewVM", linked=True)

        assert result is True
        call_args = mock_vboxmanage.call_args[0][0]
        assert "clonevm" in call_args
        assert "NewVM" in call_args

    def test_delete_vm(self, vbox_manager, mock_vboxmanage):
        """Test deleting VM"""
        vbox_manager.is_running = Mock(return_value=False)
        mock_vboxmanage.return_value = Mock(returncode=0, stdout="", stderr="")

        result = vbox_manager.delete_vm("TestVM", delete_files=True)

        assert result is True
        call_args = mock_vboxmanage.call_args[0][0]
        assert "unregistervm" in call_args
        assert "--delete" in call_args


# ============================================================================
# PentestSandbox Tests
# ============================================================================


class TestPentestSandbox:
    """Test PentestSandbox class"""

    @pytest.fixture
    def mock_vbox(self):
        """Create a mock VirtualBoxManager"""
        vbox = Mock(spec=VirtualBoxManager)
        vbox.vm_exists.return_value = True
        vbox.restore_snapshot.return_value = True
        vbox.start_vm.return_value = True
        vbox.create_snapshot.return_value = True
        vbox.stop_vm.return_value = True
        return vbox

    @pytest.fixture
    def sandbox(self, mock_vbox):
        """Create a PentestSandbox instance"""
        return PentestSandbox(mock_vbox)

    def test_initialization(self, mock_vbox):
        """Test PentestSandbox initialization"""
        sandbox = PentestSandbox(mock_vbox)

        assert sandbox.vm is mock_vbox
        assert sandbox.active_sessions == {}

    def test_create_session_success(self, sandbox, mock_vbox):
        """Test creating a session successfully"""
        result = sandbox.create_session("session-123", "kali-pentest")

        assert result is True
        assert "session-123" in sandbox.active_sessions
        mock_vbox.restore_snapshot.assert_called_once_with("kali-pentest", "clean_state")
        mock_vbox.start_vm.assert_called_once_with("kali-pentest", headless=False)

    def test_create_session_vm_not_found(self, sandbox, mock_vbox):
        """Test creating session when VM not found"""
        mock_vbox.vm_exists.return_value = False

        result = sandbox.create_session("session-123", "nonexistent-vm")

        assert result is False
        assert "session-123" not in sandbox.active_sessions

    def test_create_session_restore_fails(self, sandbox, mock_vbox):
        """Test creating session when snapshot restore fails"""
        mock_vbox.restore_snapshot.return_value = False

        result = sandbox.create_session("session-123", "kali-pentest")

        assert result is True  # Still creates session, just warns
        mock_vbox.create_snapshot.assert_called_once()

    def test_execute_tool(self, sandbox, mock_vbox):
        """Test executing tool in session"""
        sandbox.create_session("session-123", "kali-pentest")
        mock_vbox.execute_in_vm.return_value = (0, "nmap output", "")

        exit_code, stdout, stderr = sandbox.execute_tool("session-123", "nmap", "-sV 192.168.1.1")

        assert exit_code == 0
        assert stdout == "nmap output"
        mock_vbox.execute_in_vm.assert_called_once()

    def test_execute_tool_invalid_session(self, sandbox):
        """Test executing tool with invalid session"""
        exit_code, stdout, stderr = sandbox.execute_tool("invalid-session", "nmap", "-sV 192.168.1.1")

        assert exit_code == -1
        assert "Session nicht gefunden" in stderr

    def test_execute_tool_nmap(self, sandbox, mock_vbox):
        """Test executing nmap tool"""
        sandbox.create_session("session-123", "kali-pentest")
        mock_vbox.execute_in_vm.return_value = (0, "", "")

        sandbox.execute_tool("session-123", "nmap", "-sS 192.168.1.1")

        call_args = mock_vbox.execute_in_vm.call_args
        assert "nmap -sS 192.168.1.1" in call_args[0][1]

    def test_execute_tool_metasploit(self, sandbox, mock_vbox):
        """Test executing metasploit tool"""
        sandbox.create_session("session-123", "kali-pentest")
        mock_vbox.execute_in_vm.return_value = (0, "", "")

        sandbox.execute_tool("session-123", "metasploit", "use exploit/test")

        call_args = mock_vbox.execute_in_vm.call_args
        assert "msfconsole" in call_args[0][1]

    def test_end_session(self, sandbox, mock_vbox):
        """Test ending a session"""
        sandbox.create_session("session-123", "kali-pentest")

        result = sandbox.end_session("session-123")

        assert result is True
        assert "session-123" not in sandbox.active_sessions
        mock_vbox.stop_vm.assert_called_once_with("kali-pentest")

    def test_end_session_with_snapshot(self, sandbox, mock_vbox):
        """Test ending a session and saving snapshot"""
        sandbox.create_session("session-123", "kali-pentest")

        result = sandbox.end_session("session-123", save_snapshot=True)

        assert result is True
        mock_vbox.create_snapshot.assert_called_with("kali-pentest", "session_session-123_ended")

    def test_end_session_invalid(self, sandbox):
        """Test ending an invalid session"""
        result = sandbox.end_session("invalid-session")

        assert result is False


# ============================================================================
# VMConfig Tests
# ============================================================================


class TestVMConfig:
    """Test VMConfig dataclass"""

    def test_config_creation(self):
        """Test VMConfig creation"""
        config = VMConfig(name="kali-pentest", os_type="kali", vm_path="/path/to/vm.vbox")

        assert config.name == "kali-pentest"
        assert config.os_type == "kali"
        assert config.vm_path == "/path/to/vm.vbox"
        assert config.snapshot_name == "clean_state"  # default
        assert config.network_mode == "nat"  # default
        assert config.memory_mb == 4096  # default
        assert config.cpus == 2  # default

    def test_config_custom(self):
        """Test VMConfig with custom values"""
        config = VMConfig(
            name="windows-target",
            os_type="windows",
            vm_path="C:\\VMs\\windows.vbox",
            snapshot_name="base",
            network_mode="bridged",
            memory_mb=8192,
            cpus=4,
        )

        assert config.snapshot_name == "base"
        assert config.network_mode == "bridged"
        assert config.memory_mb == 8192
        assert config.cpus == 4
