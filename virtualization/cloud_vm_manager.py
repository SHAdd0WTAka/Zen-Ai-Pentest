"""
Cloud VM Manager für Zen-AI-Pentest

Unterstützt AWS EC2, Azure VMs und Google Cloud Compute Engine.
Ermöglicht dynamische Cloud-Pentest-Labs.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

logger = logging.getLogger(__name__)


@dataclass
class CloudVMConfig:
    """Konfiguration für Cloud-VM"""

    provider: Literal["aws", "azure", "gcp"]
    instance_type: str  # z.B. "t3.medium" (AWS), "Standard_B2s" (Azure)
    image_id: str  # AMI (AWS), Image URN (Azure), Image-Familie (GCP)
    region: str
    ssh_key_name: str
    security_group_id: Optional[str] = None
    tags: Dict[str, str] = None

    # Pentest-spezifisch
    auto_shutdown_after_hours: int = 4  # Sicherheit: Auto-Shutdown
    allow_inbound_ports: List[int] = None


class CloudProviderBase(ABC):
    """Abstrakte Basisklasse für Cloud-Provider"""

    @abstractmethod
    def create_instance(self, config: CloudVMConfig, name: str) -> str:
        """Erstellt VM und gibt Instance-ID zurück"""
        pass

    @abstractmethod
    def start_instance(self, instance_id: str) -> bool:
        """Startet VM"""
        pass

    @abstractmethod
    def stop_instance(self, instance_id: str) -> bool:
        """Stoppt VM"""
        pass

    @abstractmethod
    def terminate_instance(self, instance_id: str) -> bool:
        """Löscht VM permanent"""
        pass

    @abstractmethod
    def get_instance_status(self, instance_id: str) -> str:
        """Gibt Status zurück: pending, running, stopped, terminated"""
        pass

    @abstractmethod
    def get_instance_ip(self, instance_id: str) -> Optional[str]:
        """Gibt öffentliche IP zurück"""
        pass

    @abstractmethod
    def list_instances(self) -> List[Dict]:
        """Listet alle VMs auf"""
        pass

    @abstractmethod
    def create_snapshot(self, instance_id: str, name: str) -> str:
        """Erstellt Snapshot/AMI"""
        pass

    @abstractmethod
    def restore_snapshot(self, snapshot_id: str, instance_name: str) -> str:
        """Stellt Snapshot wieder her"""
        pass


class AWSProvider(CloudProviderBase):
    """AWS EC2 Provider"""

    def __init__(
        self, access_key: str, secret_key: str, region: str = "us-east-1"
    ):
        try:
            import boto3

            self.ec2 = boto3.client(
                "ec2",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )
            logger.info("AWS Provider initialisiert")
        except ImportError:
            raise RuntimeError("boto3 nicht installiert: pip install boto3")

    def create_instance(self, config: CloudVMConfig, name: str) -> str:
        """Erstellt EC2 Instance"""

        try:
            # User Data für Setup
            user_data = """#!/bin/bash
apt-get update
apt-get install -y nmap nikto sqlmap gobuster metasploit-framework
apt-get install -y python3-pip wireshark tshark

# Security: Auto-shutdown nach 4 Stunden
(sleep 14400 && shutdown -h now) &

# SSH Key Setup
echo "pentest-user ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
"""

            response = self.ec2.run_instances(
                ImageId=config.image_id,
                InstanceType=config.instance_type,
                MinCount=1,
                MaxCount=1,
                KeyName=config.ssh_key_name,
                SecurityGroupIds=(
                    [config.security_group_id]
                    if config.security_group_id
                    else []
                ),
                UserData=user_data,
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {"Key": "Name", "Value": name},
                            {"Key": "Project", "Value": "zen-ai-pentest"},
                            {
                                "Key": "AutoShutdown",
                                "Value": str(config.auto_shutdown_after_hours),
                            },
                            *[
                                {"Key": k, "Value": v}
                                for k, v in (config.tags or {}).items()
                            ],
                        ],
                    }
                ],
                InstanceInitiatedShutdownBehavior="terminate",  # Auto-cleanup
            )

            instance_id = response["Instances"][0]["InstanceId"]
            logger.info(f"AWS EC2 Instance erstellt: {instance_id}")

            return instance_id

        except Exception as e:
            logger.error(f"AWS Fehler: {e}")
            raise

    def start_instance(self, instance_id: str) -> bool:
        try:
            self.ec2.start_instances(InstanceIds=[instance_id])
            return True
        except Exception as e:
            logger.error(f"Start Fehler: {e}")
            return False

    def stop_instance(self, instance_id: str) -> bool:
        try:
            self.ec2.stop_instances(InstanceIds=[instance_id])
            return True
        except Exception as e:
            logger.error(f"Stop Fehler: {e}")
            return False

    def terminate_instance(self, instance_id: str) -> bool:
        try:
            self.ec2.terminate_instances(InstanceIds=[instance_id])
            return True
        except Exception as e:
            logger.error(f"Terminate Fehler: {e}")
            return False

    def get_instance_status(self, instance_id: str) -> str:
        try:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            state = response["Reservations"][0]["Instances"][0]["State"][
                "Name"
            ]
            return state
        except Exception as e:
            logger.error(f"Status Fehler: {e}")
            return "unknown"

    def get_instance_ip(self, instance_id: str) -> Optional[str]:
        try:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            instance = response["Reservations"][0]["Instances"][0]
            return instance.get("PublicIpAddress")
        except Exception as e:
            logger.error(f"IP Fehler: {e}")
            return None

    def list_instances(self) -> List[Dict]:
        try:
            response = self.ec2.describe_instances(
                Filters=[{"Name": "tag:Project", "Values": ["zen-ai-pentest"]}]
            )

            instances = []
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    instances.append(
                        {
                            "id": instance["InstanceId"],
                            "state": instance["State"]["Name"],
                            "type": instance["InstanceType"],
                            "ip": instance.get("PublicIpAddress"),
                            "name": next(
                                (
                                    t["Value"]
                                    for t in instance.get("Tags", [])
                                    if t["Key"] == "Name"
                                ),
                                "unknown",
                            ),
                        }
                    )
            return instances
        except Exception as e:
            logger.error(f"List Fehler: {e}")
            return []

    def create_snapshot(self, instance_id: str, name: str) -> str:
        """Erstellt AMI Snapshot"""
        try:
            response = self.ec2.create_image(
                InstanceId=instance_id,
                Name=name,
                Description=f"Zen-AI-Pentest Snapshot {name}",
                NoReboot=True,
            )
            return response["ImageId"]
        except Exception as e:
            logger.error(f"Snapshot Fehler: {e}")
            raise

    def restore_snapshot(self, snapshot_id: str, instance_name: str) -> str:
        """Startet Instance von AMI"""
        # In AWS: Neue Instance aus AMI starten
        config = CloudVMConfig(
            provider="aws",
            instance_type="t3.medium",
            image_id=snapshot_id,  # AMI ID
            region="us-east-1",
            ssh_key_name="pentest-key",
        )
        return self.create_instance(config, instance_name)


class AzureProvider(CloudProviderBase):
    """Azure Virtual Machines Provider"""

    def __init__(
        self,
        subscription_id: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
    ):
        try:
            from azure.identity import ClientSecretCredential
            from azure.mgmt.compute import ComputeManagementClient
            from azure.mgmt.network import NetworkManagementClient

            credentials = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            )

            self.compute_client = ComputeManagementClient(
                credentials, subscription_id
            )
            self.network_client = NetworkManagementClient(
                credentials, subscription_id
            )
            self.subscription_id = subscription_id
            self.resource_group = "zen-pentest-rg"  # Default RG

            logger.info("Azure Provider initialisiert")
        except ImportError:
            raise RuntimeError(
                "Azure SDK nicht installiert: pip install azure-mgmt-compute azure-mgmt-network azure-identity"
            )

    def create_instance(self, config: CloudVMConfig, name: str) -> str:
        """Erstellt Azure VM"""
        try:
            from azure.mgmt.compute.models import (
                HardwareProfile,
                NetworkInterfaceReference,
                NetworkProfile,
                OSProfile,
                VirtualMachine,
            )

            # NIC erstellen
            nic = self._create_nic(name, config)

            # VM Konfiguration
            vm_parameters = VirtualMachine(
                location=config.region,
                tags={"Project": "zen-ai-pentest", **(config.tags or {})},
                hardware_profile=HardwareProfile(vm_size=config.instance_type),
                os_profile=OSProfile(
                    computer_name=name,
                    admin_username="pentest",
                    linux_configuration={
                        "disable_password_authentication": True,
                        "ssh": {
                            "public_keys": [
                                {
                                    "path": "/home/pentest/.ssh/authorized_keys",
                                    "key_data": config.ssh_key_name,  # Should be actual key
                                }
                            ]
                        },
                    },
                ),
                network_profile=NetworkProfile(
                    network_interfaces=[NetworkInterfaceReference(id=nic.id)]
                ),
            )

            operation = (
                self.compute_client.virtual_machines.begin_create_or_update(
                    self.resource_group, name, vm_parameters
                )
            )
            vm = operation.result()

            logger.info(f"Azure VM erstellt: {vm.name}")
            return vm.name  # Azure nutzt Namen als ID

        except Exception as e:
            logger.error(f"Azure Fehler: {e}")
            raise

    def _create_nic(self, name: str, config: CloudVMConfig):
        """Erstellt Network Interface"""
        # Simplifiziert - sollte VNet/Subnet prüfen
        pass

    def start_instance(self, instance_id: str) -> bool:
        try:
            self.compute_client.virtual_machines.begin_start(
                self.resource_group, instance_id
            )
            return True
        except Exception as e:
            logger.error(f"Start Fehler: {e}")
            return False

    def stop_instance(self, instance_id: str) -> bool:
        try:
            self.compute_client.virtual_machines.begin_deallocate(
                self.resource_group, instance_id
            )
            return True
        except Exception as e:
            logger.error(f"Stop Fehler: {e}")
            return False

    def terminate_instance(self, instance_id: str) -> bool:
        try:
            self.compute_client.virtual_machines.begin_delete(
                self.resource_group, instance_id
            )
            return True
        except Exception as e:
            logger.error(f"Delete Fehler: {e}")
            return False

    def get_instance_status(self, instance_id: str) -> str:
        try:
            vm = self.compute_client.virtual_machines.instance_view(
                self.resource_group, instance_id
            )
            statuses = [s.display_status for s in vm.statuses]
            return statuses[-1] if statuses else "unknown"
        except Exception as e:
            logger.error(f"Status Fehler: {e}")
            return "unknown"

    def get_instance_ip(self, instance_id: str) -> Optional[str]:
        try:
            _vm = self.compute_client.virtual_machines.get(
                self.resource_group, instance_id
            )
            # IP aus NIC extrahieren
            return "N/A"  # Simplifiziert
        except Exception as e:
            logger.error(f"IP Fehler: {e}")
            return None

    def list_instances(self) -> List[Dict]:
        try:
            vms = self.compute_client.virtual_machines.list(
                self.resource_group
            )
            return [
                {
                    "id": vm.name,
                    "name": vm.name,
                    "state": self.get_instance_status(vm.name),
                    "type": vm.hardware_profile.vm_size,
                }
                for vm in vms
                if vm.tags and vm.tags.get("Project") == "zen-ai-pentest"
            ]
        except Exception as e:
            logger.error(f"List Fehler: {e}")
            return []

    def create_snapshot(self, instance_id: str, name: str) -> str:
        """Erstellt Azure Snapshot"""
        # Implementierung hier
        pass

    def restore_snapshot(self, snapshot_id: str, instance_name: str) -> str:
        """Stellt Snapshot wieder her"""
        pass


class GCPProvider(CloudProviderBase):
    """Google Cloud Platform Provider"""

    def __init__(
        self,
        project_id: str,
        credentials_path: str,
        zone: str = "us-central1-a",
    ):
        try:
            from google.cloud import compute_v1
            from google.oauth2 import service_account

            credentials = (
                service_account.Credentials.from_service_account_file(
                    credentials_path
                )
            )

            self.instances_client = compute_v1.InstancesClient(
                credentials=credentials
            )
            self.project = project_id
            self.zone = zone

            logger.info("GCP Provider initialisiert")
        except ImportError:
            raise RuntimeError(
                "GCP SDK nicht installiert: pip install google-cloud-compute"
            )

    def create_instance(self, config: CloudVMConfig, name: str) -> str:
        """Erstellt GCP Compute Instance"""
        try:
            from google.cloud import compute_v1

            instance = compute_v1.Instance()
            instance.name = name
            instance.machine_type = (
                f"zones/{self.zone}/machineTypes/{config.instance_type}"
            )

            # Boot Disk
            disk = compute_v1.AttachedDisk()
            disk.boot = True
            disk.initialize_params = compute_v1.AttachedDiskInitializeParams(
                source_image=config.image_id
            )
            instance.disks = [disk]

            # Network
            network_interface = compute_v1.NetworkInterface()
            network_interface.name = "global/networks/default"
            instance.network_interfaces = [network_interface]

            # Labels
            instance.labels = {
                "project": "zen-ai-pentest",
                **{
                    k.replace("-", "_"): v
                    for k, v in (config.tags or {}).items()
                },
            }

            operation = self.instances_client.insert(
                project=self.project,
                zone=self.zone,
                instance_resource=instance,
            )
            operation.result()

            logger.info(f"GCP Instance erstellt: {name}")
            return name

        except Exception as e:
            logger.error(f"GCP Fehler: {e}")
            raise

    def start_instance(self, instance_id: str) -> bool:
        try:
            operation = self.instances_client.start(
                project=self.project, zone=self.zone, instance=instance_id
            )
            operation.result()
            return True
        except Exception as e:
            logger.error(f"Start Fehler: {e}")
            return False

    def stop_instance(self, instance_id: str) -> bool:
        try:
            operation = self.instances_client.stop(
                project=self.project, zone=self.zone, instance=instance_id
            )
            operation.result()
            return True
        except Exception as e:
            logger.error(f"Stop Fehler: {e}")
            return False

    def terminate_instance(self, instance_id: str) -> bool:
        try:
            operation = self.instances_client.delete(
                project=self.project, zone=self.zone, instance=instance_id
            )
            operation.result()
            return True
        except Exception as e:
            logger.error(f"Delete Fehler: {e}")
            return False

    def get_instance_status(self, instance_id: str) -> str:
        try:
            instance = self.instances_client.get(
                project=self.project, zone=self.zone, instance=instance_id
            )
            return instance.status.lower()
        except Exception as e:
            logger.error(f"Status Fehler: {e}")
            return "unknown"

    def get_instance_ip(self, instance_id: str) -> Optional[str]:
        try:
            instance = self.instances_client.get(
                project=self.project, zone=self.zone, instance=instance_id
            )
            if instance.network_interfaces:
                access_configs = instance.network_interfaces[0].access_configs
                if access_configs:
                    return access_configs[0].nat_i_p
            return None
        except Exception as e:
            logger.error(f"IP Fehler: {e}")
            return None

    def list_instances(self) -> List[Dict]:
        try:
            instances = self.instances_client.list(
                project=self.project, zone=self.zone
            )
            return [
                {
                    "id": instance.name,
                    "name": instance.name,
                    "state": instance.status.lower(),
                    "type": instance.machine_type.split("/")[-1],
                    "ip": self.get_instance_ip(instance.name),
                }
                for instance in instances
                if instance.labels
                and instance.labels.get("project") == "zen-ai-pentest"
            ]
        except Exception as e:
            logger.error(f"List Fehler: {e}")
            return []

    def create_snapshot(self, instance_id: str, name: str) -> str:
        """Erstellt GCP Disk Snapshot"""
        pass

    def restore_snapshot(self, snapshot_id: str, instance_name: str) -> str:
        pass


class CloudVMManager:
    """
    Unified Manager für alle Cloud-Provider.
    Ermöglicht Multi-Cloud Pentest-Labs.
    """

    def __init__(self):
        self.providers: Dict[str, CloudProviderBase] = {}
        self.active_instances: Dict[str, Dict] = {}

    def add_provider(self, name: str, provider: CloudProviderBase):
        """Fügt Provider hinzu"""
        self.providers[name] = provider
        logger.info(f"Provider hinzugefügt: {name}")

    def create_instance(
        self, provider_name: str, config: CloudVMConfig, name: str
    ) -> str:
        """Erstellt VM beim angegebenen Provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} nicht konfiguriert")

        provider = self.providers[provider_name]
        instance_id = provider.create_instance(config, name)

        # Tracken
        self.active_instances[instance_id] = {
            "provider": provider_name,
            "config": config,
            "name": name,
            "created_at": time.time(),
        }

        return instance_id

    def get_provider_for_instance(self, instance_id: str) -> CloudProviderBase:
        """Gibt Provider für Instance zurück"""
        if instance_id not in self.active_instances:
            raise ValueError(f"Instance {instance_id} nicht gefunden")

        provider_name = self.active_instances[instance_id]["provider"]
        return self.providers[provider_name]

    def start_instance(self, instance_id: str) -> bool:
        provider = self.get_provider_for_instance(instance_id)
        return provider.start_instance(instance_id)

    def stop_instance(self, instance_id: str) -> bool:
        provider = self.get_provider_for_instance(instance_id)
        return provider.stop_instance(instance_id)

    def terminate_instance(self, instance_id: str) -> bool:
        provider = self.get_provider_for_instance(instance_id)
        success = provider.terminate_instance(instance_id)

        if success and instance_id in self.active_instances:
            del self.active_instances[instance_id]

        return success

    def get_instance_status(self, instance_id: str) -> str:
        provider = self.get_provider_for_instance(instance_id)
        return provider.get_instance_status(instance_id)

    def get_instance_ip(self, instance_id: str) -> Optional[str]:
        provider = self.get_provider_for_instance(instance_id)
        return provider.get_instance_ip(instance_id)

    def list_all_instances(self) -> List[Dict]:
        """Listet VMs von allen Providern"""
        all_instances = []

        for name, provider in self.providers.items():
            instances = provider.list_instances()
            for inst in instances:
                inst["provider"] = name
            all_instances.extend(instances)

        return all_instances

    def execute_ssh_command(
        self,
        instance_id: str,
        command: str,
        ssh_key_path: str,
        username: str = "ubuntu",
    ) -> tuple:
        """Führt SSH-Befehl auf VM aus"""
        import paramiko

        ip = self.get_instance_ip(instance_id)
        if not ip:
            return -1, "", "Keine IP verfügbar"

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username=username, key_filename=ssh_key_path)

            stdin, stdout, stderr = client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()

            return exit_code, stdout.read().decode(), stderr.read().decode()
        except Exception as e:
            return -1, "", str(e)
        finally:
            client.close()

    def auto_cleanup(self, max_age_hours: int = 4):
        """Terminiert alte Instanzen (Sicherheit)"""
        current_time = time.time()

        for instance_id, info in list(self.active_instances.items()):
            age_hours = (current_time - info["created_at"]) / 3600

            if age_hours > max_age_hours:
                logger.warning(
                    f"Auto-cleanup: Terminiere {instance_id} (Alter: {age_hours:.1f}h)"
                )
                self.terminate_instance(instance_id)

    def create_kali_instance(
        self, provider_name: str, region: str, name: str = "zen-kali-pentest"
    ) -> str:
        """Erstellt vorkonfigurierte Kali Linux VM"""

        # Provider-spezifische Kali Images
        kali_images = {
            "aws": "ami-0c7ecac5f6e6f09d8",  # Kali Linux 2024.x
            "azure": "kali-linux:kali:kali-2024:latest",
            "gcp": "projects/kali-linux-cloud/global/images/family/kali-linux-2024",
        }

        instance_types = {
            "aws": "t3.medium",
            "azure": "Standard_B2s",
            "gcp": "e2-medium",
        }

        config = CloudVMConfig(
            provider=provider_name,
            instance_type=instance_types.get(provider_name, "t3.medium"),
            image_id=kali_images.get(provider_name, "ami-0c7ecac5f6e6f09d8"),
            region=region,
            ssh_key_name="zen-pentest-key",
            auto_shutdown_after_hours=4,
            tags={"OS": "Kali", "Purpose": "Pentesting"},
        )

        return self.create_instance(provider_name, config, name)


# Factory-Methoden
def create_aws_manager(
    access_key: str, secret_key: str, region: str = "us-east-1"
) -> CloudVMManager:
    """Erstellt Manager mit AWS Provider"""
    manager = CloudVMManager()
    manager.add_provider("aws", AWSProvider(access_key, secret_key, region))
    return manager


def create_azure_manager(
    subscription_id: str, tenant_id: str, client_id: str, client_secret: str
) -> CloudVMManager:
    """Erstellt Manager mit Azure Provider"""
    manager = CloudVMManager()
    manager.add_provider(
        "azure",
        AzureProvider(subscription_id, tenant_id, client_id, client_secret),
    )
    return manager


def create_gcp_manager(
    project_id: str, credentials_path: str, zone: str = "us-central1-a"
) -> CloudVMManager:
    """Erstellt Manager mit GCP Provider"""
    manager = CloudVMManager()
    manager.add_provider(
        "gcp", GCPProvider(project_id, credentials_path, zone)
    )
    return manager


if __name__ == "__main__":
    # Test-Code
    logging.basicConfig(level=logging.INFO)

    print("CloudVMManager initialisiert")
    print("Verfügbare Provider: AWS, Azure, GCP")
    print("\nBeispiel:")
    print("  manager = create_aws_manager('AKIA...', 'secret...')")
    print("  instance_id = manager.create_kali_instance('aws', 'us-east-1')")
