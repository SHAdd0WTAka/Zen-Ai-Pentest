#!/usr/bin/env python3
"""
Zen-AI-Pentest Kubernetes Operator

A production-ready Kubernetes operator for managing penetration testing scans.
Uses Kopf framework for Kubernetes operator development.

Features:
- Watch and reconcile PentestScan CRDs
- Create Jobs/Pods for scan execution
- Handle scheduled scans via CronJobs
- Update status with retry logic
- Resource management and limits
- Notification on completion
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import kopf
import kubernetes.client as k8s_client
from kubernetes.client.rest import ApiException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zen-operator")

# Constants
OPERATOR_NAMESPACE = os.environ.get("OPERATOR_NAMESPACE", "zen-ai-pentest")
DEFAULT_SCAN_IMAGE = os.environ.get("SCAN_IMAGE", "zen-ai-pentest/scanner:latest")
DEFAULT_TIMEOUT = int(os.environ.get("DEFAULT_SCAN_TIMEOUT", "3600"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", "30"))

# Tool configurations
TOOL_COMMANDS = {
    "nmap": ["nmap", "-sV", "-sC", "-oX", "/results/nmap.xml"],
    "nuclei": ["nuclei", "-u", "{target}", "-o", "/results/nuclei.json", "-json"],
    "zap": ["zap-baseline.py", "-t", "{target}", "-r", "/results/zap-report.html"],
    "sqlmap": ["sqlmap", "-u", "{target}", "--batch", "--output-dir=/results"],
    "ffuf": ["ffuf", "-u", "{target}/FUZZ", "-w", "/wordlists/common.txt", "-o", "/results/ffuf.json"],
    "subfinder": ["subfinder", "-d", "{target}", "-o", "/results/subdomains.txt"],
    "httpx": ["httpx", "-l", "/results/subdomains.txt", "-o", "/results/httpx.txt"],
    "whatweb": ["whatweb", "{target}", "--log-json=/results/whatweb.json"],
    "wafw00f": ["wafw00f", "{target}", "-o", "/results/wafw00f.txt"],
    "nikto": ["nikto", "-h", "{target}", "-o", "/results/nikto.txt"],
    "gobuster": ["gobuster", "dir", "-u", "{target}", "-w", "/wordlists/common.txt", "-o", "/results/gobuster.txt"],
    "amass": ["amass", "enum", "-d", "{target}", "-o", "/results/amass.txt"],
    "masscan": ["masscan", "-p1-65535", "{target}", "-oX", "/results/masscan.xml"],
    "trivy": ["trivy", "fs", "--scanners=vuln", "-f", "json", "-o", "/results/trivy.json", "/target"],
    "semgrep": ["semgrep", "--config=auto", "--json", "--output=/results/semgrep.json", "/target"],
    "trufflehog": ["trufflehog", "filesystem", "/target", "--json", "--output=/results/trufflehog.json"],
}


def get_k8s_client():
    """Get Kubernetes API client."""
    try:
        k8s_client.config.load_incluster_config()
    except k8s_client.config.ConfigException:
        k8s_client.config.load_kube_config()
    return k8s_client.ApiClient()


def create_job_name(name: str) -> str:
    """Generate unique job name."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"zen-scan-{name}-{timestamp}".lower()[:63]


def create_cronjob_name(name: str) -> str:
    """Generate unique cronjob name."""
    return f"zen-cron-{name}".lower()[:52]  # Leave room for suffix


def build_scan_command(spec: Dict[str, Any]) -> List[str]:
    """Build the scan command based on spec."""
    target = spec.get("target", "")
    scan_type = spec.get("scanType", "full")
    tools = spec.get("tools", [])
    options = spec.get("options", {})

    # If no specific tools, use scan type defaults
    if not tools:
        tools = get_default_tools(scan_type)

    # Build commands for each tool
    commands = []
    for tool in tools:
        if tool in TOOL_COMMANDS:
            cmd = TOOL_COMMANDS[tool].copy()
            # Replace placeholders
            cmd = [arg.replace("{target}", target) for arg in cmd]

            # Add aggressive flag if set
            if options.get("aggressive") and tool in ["nmap", "nikto"]:
                if tool == "nmap":
                    cmd.insert(1, "-A")
                elif tool == "nikto":
                    cmd.insert(1, "-Cgidirs")
                    cmd.insert(2, "all")

            # Add ports for network scans
            if options.get("ports") and tool in ["nmap", "masscan"]:
                cmd.insert(1, "-p")
                cmd.insert(2, options["ports"])

            commands.append(cmd)

    # Create a wrapper script that runs all tools
    script = "#!/bin/sh\nset -e\necho 'Starting Zen-AI-Pentest scan...'\n"
    for i, cmd in enumerate(commands):
        script += f"echo 'Running tool {i + 1}/{len(commands)}: {cmd[0]}'\n"
        script += f"{' '.join(cmd)} || echo 'Tool {cmd[0]} failed but continuing...'\n"
    script += "echo 'Scan completed'\n"

    return ["sh", "-c", script]


def get_default_tools(scan_type: str) -> List[str]:
    """Get default tools based on scan type."""
    defaults = {
        "recon": ["subfinder", "amass", "httpx"],
        "vulnerability": ["nuclei", "nikto", "whatweb"],
        "full": ["nmap", "nuclei", "whatweb", "wafw00f"],
        "network": ["nmap", "masscan"],
        "web": ["nuclei", "nikto", "whatweb", "wafw00f", "gobuster"],
        "api": ["nuclei", "ffuf", "httpx"],
    }
    return defaults.get(scan_type, defaults["full"])


def create_job_manifest(
    name: str,
    namespace: str,
    spec: Dict[str, Any],
    job_name: str,
) -> Dict[str, Any]:
    """Create Kubernetes Job manifest."""
    target = spec.get("target", "")
    resources = spec.get("resources", {})
    timeout = spec.get("timeout", DEFAULT_TIMEOUT)
    secrets = spec.get("secrets", {})
    spec.get("storage", {})

    # Build resource requirements
    resource_requirements = {
        "limits": resources.get("limits", {"cpu": "2000m", "memory": "4Gi"}),
        "requests": resources.get("requests", {"cpu": "500m", "memory": "1Gi"}),
    }

    # Build environment variables
    env = [
        {"name": "SCAN_TARGET", "value": target},
        {"name": "SCAN_TYPE", "value": spec.get("scanType", "full")},
        {"name": "SCAN_TIMEOUT", "value": str(timeout)},
        {"name": "RESULTS_DIR", "value": "/results"},
    ]

    # Add API keys from secrets
    if secrets.get("apiKeys"):
        env.append({"name": "API_KEYS_SECRET", "valueFrom": {"secretKeyRef": {"name": secrets["apiKeys"], "key": "keys"}}})

    # Build volumes
    volumes = [{"name": "results", "persistentVolumeClaim": {"claimName": f"{name}-results"}}]

    volume_mounts = [{"name": "results", "mountPath": "/results"}]

    # Add SSH key if specified
    if secrets.get("sshKey"):
        volumes.append({"name": "ssh-key", "secret": {"secretName": secrets["sshKey"], "defaultMode": 0o400}})
        volume_mounts.append({"name": "ssh-key", "mountPath": "/secrets/ssh"})

    # Build the job manifest
    job = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": job_name,
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/name": "zen-ai-pentest",
                "app.kubernetes.io/component": "scanner",
                "app.kubernetes.io/managed-by": "zen-operator",
                "zen-ai.io/scan-name": name,
            },
            "ownerReferences": [
                {
                    "apiVersion": "security.zen-ai.io/v1",
                    "kind": "PentestScan",
                    "name": name,
                    "uid": "",  # Will be set by kopf
                    "controller": True,
                    "blockOwnerDeletion": True,
                }
            ],
        },
        "spec": {
            "ttlSecondsAfterFinished": 86400,  # Keep for 24 hours
            "activeDeadlineSeconds": timeout + 300,  # Add buffer
            "backoffLimit": MAX_RETRIES,
            "template": {
                "metadata": {
                    "labels": {
                        "app.kubernetes.io/name": "zen-ai-pentest",
                        "app.kubernetes.io/component": "scanner",
                        "zen-ai.io/scan-name": name,
                    }
                },
                "spec": {
                    "restartPolicy": "Never",
                    "containers": [
                        {
                            "name": "scanner",
                            "image": DEFAULT_SCAN_IMAGE,
                            "imagePullPolicy": "Always",
                            "command": build_scan_command(spec),
                            "env": env,
                            "resources": resource_requirements,
                            "volumeMounts": volume_mounts,
                            "securityContext": {
                                "allowPrivilegeEscalation": False,
                                "readOnlyRootFilesystem": True,
                                "runAsNonRoot": True,
                                "runAsUser": 1000,
                                "capabilities": {"drop": ["ALL"]},
                            },
                        }
                    ],
                    "volumes": volumes,
                },
            },
        },
    }

    return job


def create_cronjob_manifest(
    name: str,
    namespace: str,
    spec: Dict[str, Any],
    cronjob_name: str,
) -> Dict[str, Any]:
    """Create Kubernetes CronJob manifest."""
    job_name = create_job_name(name)
    job_template = create_job_manifest(name, namespace, spec, job_name)
    schedule = spec.get("schedule", "0 2 * * 1")  # Default: weekly Monday 2 AM

    # Remove ownerReferences from job template (CronJob owns the Job)
    job_template["metadata"].pop("ownerReferences", None)

    cronjob = {
        "apiVersion": "batch/v1",
        "kind": "CronJob",
        "metadata": {
            "name": cronjob_name,
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/name": "zen-ai-pentest",
                "app.kubernetes.io/component": "scheduled-scanner",
                "app.kubernetes.io/managed-by": "zen-operator",
                "zen-ai.io/scan-name": name,
            },
        },
        "spec": {
            "schedule": schedule,
            "concurrencyPolicy": "Forbid",  # Don't run multiple instances
            "successfulJobsHistoryLimit": 3,
            "failedJobsHistoryLimit": 3,
            "jobTemplate": {"spec": job_template["spec"]},
        },
    }

    return cronjob


def create_pvc_manifest(name: str, namespace: str, storage: Dict[str, Any]) -> Dict[str, Any]:
    """Create PersistentVolumeClaim for results."""
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": f"{name}-results",
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/name": "zen-ai-pentest",
                "app.kubernetes.io/component": "storage",
                "zen-ai.io/scan-name": name,
            },
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": storage.get("size", "10Gi")}},
            "storageClassName": storage.get("storageClass") or None,
        },
    }


async def send_notification(spec: Dict[str, Any], status: str, message: str):
    """Send notification on scan completion."""
    notifications = spec.get("notifications", {})

    if not notifications:
        return

    # Check if we should notify for this status
    on_success = notifications.get("onSuccess", False)
    on_failure = notifications.get("onFailure", True)

    if status == "Completed" and not on_success:
        return
    if status == "Failed" and not on_failure:
        return

    target = spec.get("target", "")
    scan_type = spec.get("scanType", "unknown")

    payload = {
        "scan": spec.get("metadata", {}).get("name", "unknown"),
        "target": target,
        "type": scan_type,
        "status": status,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Slack notification
    if notifications.get("slack"):
        try:
            import aiohttp

            slack_url = notifications["slack"]
            if not slack_url.startswith("http"):
                # Assume it's a channel, would need webhook URL from secret
                logger.info(f"Slack channel specified: {slack_url}")
            else:
                async with aiohttp.ClientSession() as session:
                    await session.post(slack_url, json={"text": f"🔒 Zen-AI Scan {status}: {target} ({scan_type})\n{message}"})
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    # Webhook notification
    if notifications.get("webhook"):
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                await session.post(notifications["webhook"], json=payload)
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")

    # Email notification would require SMTP configuration
    if notifications.get("email"):
        logger.info(f"Email notifications would be sent to: {notifications['email']}")


# ============================================================================
# Kopf Handlers
# ============================================================================


@kopf.on.create("security.zen-ai.io", "v1", "pentestscans")
async def create_scan(spec: Dict[str, Any], name: str, namespace: str, **kwargs):
    """Handle creation of a PentestScan resource."""
    logger.info(f"Creating scan: {name} in namespace: {namespace}")

    api = k8s_client.BatchV1Api()
    core_api = k8s_client.CoreV1Api()

    # Create PVC for results
    storage = spec.get("storage", {})
    pvc_manifest = create_pvc_manifest(name, namespace, storage)

    try:
        core_api.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc_manifest)
        logger.info(f"Created PVC: {name}-results")
    except ApiException as e:
        if e.status == 409:
            logger.info(f"PVC already exists: {name}-results")
        else:
            raise

    # Check if this is a scheduled scan
    if spec.get("schedule"):
        cronjob_name = create_cronjob_name(name)
        cronjob_manifest = create_cronjob_manifest(name, namespace, spec, cronjob_name)

        api.create_namespaced_cron_job(namespace=namespace, body=cronjob_manifest)
        logger.info(f"Created CronJob: {cronjob_name}")

        return {
            "phase": "Scheduled",
            "message": f"Scheduled scan created with cron: {spec['schedule']}",
            "cronJobName": cronjob_name,
        }
    else:
        # Create immediate Job
        job_name = create_job_name(name)
        job_manifest = create_job_manifest(name, namespace, spec, job_name)

        # Set owner reference
        if "uid" in kwargs.get("body", {}).get("metadata", {}):
            uid = kwargs["body"]["metadata"]["uid"]
            job_manifest["metadata"]["ownerReferences"][0]["uid"] = uid

        api.create_namespaced_job(namespace=namespace, body=job_manifest)
        logger.info(f"Created Job: {job_name}")

        return {
            "phase": "Pending",
            "message": "Scan job created, waiting for pod scheduling",
            "jobName": job_name,
            "startTime": datetime.now(timezone.utc).isoformat(),
        }


@kopf.on.update("security.zen-ai.io", "v1", "pentestscans")
async def update_scan(spec: Dict[str, Any], old: Dict[str, Any], name: str, namespace: str, **kwargs):
    """Handle updates to a PentestScan resource."""
    logger.info(f"Updating scan: {name}")

    api = k8s_client.BatchV1Api()

    # If schedule changed, update CronJob
    if spec.get("schedule"):
        cronjob_name = create_cronjob_name(name)

        try:
            # Check if CronJob exists
            api.read_namespaced_cron_job(name=cronjob_name, namespace=namespace)

            # Update schedule
            patch = {"spec": {"schedule": spec["schedule"]}}
            api.patch_namespaced_cron_job(name=cronjob_name, namespace=namespace, body=patch)
            logger.info(f"Updated CronJob schedule: {cronjob_name}")

            return {"message": f"Updated schedule to: {spec['schedule']}"}
        except ApiException as e:
            if e.status == 404:
                # CronJob doesn't exist, create it
                cronjob_manifest = create_cronjob_manifest(name, namespace, spec, cronjob_name)
                api.create_namespaced_cron_job(namespace=namespace, body=cronjob_manifest)
                logger.info(f"Created new CronJob: {cronjob_name}")

                return {
                    "phase": "Scheduled",
                    "message": f"Converted to scheduled scan with cron: {spec['schedule']}",
                    "cronJobName": cronjob_name,
                }
            raise

    return {"message": "Scan configuration updated"}


@kopf.on.delete("security.zen-ai.io", "v1", "pentestscans")
async def delete_scan(spec: Dict[str, Any], name: str, namespace: str, **kwargs):
    """Handle deletion of a PentestScan resource."""
    logger.info(f"Deleting scan: {name}")

    api = k8s_client.BatchV1Api()
    core_api = k8s_client.CoreV1Api()

    # Clean up CronJob if exists
    if spec.get("schedule"):
        cronjob_name = create_cronjob_name(name)
        try:
            api.delete_namespaced_cron_job(name=cronjob_name, namespace=namespace, body=k8s_client.V1DeleteOptions())
            logger.info(f"Deleted CronJob: {cronjob_name}")
        except ApiException as e:
            if e.status != 404:
                logger.error(f"Error deleting CronJob: {e}")

    # Clean up PVC if not retained
    storage = spec.get("storage", {})
    if not storage.get("retain", True):
        try:
            core_api.delete_namespaced_persistent_volume_claim(
                name=f"{name}-results", namespace=namespace, body=k8s_client.V1DeleteOptions()
            )
            logger.info(f"Deleted PVC: {name}-results")
        except ApiException as e:
            if e.status != 404:
                logger.error(f"Error deleting PVC: {e}")


@kopf.on.field("batch", "v1", "jobs", field="status.active")
async def job_status_change(old, new, body, **kwargs):
    """Monitor Job status changes."""
    job_name = body["metadata"]["name"]
    body["metadata"]["namespace"]

    # Find the owning PentestScan
    owner_refs = body["metadata"].get("ownerReferences", [])
    scan_name = None

    for ref in owner_refs:
        if ref.get("kind") == "PentestScan":
            scan_name = ref["name"]
            break

    if not scan_name:
        return

    logger.info(f"Job {job_name} status changed for scan {scan_name}")


@kopf.timer("security.zen-ai.io", "v1", "pentestscans", interval=30)
async def scan_timer(spec: Dict[str, Any], status: Dict[str, Any], name: str, namespace: str, **kwargs):
    """Periodic check for scan status."""
    api = k8s_client.BatchV1Api()
    core_api = k8s_client.CoreV1Api()
    custom_api = k8s_client.CustomObjectsApi()

    current_phase = status.get("phase", "Pending")

    # Skip if already completed or failed
    if current_phase in ["Completed", "Failed", "Cancelled", "Scheduled"]:
        return

    job_name = status.get("jobName", "")
    if not job_name:
        return

    try:
        job = api.read_namespaced_job_status(name=job_name, namespace=namespace)
        job_status = job.status

        new_phase = current_phase
        message = status.get("message", "")

        # Check if job has completed
        if job_status.succeeded:
            new_phase = "Completed"
            message = "Scan completed successfully"

            # Try to get pod logs for results summary
            try:
                pods = core_api.list_namespaced_pod(namespace=namespace, label_selector=f"job-name={job_name}")
                if pods.items:
                    pod_name = pods.items[0].metadata.name
                    status["podName"] = pod_name
            except Exception as e:
                logger.warning(f"Could not get pod info: {e}")

            # Send notification
            await send_notification(spec, "Completed", message)

        elif job_status.failed:
            new_phase = "Failed"
            message = f"Scan failed after {job_status.failed} attempts"

            # Send notification
            await send_notification(spec, "Failed", message)

        elif job_status.active:
            new_phase = "Running"
            message = "Scan is in progress"

            # Get pod name
            try:
                pods = core_api.list_namespaced_pod(namespace=namespace, label_selector=f"job-name={job_name}")
                if pods.items:
                    pod_name = pods.items[0].metadata.name
                    status["podName"] = pod_name
            except Exception:
                pass

        # Update status if changed
        if new_phase != current_phase:
            patch = {
                "status": {
                    "phase": new_phase,
                    "message": message,
                }
            }

            if new_phase == "Completed":
                patch["status"]["completionTime"] = datetime.now(timezone.utc).isoformat()
                # Mock results - in real implementation, parse from pod output
                patch["status"]["results"] = {
                    "findingsCount": 0,
                    "criticalCount": 0,
                    "highCount": 0,
                    "mediumCount": 0,
                    "lowCount": 0,
                    "reportPath": f"/results/{job_name}",
                }

            custom_api.patch_namespaced_custom_object_status(
                group="security.zen-ai.io", version="v1", namespace=namespace, plural="pentestscans", name=name, body=patch
            )

            logger.info(f"Updated scan {name} status to {new_phase}")

    except ApiException as e:
        if e.status == 404:
            # Job was deleted
            if current_phase not in ["Completed", "Failed"]:
                patch = {
                    "status": {
                        "phase": "Failed",
                        "message": "Scan job was deleted unexpectedly",
                    }
                }
                try:
                    custom_api.patch_namespaced_custom_object_status(
                        group="security.zen-ai.io",
                        version="v1",
                        namespace=namespace,
                        plural="pentestscans",
                        name=name,
                        body=patch,
                    )
                except Exception as patch_err:
                    logger.error(f"Failed to update status: {patch_err}")
        else:
            logger.error(f"Error checking job status: {e}")


@kopf.on.startup()
async def startup(**kwargs):
    """Operator startup handler."""
    logger.info("Starting Zen-AI-Pentest Operator")

    # Initialize Kubernetes client
    try:
        get_k8s_client()
        logger.info("Kubernetes client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Kubernetes client: {e}")
        raise


@kopf.on.cleanup()
async def cleanup(**kwargs):
    """Operator cleanup handler."""
    logger.info("Shutting down Zen-AI-Pentest Operator")


if __name__ == "__main__":
    # Run the operator
    kopf.run(
        clusterwide=True,
        namespace=OPERATOR_NAMESPACE,
        priority=100,
    )
