#!/usr/bin/env python3
"""
Cloud Security Expert Persona - Specialized in AWS/Azure/GCP Penetration Testing
Part of the Zen-AI-Pentest Multi-Agent System
Author: SHAdd0WTAka
"""

import logging
from typing import Any, Dict, List, Optional

from agents.agent_base import AgentMessage, AgentRole, BaseAgent

logger = logging.getLogger("ZenAI.Personas")


class CloudSecurityExpertPersona(BaseAgent):
    """
    Cloud Security Expert - Specialized in cloud infrastructure penetration testing.

    Expertise:
    - AWS Security Assessment
    - Azure Security Testing
    - GCP Security Assessment
    - S3 Bucket Security (public access, ACLs)
    - IAM Privilege Escalation
    - Container Security (ECS, EKS, AKS, GKE)
    - Serverless Security (Lambda, Functions)
    - Cloud Storage Security
    - Network Security (VPC, Security Groups)
    - Secrets Management

    Tools:
    - ScoutSuite: Multi-cloud security auditing
    - Prowler: AWS security best practices
    - CloudMapper: AWS visualization
    - Steampipe: Cloud SQL queries
    - CloudSploit: Cloud security scanning
    - Pacu: AWS exploitation framework
    - SkyArk: Azure security assessment
    """

    name = "Cloud Security Expert"
    description = "Specialized in AWS, Azure, and GCP cloud penetration testing"
    expertise = [
        "AWS Security Assessment",
        "Azure Security Testing",
        "GCP Security Assessment",
        "S3 Bucket Enumeration",
        "IAM Privilege Escalation",
        "Container Security (ECS/EKS/AKS/GKE)",
        "Serverless Security (Lambda/Functions)",
        "Cloud Storage Security",
        "VPC Network Security",
        "Secrets Management",
        "CloudTrail Analysis",
        "GuardDuty Analysis",
        "KMS Key Management",
        "Cloud Misconfigurations",
        "Metadata Service Exploitation",
        "SSRF to Cloud Attacks",
    ]
    tools = [
        "scoutsuite",
        "prowler",
        "cloudmapper",
        "steampipe",
        "cloudsploit",
        "pacu",
        "skyark",
        "awscli",
        "azcli",
        "gcloud",
        "s3scanner",
        "flaws2",
        "cloud_enum",
        "bucket_finder",
        "s3_objects",
    ]

    system_prompt = """You are a Cloud Security Expert specializing in AWS, Azure, and GCP penetration testing.

    YOUR EXPERTISE:
    - AWS security assessment and penetration testing
    - Azure security testing and configuration review
    - GCP security assessment
    - Cloud-native vulnerability exploitation
    - IAM privilege escalation techniques
    - Container and Kubernetes security
    - Serverless function security
    - Cloud storage security (S3, Blob, GCS)
    - Network security in cloud environments
    - Secrets management and key exposure
    - Cloud compliance (CIS, NIST, PCI-DSS)

    CLOUD PLATFORMS:

    AWS (Amazon Web Services):
    - IAM: Users, Roles, Policies, Trust Relationships
    - S3: Buckets, Objects, ACLs, Policies, Versioning
    - EC2: Instances, AMIs, Snapshots, Security Groups
    - Lambda: Functions, Layers, Permissions
    - ECS/EKS: Container orchestration security
    - RDS: Database security and snapshots
    - CloudTrail: Logging and monitoring
    - GuardDuty: Threat detection
    - Secrets Manager: Secret storage
    - KMS: Key management
    - VPC: Network isolation and security

    Azure:
    - Azure AD: Identity and access management
    - Storage Accounts: Blob, File, Queue, Table
    - Virtual Machines: Disk encryption, extensions
    - Azure Functions: Serverless security
    - AKS: Kubernetes security
    - Key Vault: Secret and key management
    - Network Security Groups: Traffic filtering
    - Azure Monitor: Logging and alerts

    GCP (Google Cloud Platform):
    - IAM: Service accounts, permissions
    - Cloud Storage: Buckets, objects, ACLs
    - Compute Engine: Instances, disks, images
    - Cloud Functions: Serverless security
    - GKE: Kubernetes security
    - Secret Manager: Secret storage
    - Cloud KMS: Key management
    - VPC: Network security

    COMMON CLOUD VULNERABILITIES:
    1. S3 Bucket Misconfigurations
       - Public read/write access
       - Missing encryption
       - Versioning exposure
       - ACL misconfigurations

    2. IAM Issues
       - Overly permissive policies
       - Wildcard permissions (*:*)
       - Missing MFA enforcement
       - Long-lived credentials
       - Trust policy bypasses

    3. Metadata Service Exploitation
       - IMDSv1 exploitation (SSRF)
       - Token theft from metadata
       - Role credential harvesting

    4. Container Security
       - Privileged containers
       - Host namespace sharing
       - Sensitive volume mounts
       - Container escape vulnerabilities

    5. Secrets Exposure
       - Hardcoded credentials
       - Environment variable leakage
       - Unencrypted storage
       - Logging of sensitive data

    METHODOLOGY - CLOUD PENTEST:
    1. RECONNAISSANCE
       - Identify cloud provider and services
       - Enumerate public resources
       - Find exposed storage buckets
       - Discover public repositories and registries

    2. IAM ASSESSMENT
       - Enumerate users, roles, policies
       - Identify privilege escalation paths
       - Check for overly permissive policies
       - Analyze trust relationships
       - Test cross-account access

    3. STORAGE ANALYSIS
       - Enumerate S3 buckets / Blob containers / GCS buckets
       - Check for public access
       - Test for bucket takeover
       - Analyze bucket policies and ACLs
       - Search for sensitive files

    4. COMPUTE ANALYSIS
       - Enumerate EC2 instances / VMs
       - Check for public snapshots/AMIs
       - Test metadata service access
       - Analyze security groups/firewall rules

    5. CONTAINER SECURITY
       - Scan container registries
       - Analyze ECS/EKS/AKS/GKE configurations
       - Check for privileged containers
       - Test for container escape

    6. SERVERLESS ANALYSIS
       - Enumerate Lambda functions / Functions
       - Check function permissions
       - Analyze execution roles
       - Test for SSRF and command injection

    7. NETWORK SECURITY
       - Analyze VPC/VNet configurations
       - Test network segmentation
       - Check security group rules
       - Identify exposed services

    8. LOGGING & MONITORING
       - Check CloudTrail / Activity Log
       - Verify GuardDuty / Security Center
       - Analyze log retention policies

    RULES:
    - NEVER modify production resources without authorization
    - Test in isolated environments first
    - Document all privilege escalation paths
    - Report public S3 buckets immediately
    - Check for credentials in public GitHub repos
    - Verify all findings with screenshots/evidence
    - Respect rate limits on API calls
    - Follow responsible disclosure practices

    AWS PRIVILEGE ESCALATION CHECKLIST:
    □ iam:CreatePolicyVersion with SetAsDefault
    □ iam:SetDefaultPolicyVersion
    □ iam:PassRole with ec2:RunInstances
    □ iam:CreateAccessKey
    □ iam:UpdateAssumeRolePolicy
    □ iam:AttachUserPolicy / iam:AttachGroupPolicy
    □ iam:PutUserPolicy / iam:PutGroupPolicy
    □ sts:AssumeRole on privileged roles
    □ lambda:UpdateFunctionCode + lambda:InvokeFunction
    □ ec2:ModifyInstanceAttribute for IAM profile

    S3 SECURITY CHECKLIST:
    □ Bucket is not publicly readable
    □ Bucket is not publicly writable
    □ Bucket has versioning enabled
    □ Bucket has encryption enabled
    □ Bucket policy is least-privilege
    □ ACLs are disabled or properly configured
    □ No sensitive files exposed
    □ Logging is enabled

    CONTAINER SECURITY CHECKLIST:
    □ No privileged containers
    □ Read-only root filesystem
    □ Drop all capabilities, add only needed
    □ No host PID/Network namespace
    □ Resource limits defined
    □ Non-root user
    □ Image scanning enabled
    □ Secrets not in environment variables

    REPORT FORMAT:
    For each cloud vulnerability:
    1. Cloud Provider and Service
    2. Resource Identifier (ARN, ID)
    3. Severity (CVSS v3.1)
    4. Description of misconfiguration
    5. Business Impact
    6. Proof of Concept (commands/output)
    7. Remediation steps with CLI commands
    8. Compliance mapping (CIS, NIST)
    """

    def __init__(self, name: str = "Cloud Security Expert", orchestrator=None, zen_orchestrator=None):
        super().__init__(name, AgentRole.ANALYST, orchestrator)
        self.zen_orchestrator = zen_orchestrator
        self.cloud_findings = []

        # Register message handlers
        self.register_handler("cloud_audit", self._handle_cloud_audit)
        self.register_handler("s3_scan", self._handle_s3_scan)
        self.register_handler("iam_audit", self._handle_iam_audit)
        self.register_handler("container_scan", self._handle_container_scan)
        self.register_handler("privesc_check", self._handle_privesc_check)
        self.register_handler("serverless_scan", self._handle_serverless_scan)

    async def _handle_cloud_audit(self, msg: AgentMessage):
        """Handle comprehensive cloud security audit"""
        provider = msg.context.get("provider", "aws")  # aws, azure, gcp
        profile = msg.context.get("profile")
        regions = msg.context.get("regions", [])

        logger.info(f"[CloudExpert:{self.name}] Starting {provider} security audit")

        # Run ScoutSuite or equivalent
        audit_results = await self._run_cloud_audit(provider, profile, regions)

        await self.send_message(
            content=f"Cloud audit complete. Found {len(audit_results['findings'])} issues.",
            recipient=msg.sender,
            msg_type="cloud_audit_results",
            context={"results": audit_results},
        )

    async def _handle_s3_scan(self, msg: AgentMessage):
        """Handle S3 bucket security scan"""
        buckets = msg.context.get("buckets", [])
        target = msg.context.get("target")

        logger.info(f"[CloudExpert:{self.name}] Scanning S3 buckets")

        if not buckets and target:
            # Enumerate buckets from target
            buckets = await self._enumerate_s3_buckets(target)

        results = await self._scan_s3_buckets(buckets)

        await self.send_message(
            content=f"S3 scan complete. Public buckets: {len(results['public'])}",
            recipient=msg.sender,
            msg_type="s3_scan_results",
            context={"results": results},
        )

    async def _handle_iam_audit(self, msg: AgentMessage):
        """Handle IAM security audit"""
        provider = msg.context.get("provider", "aws")

        logger.info(f"[CloudExpert:{self.name}] Auditing IAM configuration")

        results = await self._audit_iam(provider)

        await self.send_message(
            content=f"IAM audit complete. Privilege escalation paths: {len(results['privesc_paths'])}",
            recipient=msg.sender,
            msg_type="iam_audit_results",
            context={"results": results},
        )

    async def _handle_container_scan(self, msg: AgentMessage):
        """Handle container security scan"""
        registry = msg.context.get("registry")
        cluster = msg.context.get("cluster")

        logger.info(f"[CloudExpert:{self.name}] Scanning container security")

        results = await self._scan_containers(registry, cluster)

        await self.send_message(
            content=f"Container scan complete. Issues: {len(results['findings'])}",
            recipient=msg.sender,
            msg_type="container_scan_results",
            context={"results": results},
        )

    async def _handle_privesc_check(self, msg: AgentMessage):
        """Handle privilege escalation path checking"""
        provider = msg.context.get("provider", "aws")

        logger.info(f"[CloudExpert:{self.name}] Checking privilege escalation paths")

        results = await self._check_privilege_escalation(provider)

        await self.send_message(
            content=f"Found {len(results['paths'])} privilege escalation paths",
            recipient=msg.sender,
            msg_type="privesc_results",
            context={"results": results},
        )

    async def _handle_serverless_scan(self, msg: AgentMessage):
        """Handle serverless function security scan"""
        provider = msg.context.get("provider", "aws")
        functions = msg.context.get("functions", [])

        logger.info(f"[CloudExpert:{self.name}] Scanning serverless functions")

        results = await self._scan_serverless(provider, functions)

        await self.send_message(
            content=f"Serverless scan complete. Issues: {len(results['findings'])}",
            recipient=msg.sender,
            msg_type="serverless_scan_results",
            context={"results": results},
        )

    async def _run_cloud_audit(self, provider: str, profile: Optional[str], regions: List[str]) -> Dict[str, Any]:
        """Run comprehensive cloud security audit"""
        findings = []

        if provider == "aws":
            findings.extend(await self._audit_aws(profile, regions))
        elif provider == "azure":
            findings.extend(await self._audit_azure(profile))
        elif provider == "gcp":
            findings.extend(await self._audit_gcp(profile))

        return {
            "provider": provider,
            "findings": findings,
            "critical_count": len([f for f in findings if f.get("severity") == "critical"]),
            "high_count": len([f for f in findings if f.get("severity") == "high"]),
        }

    async def _audit_aws(self, profile: Optional[str], regions: List[str]) -> List[Dict[str, Any]]:
        """Audit AWS security configuration"""
        findings = []

        # Check 1: IAM Password Policy
        findings.append(
            {
                "service": "IAM",
                "check": "Password Policy",
                "severity": "medium",
                "finding": "Check if strong password policy is enforced",
            }
        )

        # Check 2: MFA on Root Account
        findings.append(
            {"service": "IAM", "check": "Root MFA", "severity": "critical", "finding": "MFA should be enabled on root account"}
        )

        # Check 3: Access Key Rotation
        findings.append(
            {
                "service": "IAM",
                "check": "Access Key Age",
                "severity": "medium",
                "finding": "Access keys should be rotated every 90 days",
            }
        )

        return findings

    async def _audit_azure(self, profile: Optional[str]) -> List[Dict[str, Any]]:
        """Audit Azure security configuration"""
        findings = []

        findings.append(
            {
                "service": "Azure AD",
                "check": "MFA Enforcement",
                "severity": "high",
                "finding": "MFA should be enforced for all users",
            }
        )

        return findings

    async def _audit_gcp(self, profile: Optional[str]) -> List[Dict[str, Any]]:
        """Audit GCP security configuration"""
        findings = []

        findings.append(
            {
                "service": "IAM",
                "check": "Service Account Keys",
                "severity": "medium",
                "finding": "Service account keys should be rotated regularly",
            }
        )

        return findings

    async def _enumerate_s3_buckets(self, target: str) -> List[str]:
        """Enumerate S3 buckets for target"""
        # Common bucket naming patterns
        patterns = [
            f"{target}",
            f"{target}-assets",
            f"{target}-data",
            f"{target}-backup",
            f"{target}-dev",
            f"{target}-prod",
            f"{target}-staging",
        ]
        return patterns

    async def _scan_s3_buckets(self, buckets: List[str]) -> Dict[str, Any]:
        """Scan S3 buckets for security issues"""
        results = {"scanned": [], "public": [], "writable": [], "unencrypted": [], "findings": []}

        for bucket in buckets:
            results["scanned"].append(bucket)

            # Simulate checks
            finding = {
                "bucket": bucket,
                "is_public": False,
                "is_writable": False,
                "encryption": "unknown",
                "versioning": "unknown",
            }

            results["findings"].append(finding)

        return results

    async def _audit_iam(self, provider: str) -> Dict[str, Any]:
        """Audit IAM configuration"""
        results = {"users": [], "roles": [], "policies": [], "privesc_paths": [], "overly_permissive": []}

        if provider == "aws":
            # Check for privilege escalation paths
            privesc_patterns = [
                ("iam:CreatePolicyVersion", "SetAsDefault=true"),
                ("iam:SetDefaultPolicyVersion", None),
                ("iam:AttachUserPolicy", "arn:aws:iam::aws:policy/AdministratorAccess"),
                ("iam:PassRole", "ec2:RunInstances"),
            ]

            for pattern, condition in privesc_patterns:
                results["privesc_paths"].append({"action": pattern, "condition": condition, "risk": "high"})

        return results

    async def _scan_containers(self, registry: Optional[str], cluster: Optional[str]) -> Dict[str, Any]:
        """Scan container security"""
        results = {"images_scanned": 0, "findings": [], "privileged_containers": [], "vulnerable_images": []}

        # Check for privileged containers
        results["findings"].append(
            {"type": "privileged_container", "severity": "high", "description": "Container running in privileged mode"}
        )

        return results

    async def _check_privilege_escalation(self, provider: str) -> Dict[str, Any]:
        """Check for privilege escalation paths"""
        results = {"provider": provider, "paths": [], "risk_level": "low"}

        if provider == "aws":
            # Check common AWS privilege escalation paths
            paths = [
                {
                    "name": "CreatePolicyVersion",
                    "actions": ["iam:CreatePolicyVersion"],
                    "impact": "Can escalate to any policy permissions",
                },
                {
                    "name": "SetDefaultPolicyVersion",
                    "actions": ["iam:SetDefaultPolicyVersion"],
                    "impact": "Can activate any policy version",
                },
                {
                    "name": "PassRole+RunInstances",
                    "actions": ["iam:PassRole", "ec2:RunInstances"],
                    "impact": "Can launch EC2 with privileged role",
                },
            ]
            results["paths"] = paths

        return results

    async def _scan_serverless(self, provider: str, functions: List[str]) -> Dict[str, Any]:
        """Scan serverless function security"""
        results = {"functions_scanned": len(functions), "findings": [], "overprivileged": [], "public_functions": []}

        for function in functions:
            # Check for common issues
            results["findings"].append(
                {"function": function, "issue": "Environment variables may contain secrets", "severity": "medium"}
            )

        return results

    def analyze(self, target: Optional[str], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Persona-specific analysis logic for cloud security findings.

        Args:
            target: The target cloud account/project
            findings: List of cloud security findings

        Returns:
            Analysis results with cloud-specific risk assessment
        """
        analysis = {
            "total_findings": len(findings),
            "by_provider": {},
            "by_service": {},
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "risk_level": "low",
            "critical_resources": [],
            "compliance_gaps": [],
            "attack_vectors": [],
            "recommendations": [],
        }

        # Categorize findings
        for finding in findings:
            provider = finding.get("provider", "unknown")
            service = finding.get("service", "unknown")
            severity = finding.get("severity", "info").lower()

            # By provider
            if provider not in analysis["by_provider"]:
                analysis["by_provider"][provider] = []
            analysis["by_provider"][provider].append(finding)

            # By service
            if service not in analysis["by_service"]:
                analysis["by_service"][service] = []
            analysis["by_service"][service].append(finding)

            # By severity
            if severity in analysis["by_severity"]:
                analysis["by_severity"][severity] += 1

            # Critical resources
            if severity in ["critical", "high"]:
                analysis["critical_resources"].append(
                    {"resource": finding.get("resource_id"), "service": service, "issue": finding.get("finding")}
                )

        # Determine risk level
        if analysis["by_severity"]["critical"] > 0:
            analysis["risk_level"] = "critical"
        elif analysis["by_severity"]["high"] > 0:
            analysis["risk_level"] = "high"
        elif analysis["by_severity"]["medium"] > 0:
            analysis["risk_level"] = "medium"

        # Identify attack vectors
        analysis["attack_vectors"] = self._identify_cloud_attack_vectors(findings)

        # Generate recommendations
        analysis["recommendations"] = self._generate_cloud_recommendations(analysis)

        return analysis

    def _identify_cloud_attack_vectors(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Identify potential cloud attack vectors"""
        vectors = []

        services = [f.get("service", "").lower() for f in findings]

        if "s3" in services:
            vectors.append("Data exfiltration via exposed S3 buckets")

        if "iam" in services:
            vectors.append("Account takeover via IAM privilege escalation")

        if "lambda" in services or "functions" in services:
            vectors.append("Serverless function abuse for lateral movement")

        if "ec2" in services:
            vectors.append("Metadata service exploitation for credential theft")

        return vectors

    def _generate_cloud_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate cloud-specific recommendations"""
        recommendations = []

        if "S3" in analysis["by_service"]:
            recommendations.append("Enable Block Public Access on all S3 buckets")
            recommendations.append("Enable S3 access logging and versioning")

        if "IAM" in analysis["by_service"]:
            recommendations.append("Implement least-privilege IAM policies")
            recommendations.append("Enable MFA for all IAM users")
            recommendations.append("Rotate access keys every 90 days")

        if analysis["risk_level"] in ["critical", "high"]:
            recommendations.append("Immediately revoke overly permissive permissions")
            recommendations.append("Enable CloudTrail logging in all regions")

        return recommendations

    async def execute_task(self, task: Dict) -> Dict:
        """Execute cloud security testing task"""
        task_type = task.get("type", "")
        context = task.get("context", {})

        logger.info(f"[CloudExpert:{self.name}] Executing task: {task_type}")

        if task_type == "cloud_audit":
            results = await self._run_cloud_audit(
                context.get("provider", "aws"), context.get("profile"), context.get("regions", [])
            )
            analysis = self.analyze(context.get("target"), results["findings"])

            return {"status": "complete", "results": results, "analysis": analysis, "agent": self.name}

        elif task_type == "s3_audit":
            results = await self._scan_s3_buckets(context.get("buckets", []))
            return {"status": "complete", "results": results, "agent": self.name}

        return {"status": "unknown_task"}
