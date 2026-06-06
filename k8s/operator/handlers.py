"""
Resource Handlers for Zen-AI-Pentest Kubernetes Operator.

This module contains handlers for creating, updating, and deleting
scan and report jobs based on custom resource changes.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from kubernetes.client.rest import ApiException

from kubernetes import client

logger = logging.getLogger(__name__)


class ScanJobHandler:
    """Handler for ZenScan resource lifecycle."""

    def __init__(self, operator: Any):
        """Initialize handler with operator reference."""
        self.operator = operator
        self.config = operator.config
        self.core_api = operator.core_api
        self.batch_api = operator.batch_api
        self.custom_api = operator.custom_api

    async def create_scan_job(self, zenscan: Dict[str, Any]) -> None:
        """
        Create a Kubernetes Job for executing a security scan.

        Args:
            zenscan: The ZenScan custom resource
        """
        metadata = zenscan.get("metadata", {})
        spec = zenscan.get("spec", {})

        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")
        uid = metadata.get("uid", "")

        # Check if job already exists
        job_name = f"zen-scan-{name}"
        try:
            existing = self.batch_api.read_namespaced_job(name=job_name, namespace=namespace)
            if existing:
                logger.info(f"Scan job {job_name} already exists, skipping creation")
                return
        except ApiException as e:
            if e.status != 404:
                raise

        logger.info(f"Creating scan job for {namespace}/{name}")

        # Extract configuration
        target = spec.get("target")
        scan_type = spec.get("scanType", "full")
        tools = spec.get("tools", ["all"])
        timeout = spec.get("timeout", 3600)
        spec.get("priority", 5)

        # Resource configuration
        resources = spec.get("resources", {})
        resource_requests = resources.get("requests", {})
        resource_limits = resources.get("limits", {})

        # Build container resources
        container_resources = client.V1ResourceRequirements(
            requests={"cpu": resource_requests.get("cpu", "500m"), "memory": resource_requests.get("memory", "512Mi")},
            limits={"cpu": resource_limits.get("cpu", "2000m"), "memory": resource_limits.get("memory", "2Gi")},
        )

        # Build environment variables
        env_vars = self._build_scan_env_vars(spec, zenscan)

        # Build volume mounts
        volume_mounts = [
            client.V1VolumeMount(name="reports", mount_path="/reports"),
            client.V1VolumeMount(name="tmp", mount_path="/tmp"),  # nosec B108
            client.V1VolumeMount(name="config", mount_path="/config", read_only=True),
        ]

        # Build volumes
        volumes = [
            client.V1Volume(
                name="reports",
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name="zen-reports-pvc"),
            ),
            client.V1Volume(name="tmp", empty_dir=client.V1EmptyDirVolumeSource()),
            client.V1Volume(name="config", config_map=client.V1ConfigMapVolumeSource(name="zen-scanner-config")),
        ]

        # Add secret volume if auth is configured
        auth = spec.get("auth", {})
        auth_type = auth.get("type", "none")
        secret_ref = auth.get("secretRef")

        if auth_type != "none" and secret_ref:
            volume_mounts.append(client.V1VolumeMount(name="auth-secrets", mount_path="/secrets", read_only=True))
            volumes.append(client.V1Volume(name="auth-secrets", secret=client.V1SecretVolumeSource(secret_name=secret_ref)))

        # Build security context
        security_context = client.V1SecurityContext(
            run_as_non_root=True,
            run_as_user=1000,
            run_as_group=1000,
            read_only_root_filesystem=True,
            allow_privilege_escalation=False,
            capabilities=client.V1Capabilities(drop=["ALL"]),
            seccomp_profile=client.V1SeccompProfile(type="RuntimeDefault"),
        )

        # Build pod spec
        container = client.V1Container(
            name="scanner",
            image=self.config.scanner_image,
            image_pull_policy=self.config.image_pull_policy,
            command=["python", "-m", "zen_ai_pentest"],
            args=[
                "scan",
                "--target",
                target,
                "--type",
                scan_type,
                "--tools",
                ",".join(tools),
                "--output",
                "/reports",
                "--format",
                "json",
                f"--timeout={timeout}",
            ],
            env=env_vars,
            resources=container_resources,
            volume_mounts=volume_mounts,
            security_context=security_context,
            liveness_probe=client.V1Probe(
                exec_=client.V1ExecAction(
                    command=["python", "-c", "import os; exit(0 if os.path.exists('/reports/scan.pid') else 1)"]
                ),
                initial_delay_seconds=30,
                period_seconds=60,
                timeout_seconds=5,
                failure_threshold=3,
            ),
        )

        # Build pod template
        pod_template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={"app": "zen-pentest", "scan-id": name, "scan-uid": uid, "managed-by": "zen-operator"},
                annotations={"prometheus.io/scrape": "true", "prometheus.io/port": "8080", "prometheus.io/path": "/metrics"},
            ),
            spec=client.V1PodSpec(
                service_account_name="zen-scanner",
                security_context=client.V1PodSecurityContext(
                    run_as_non_root=True,
                    run_as_user=1000,
                    fs_group=1000,
                    seccomp_profile=client.V1SeccompProfile(type="RuntimeDefault"),
                ),
                containers=[container],
                volumes=volumes,
                restart_policy="Never",
                dns_policy="ClusterFirst",
                automount_service_account_token=False,
                termination_grace_period_seconds=30,
            ),
        )

        # Build job spec
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_name,
                namespace=namespace,
                labels={"app": "zen-pentest", "scan-id": name, "scan-uid": uid, "managed-by": "zen-operator"},
                owner_references=[
                    client.V1OwnerReference(
                        api_version="security.zen-ai.io/v1",
                        kind="ZenScan",
                        name=name,
                        uid=uid,
                        controller=True,
                        block_owner_deletion=True,
                    )
                ],
            ),
            spec=client.V1JobSpec(
                template=pod_template,
                backoff_limit=1,
                ttl_seconds_after_finished=86400,  # 24 hours
                active_deadline_seconds=timeout,
                parallelism=1,
                completions=1,
            ),
        )

        # Create the job
        try:
            self.batch_api.create_namespaced_job(namespace=namespace, body=job)
            logger.info(f"Created scan job {job_name}")

            # Update ZenScan status
            await self.operator.update_status(
                namespace,
                name,
                "zenscans",
                {
                    "phase": "Running",
                    "startTime": datetime.now(timezone.utc).isoformat() + "Z",
                    "jobName": job_name,
                    "message": "Scan job created successfully",
                },
            )

            self.operator.metrics["scans_created"] += 1

        except ApiException as e:
            logger.error(f"Failed to create scan job: {e}")
            await self.operator.update_status(
                namespace, name, "zenscans", {"phase": "Failed", "message": f"Failed to create job: {e.reason}"}
            )
            raise

    async def update_scan_job(self, zenscan: Dict[str, Any]) -> None:
        """
        Update an existing scan job based on resource changes.

        Args:
            zenscan: The updated ZenScan custom resource
        """
        metadata = zenscan.get("metadata", {})
        status = zenscan.get("status", {})

        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")
        job_name = status.get("jobName", f"zen-scan-{name}")

        logger.debug(f"Updating scan job for {namespace}/{name}")

        try:
            # Check job status
            job = self.batch_api.read_namespaced_job(name=job_name, namespace=namespace)

            job_status = job.status
            if job_status:
                if job_status.succeeded:
                    # Job completed successfully
                    await self._handle_scan_completion(zenscan, job, succeeded=True)
                elif job_status.failed:
                    # Job failed
                    await self._handle_scan_completion(zenscan, job, succeeded=False)
                else:
                    # Job still running - update progress if possible
                    await self._update_scan_progress(zenscan, job)

        except ApiException as e:
            if e.status == 404:
                # Job doesn't exist - may have been deleted
                logger.warning(f"Scan job {job_name} not found")
                # Optionally recreate the job
                await self.create_scan_job(zenscan)
            else:
                raise

    async def delete_scan_job(self, zenscan: Dict[str, Any]) -> None:
        """
        Delete a scan job and associated resources.

        Args:
            zenscan: The deleted ZenScan custom resource
        """
        metadata = zenscan.get("metadata", {})
        status = zenscan.get("status", {})

        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")
        job_name = status.get("jobName", f"zen-scan-{name}")

        logger.info(f"Deleting scan job for {namespace}/{name}")

        try:
            # Delete the job with background propagation
            self.batch_api.delete_namespaced_job(
                name=job_name, namespace=namespace, body=client.V1DeleteOptions(propagation_policy="Background")
            )
            logger.info(f"Deleted scan job {job_name}")

        except ApiException as e:
            if e.status == 404:
                logger.debug(f"Scan job {job_name} already deleted")
            else:
                raise

    def _build_scan_env_vars(self, spec: Dict[str, Any], zenscan: Dict[str, Any]) -> List[client.V1EnvVar]:
        """Build environment variables for scan container."""
        env_vars = [
            client.V1EnvVar(name="ZEN_SCAN_ID", value=zenscan["metadata"]["name"]),
            client.V1EnvVar(name="ZEN_SCAN_NAMESPACE", value=zenscan["metadata"]["namespace"]),
            client.V1EnvVar(name="ZEN_SCAN_TARGET", value=spec.get("target")),
            client.V1EnvVar(name="ZEN_SCAN_TYPE", value=spec.get("scanType", "full")),
            client.V1EnvVar(name="ZEN_OUTPUT_PATH", value="/reports"),
            client.V1EnvVar(name="ZEN_LOG_LEVEL", value="INFO"),
            client.V1EnvVar(name="PYTHONUNBUFFERED", value="1"),
        ]

        # Add notification settings
        notifications = spec.get("notifications", {})
        if notifications.get("slack"):
            env_vars.append(client.V1EnvVar(name="ZEN_SLACK_WEBHOOK", value=notifications["slack"]))
        if notifications.get("email"):
            env_vars.append(client.V1EnvVar(name="ZEN_NOTIFY_EMAIL", value=notifications["email"]))
        if notifications.get("webhook"):
            env_vars.append(client.V1EnvVar(name="ZEN_WEBHOOK_URL", value=notifications["webhook"]))

        # Add auth configuration
        auth = spec.get("auth", {})
        if auth.get("type") != "none":
            env_vars.append(client.V1EnvVar(name="ZEN_AUTH_TYPE", value=auth["type"]))
            if auth.get("secretRef"):
                env_vars.append(client.V1EnvVar(name="ZEN_AUTH_SECRET_PATH", value="/secrets"))

        return env_vars

    async def _handle_scan_completion(self, zenscan: Dict[str, Any], job: client.V1Job, succeeded: bool) -> None:
        """Handle scan job completion."""
        metadata = zenscan.get("metadata", {})
        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")

        phase = "Completed" if succeeded else "Failed"

        # Try to get scan results
        findings = 0
        try:
            # This would typically read from a shared storage or API
            findings = await self._get_scan_findings(namespace, name)
        except Exception as e:
            logger.warning(f"Could not retrieve findings: {e}")

        await self.operator.update_status(
            namespace,
            name,
            "zenscans",
            {
                "phase": phase,
                "completionTime": datetime.now(timezone.utc).isoformat() + "Z",
                "findings": findings,
                "message": "Scan completed successfully" if succeeded else "Scan failed",
            },
        )

        if succeeded:
            self.operator.metrics["scans_completed"] += 1
        else:
            self.operator.metrics["scans_failed"] += 1

        logger.info(f"Scan {namespace}/{name} {phase.lower()}")

    async def _update_scan_progress(self, zenscan: Dict[str, Any], job: client.V1Job) -> None:
        """Update scan progress in status."""
        metadata = zenscan.get("metadata", {})
        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")

        # Get pod name
        try:
            pods = self.core_api.list_namespaced_pod(
                namespace=namespace, label_selector=f"scan-id={name},job-name={job.metadata.name}"
            )
            if pods.items:
                pod_name = pods.items[0].metadata.name
                await self.operator.update_status(namespace, name, "zenscans", {"podName": pod_name})
        except Exception as e:
            logger.debug(f"Could not get pod name: {e}")

    async def _get_scan_findings(self, namespace: str, scan_name: str) -> int:
        """Get number of findings from scan results."""
        # This would typically read from shared storage
        # For now, return 0
        return 0


class ReportJobHandler:
    """Handler for ZenReport resource lifecycle."""

    def __init__(self, operator: Any):
        """Initialize handler with operator reference."""
        self.operator = operator
        self.config = operator.config
        self.core_api = operator.core_api
        self.batch_api = operator.batch_api
        self.custom_api = operator.custom_api

    async def create_report_job(self, zenreport: Dict[str, Any]) -> None:
        """Create a Kubernetes Job for generating a report."""
        metadata = zenreport.get("metadata", {})
        spec = zenreport.get("spec", {})

        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")
        uid = metadata.get("uid", "")

        scan_ref = spec.get("scanRef", {})
        scan_name = scan_ref.get("name", "")
        scan_namespace = scan_ref.get("namespace", namespace)

        if not scan_name:
            raise ValueError("scanRef.name is required")

        # Check if referenced scan exists
        try:
            self.custom_api.get_namespaced_custom_object(
                group="security.zen-ai.io", version="v1", namespace=scan_namespace, plural="zenscans", name=scan_name
            )
        except ApiException as e:
            if e.status == 404:
                raise ValueError(f"Referenced ZenScan {scan_namespace}/{scan_name} not found")
            raise

        job_name = f"zen-report-{name}"

        logger.info(f"Creating report job for {namespace}/{name}")

        # Extract format configuration
        format_config = spec.get("format", {})
        report_format = format_config.get("format", "pdf")
        include_evidence = format_config.get("includeEvidence", True)
        include_screenshots = format_config.get("includeScreenshots", True)

        # Build container
        container = client.V1Container(
            name="report-generator",
            image=self.config.scanner_image,
            image_pull_policy=self.config.image_pull_policy,
            command=["python", "-m", "zen_ai_pentest"],
            args=[
                "report",
                "generate",
                "--scan-id",
                scan_name,
                "--format",
                report_format,
                "--output",
                "/reports",
                f"--include-evidence={str(include_evidence).lower()}",
                f"--include-screenshots={str(include_screenshots).lower()}",
            ],
            env=[
                client.V1EnvVar(name="ZEN_REPORT_ID", value=name),
                client.V1EnvVar(name="ZEN_SCAN_ID", value=scan_name),
                client.V1EnvVar(name="ZEN_OUTPUT_PATH", value="/reports"),
            ],
            resources=client.V1ResourceRequirements(
                requests={"cpu": "250m", "memory": "256Mi"}, limits={"cpu": "1000m", "memory": "1Gi"}
            ),
            volume_mounts=[client.V1VolumeMount(name="reports", mount_path="/reports")],
            security_context=client.V1SecurityContext(
                run_as_non_root=True, run_as_user=1000, read_only_root_filesystem=True, allow_privilege_escalation=False
            ),
        )

        # Build job
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_name,
                namespace=namespace,
                labels={"app": "zen-pentest", "report-id": name, "scan-id": scan_name, "managed-by": "zen-operator"},
                owner_references=[
                    client.V1OwnerReference(
                        api_version="security.zen-ai.io/v1",
                        kind="ZenReport",
                        name=name,
                        uid=uid,
                        controller=True,
                        block_owner_deletion=True,
                    )
                ],
            ),
            spec=client.V1JobSpec(
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": "zen-pentest", "report-id": name, "scan-id": scan_name}),
                    spec=client.V1PodSpec(
                        service_account_name="zen-scanner",
                        security_context=client.V1PodSecurityContext(run_as_non_root=True, run_as_user=1000),
                        containers=[container],
                        volumes=[
                            client.V1Volume(
                                name="reports",
                                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                    claim_name="zen-reports-pvc"
                                ),
                            )
                        ],
                        restart_policy="Never",
                    ),
                ),
                backoff_limit=2,
                ttl_seconds_after_finished=604800,  # 7 days
            ),
        )

        # Create the job
        try:
            self.batch_api.create_namespaced_job(namespace=namespace, body=job)
            logger.info(f"Created report job {job_name}")

            # Update status
            await self.operator.update_status(
                namespace,
                name,
                "zenreports",
                {
                    "phase": "Generating",
                    "startTime": datetime.now(timezone.utc).isoformat() + "Z",
                    "message": "Report generation started",
                },
            )

        except ApiException as e:
            logger.error(f"Failed to create report job: {e}")
            await self.operator.update_status(
                namespace, name, "zenreports", {"phase": "Failed", "message": f"Failed to create job: {e.reason}"}
            )
            raise

    async def update_report_job(self, zenreport: Dict[str, Any]) -> None:
        """Update an existing report job."""
        metadata = zenreport.get("metadata", {})
        status = zenreport.get("status", {})

        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")
        job_name = status.get("jobName", f"zen-report-{name}")

        try:
            job = self.batch_api.read_namespaced_job(name=job_name, namespace=namespace)

            job_status = job.status
            if job_status:
                if job_status.succeeded:
                    await self._handle_report_completion(zenreport, job, succeeded=True)
                elif job_status.failed:
                    await self._handle_report_completion(zenreport, job, succeeded=False)

        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Report job {job_name} not found")
            else:
                raise

    async def delete_report_job(self, zenreport: Dict[str, Any]) -> None:
        """Delete a report job."""
        metadata = zenreport.get("metadata", {})
        status = zenreport.get("status", {})

        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")
        job_name = status.get("jobName", f"zen-report-{name}")

        logger.info(f"Deleting report job for {namespace}/{name}")

        try:
            self.batch_api.delete_namespaced_job(
                name=job_name, namespace=namespace, body=client.V1DeleteOptions(propagation_policy="Background")
            )
        except ApiException as e:
            if e.status != 404:
                raise

    async def _handle_report_completion(self, zenreport: Dict[str, Any], job: client.V1Job, succeeded: bool) -> None:
        """Handle report job completion."""
        metadata = zenreport.get("metadata", {})
        spec = zenreport.get("spec", {})

        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")

        phase = "Completed" if succeeded else "Failed"

        # Generate report URL
        report_format = spec.get("format", {}).get("format", "pdf")
        report_url = f"/reports/{name}.{report_format}"

        await self.operator.update_status(
            namespace,
            name,
            "zenreports",
            {
                "phase": phase,
                "completionTime": datetime.now(timezone.utc).isoformat() + "Z",
                "reportUrl": report_url if succeeded else None,
                "message": "Report generated successfully" if succeeded else "Report generation failed",
            },
        )

        logger.info(f"Report {namespace}/{name} {phase.lower()}")
