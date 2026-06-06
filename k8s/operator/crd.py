"""
Custom Resource Definitions for Zen-AI-Pentest Kubernetes Operator.

This module defines the CRD schemas for ZenScan and ZenReport resources.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ScanType(str, Enum):
    """Supported scan types."""

    RECON = "recon"
    VULNERABILITY = "vulnerability"
    FULL = "full"
    COMPLIANCE = "compliance"


class ScanPhase(str, Enum):
    """Scan execution phases."""

    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class AuthType(str, Enum):
    """Authentication types."""

    JWT = "jwt"
    API_KEY = "api_key"
    BASIC = "basic"
    NONE = "none"


class ToolType(str, Enum):
    """Available security tools."""

    NMAP = "nmap"
    NUCLEI = "nuclei"
    ZAP = "zap"
    SQLMAP = "sqlmap"
    ALL = "all"


@dataclass
class AuthConfig:
    """Authentication configuration for scans."""

    type: AuthType = AuthType.NONE
    secret_ref: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type.value, "secretRef": self.secret_ref}


@dataclass
class NotificationConfig:
    """Notification configuration for scan results."""

    slack: Optional[str] = None
    email: Optional[str] = None
    webhook: Optional[str] = None
    discord: Optional[str] = None
    telegram: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.slack:
            result["slack"] = self.slack
        if self.email:
            result["email"] = self.email
        if self.webhook:
            result["webhook"] = self.webhook
        if self.discord:
            result["discord"] = self.discord
        if self.telegram:
            result["telegram"] = self.telegram
        return result


@dataclass
class ResourceRequirements:
    """Resource requirements for scan jobs."""

    cpu_request: str = "500m"
    cpu_limit: str = "2000m"
    memory_request: str = "512Mi"
    memory_limit: str = "2Gi"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requests": {"cpu": self.cpu_request, "memory": self.memory_request},
            "limits": {"cpu": self.cpu_limit, "memory": self.memory_limit},
        }


@dataclass
class ScanSpec:
    """ZenScan resource specification."""

    target: str
    scan_type: ScanType = ScanType.FULL
    schedule: Optional[str] = None
    tools: List[ToolType] = field(default_factory=lambda: [ToolType.ALL])
    auth: AuthConfig = field(default_factory=AuthConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    resources: ResourceRequirements = field(default_factory=ResourceRequirements)
    timeout: int = 3600  # seconds
    concurrent_scans: int = 1
    priority: int = 5  # 1-10, lower is higher priority

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "scanType": self.scan_type.value,
            "schedule": self.schedule,
            "tools": [t.value for t in self.tools],
            "auth": self.auth.to_dict(),
            "notifications": self.notifications.to_dict(),
            "resources": self.resources.to_dict(),
            "timeout": self.timeout,
            "concurrentScans": self.concurrent_scans,
            "priority": self.priority,
        }


@dataclass
class ScanStatus:
    """ZenScan resource status."""

    phase: ScanPhase = ScanPhase.PENDING
    start_time: Optional[str] = None
    completion_time: Optional[str] = None
    findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    info_findings: int = 0
    report_url: Optional[str] = None
    job_name: Optional[str] = None
    pod_name: Optional[str] = None
    message: Optional[str] = None
    progress_percent: int = 0
    last_transition_time: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "startTime": self.start_time,
            "completionTime": self.completion_time,
            "findings": self.findings,
            "criticalFindings": self.critical_findings,
            "highFindings": self.high_findings,
            "mediumFindings": self.medium_findings,
            "lowFindings": self.low_findings,
            "infoFindings": self.info_findings,
            "reportUrl": self.report_url,
            "jobName": self.job_name,
            "podName": self.pod_name,
            "message": self.message,
            "progressPercent": self.progress_percent,
            "lastTransitionTime": self.last_transition_time,
        }


@dataclass
class ZenScanResource:
    """Complete ZenScan resource definition."""

    api_version: str = "security.zen-ai.io/v1"
    kind: str = "ZenScan"
    metadata: Dict[str, Any] = field(default_factory=dict)
    spec: ScanSpec = field(default_factory=lambda: ScanSpec(target=""))
    status: ScanStatus = field(default_factory=ScanStatus)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "apiVersion": self.api_version,
            "kind": self.kind,
            "metadata": self.metadata,
            "spec": self.spec.to_dict(),
            "status": self.status.to_dict(),
        }


@dataclass
class ReportFormat:
    """Report format configuration."""

    format: str = "pdf"  # pdf, html, json, xml, sarif
    include_evidence: bool = True
    include_screenshots: bool = True
    template: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "includeEvidence": self.include_evidence,
            "includeScreenshots": self.include_screenshots,
            "template": self.template,
        }


@dataclass
class ReportSpec:
    """ZenReport resource specification."""

    scan_ref: Dict[str, str] = field(default_factory=dict)
    format: ReportFormat = field(default_factory=ReportFormat)
    recipients: List[str] = field(default_factory=list)
    storage_class: Optional[str] = None
    retention_days: int = 90
    encryption_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scanRef": self.scan_ref,
            "format": self.format.to_dict(),
            "recipients": self.recipients,
            "storageClass": self.storage_class,
            "retentionDays": self.retention_days,
            "encryptionEnabled": self.encryption_enabled,
        }


@dataclass
class ReportStatus:
    """ZenReport resource status."""

    phase: str = "Pending"  # Pending, Generating, Completed, Failed
    start_time: Optional[str] = None
    completion_time: Optional[str] = None
    report_url: Optional[str] = None
    size_bytes: int = 0
    checksum: Optional[str] = None
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "startTime": self.start_time,
            "completionTime": self.completion_time,
            "reportUrl": self.report_url,
            "sizeBytes": self.size_bytes,
            "checksum": self.checksum,
            "message": self.message,
        }


@dataclass
class ZenReportResource:
    """Complete ZenReport resource definition."""

    api_version: str = "security.zen-ai.io/v1"
    kind: str = "ZenReport"
    metadata: Dict[str, Any] = field(default_factory=dict)
    spec: ReportSpec = field(default_factory=ReportSpec)
    status: ReportStatus = field(default_factory=ReportStatus)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "apiVersion": self.api_version,
            "kind": self.kind,
            "metadata": self.metadata,
            "spec": self.spec.to_dict(),
            "status": self.status.to_dict(),
        }


# CRD YAML Definitions for kubectl apply
ZENSCAN_CRD_YAML = r"""
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: zenscans.security.zen-ai.io
  labels:
    app: zen-pentest-operator
spec:
  group: security.zen-ai.io
  names:
    plural: zenscans
    singular: zenscan
    kind: ZenScan
    shortNames:
      - zs
      - scan
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      subresources:
        status: {}
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required:
                - target
              properties:
                target:
                  type: string
                  description: "Target URL/IP to scan"
                  pattern: '^[a-zA-Z0-9][-a-zA-Z0-9.:/]*$'
                scanType:
                  type: string
                  enum: ["recon", "vulnerability", "full", "compliance"]
                  default: "full"
                  description: "Type of security scan to perform"
                schedule:
                  type: string
                  description: "Cron expression for recurring scans (optional)"
                  pattern: '^([0-9,*/-]+\s+){4}[0-9,*/-]+$|^@'
                tools:
                  type: array
                  items:
                    type: string
                    enum: ["nmap", "nuclei", "zap", "sqlmap", "all"]
                  default: ["all"]
                  description: "Security tools to use"
                auth:
                  type: object
                  properties:
                    type:
                      type: string
                      enum: ["jwt", "api_key", "basic", "none"]
                      default: "none"
                    secretRef:
                      type: string
                      description: "Kubernetes secret name containing credentials"
                notifications:
                  type: object
                  properties:
                    slack:
                      type: string
                      description: "Slack webhook URL"
                      format: uri
                    email:
                      type: string
                      description: "Email address for notifications"
                      format: email
                    webhook:
                      type: string
                      description: "Generic webhook URL"
                      format: uri
                    discord:
                      type: string
                      description: "Discord webhook URL"
                      format: uri
                    telegram:
                      type: string
                      description: "Telegram bot token and chat ID"
                resources:
                  type: object
                  properties:
                    requests:
                      type: object
                      properties:
                        cpu:
                          type: string
                          default: "500m"
                        memory:
                          type: string
                          default: "512Mi"
                    limits:
                      type: object
                      properties:
                        cpu:
                          type: string
                          default: "2000m"
                        memory:
                          type: string
                          default: "2Gi"
                timeout:
                  type: integer
                  default: 3600
                  minimum: 60
                  maximum: 86400
                  description: "Scan timeout in seconds"
                concurrentScans:
                  type: integer
                  default: 1
                  minimum: 1
                  maximum: 10
                  description: "Number of concurrent scans"
                priority:
                  type: integer
                  default: 5
                  minimum: 1
                  maximum: 10
                  description: "Scan priority (1=highest, 10=lowest)"
            status:
              type: object
              properties:
                phase:
                  type: string
                  enum: ["Pending", "Running", "Completed", "Failed"]
                  description: "Current phase of the scan"
                startTime:
                  type: string
                  format: date-time
                  description: "When the scan started"
                completionTime:
                  type: string
                  format: date-time
                  description: "When the scan completed"
                findings:
                  type: integer
                  description: "Total number of findings"
                criticalFindings:
                  type: integer
                  description: "Number of critical findings"
                highFindings:
                  type: integer
                  description: "Number of high severity findings"
                mediumFindings:
                  type: integer
                  description: "Number of medium severity findings"
                lowFindings:
                  type: integer
                  description: "Number of low severity findings"
                infoFindings:
                  type: integer
                  description: "Number of informational findings"
                reportUrl:
                  type: string
                  description: "URL to the scan report"
                jobName:
                  type: string
                  description: "Name of the Kubernetes Job"
                podName:
                  type: string
                  description: "Name of the scan Pod"
                message:
                  type: string
                  description: "Status message or error details"
                progressPercent:
                  type: integer
                  minimum: 0
                  maximum: 100
                  description: "Scan progress percentage"
                lastTransitionTime:
                  type: string
                  format: date-time
                  description: "Last status transition timestamp"
      additionalPrinterColumns:
        - name: Target
          type: string
          jsonPath: .spec.target
          description: "Scan target"
        - name: Type
          type: string
          jsonPath: .spec.scanType
          description: "Scan type"
        - name: Phase
          type: string
          jsonPath: .status.phase
          description: "Current phase"
        - name: Findings
          type: integer
          jsonPath: .status.findings
          description: "Total findings"
        - name: Age
          type: date
          jsonPath: .metadata.creationTimestamp
"""

ZENREPORT_CRD_YAML = """
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: zenreports.security.zen-ai.io
  labels:
    app: zen-pentest-operator
spec:
  group: security.zen-ai.io
  names:
    plural: zenreports
    singular: zenreport
    kind: ZenReport
    shortNames:
      - zr
      - report
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      subresources:
        status: {}
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required:
                - scanRef
              properties:
                scanRef:
                  type: object
                  required:
                    - name
                  properties:
                    name:
                      type: string
                      description: "Name of the ZenScan resource"
                    namespace:
                      type: string
                      description: "Namespace of the ZenScan resource"
                      default: ""
                format:
                  type: object
                  properties:
                    format:
                      type: string
                      enum: ["pdf", "html", "json", "xml", "sarif"]
                      default: "pdf"
                      description: "Report output format"
                    includeEvidence:
                      type: boolean
                      default: true
                      description: "Include evidence in report"
                    includeScreenshots:
                      type: boolean
                      default: true
                      description: "Include screenshots in report"
                    template:
                      type: string
                      description: "Custom report template name"
                recipients:
                  type: array
                  items:
                    type: string
                    format: email
                  description: "Email recipients for the report"
                storageClass:
                  type: string
                  description: "Storage class for report PVC"
                retentionDays:
                  type: integer
                  default: 90
                  minimum: 1
                  maximum: 365
                  description: "Number of days to retain the report"
                encryptionEnabled:
                  type: boolean
                  default: true
                  description: "Enable report encryption"
            status:
              type: object
              properties:
                phase:
                  type: string
                  enum: ["Pending", "Generating", "Completed", "Failed"]
                  description: "Current phase of report generation"
                startTime:
                  type: string
                  format: date-time
                  description: "When report generation started"
                completionTime:
                  type: string
                  format: date-time
                  description: "When report generation completed"
                reportUrl:
                  type: string
                  description: "URL to download the report"
                sizeBytes:
                  type: integer
                  description: "Report file size in bytes"
                checksum:
                  type: string
                  description: "SHA256 checksum of the report"
                message:
                  type: string
                  description: "Status message or error details"
      additionalPrinterColumns:
        - name: Scan
          type: string
          jsonPath: .spec.scanRef.name
          description: "Source scan"
        - name: Format
          type: string
          jsonPath: .spec.format.format
          description: "Report format"
        - name: Phase
          type: string
          jsonPath: .status.phase
          description: "Current phase"
        - name: Size
          type: integer
          jsonPath: .status.sizeBytes
          description: "Report size in bytes"
        - name: Age
          type: date
          jsonPath: .metadata.creationTimestamp
"""


def get_crd_manifests() -> Dict[str, str]:
    """Get all CRD manifests as a dictionary."""
    return {"zenscan-crd.yaml": ZENSCAN_CRD_YAML, "zenreport-crd.yaml": ZENREPORT_CRD_YAML}


def generate_example_zenscan(name: str = "example-scan", target: str = "scanme.nmap.org") -> str:
    """Generate an example ZenScan YAML manifest."""
    return f"""
apiVersion: security.zen-ai.io/v1
kind: ZenScan
metadata:
  name: {name}
  namespace: default
  labels:
    app: zen-pentest
    environment: production
spec:
  target: {target}
  scanType: full
  tools:
    - nmap
    - nuclei
  auth:
    type: none
  notifications:
    email: security@example.com
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "2000m"
      memory: "2Gi"
  timeout: 3600
  concurrentScans: 1
  priority: 5
"""


def generate_example_zenreport(name: str = "example-report", scan_name: str = "example-scan") -> str:
    """Generate an example ZenReport YAML manifest."""
    return f"""
apiVersion: security.zen-ai.io/v1
kind: ZenReport
metadata:
  name: {name}
  namespace: default
spec:
  scanRef:
    name: {scan_name}
    namespace: default
  format:
    format: pdf
    includeEvidence: true
    includeScreenshots: true
  recipients:
    - security@example.com
    - compliance@example.com
  retentionDays: 90
  encryptionEnabled: true
"""


if __name__ == "__main__":
    # Output CRD manifests
    print("=== ZenScan CRD ===")
    print(ZENSCAN_CRD_YAML)
    print("\n=== ZenReport CRD ===")
    print(ZENREPORT_CRD_YAML)
    print("\n=== Example ZenScan ===")
    print(generate_example_zenscan())
    print("\n=== Example ZenReport ===")
    print(generate_example_zenreport())
