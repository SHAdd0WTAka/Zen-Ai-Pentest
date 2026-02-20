#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Scanner für Zen-Ai-Pentest
================================

Erweiterte Cloud-Scanning-Funktionalität mit ScoutSuite-Integration.
Bietet Multi-Cloud-Support, kontinuierliches Monitoring und
automatisierte Compliance-Checks.

Autor: Zen-Ai-Pentest Team
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Importiere ScoutSuite Integration
from scoutsuite_integration import (
    CloudProvider,
    ComplianceFramework,
    ScoutSuiteConfig,
    ScoutSuiteFinding,
    ScoutSuiteIntegration,
    ScoutSuiteReport,
)

# Logging Konfiguration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("cloud_scanner")


class ScanType(Enum):
    """Arten von Cloud-Scans"""

    FULL = "full"  # Vollständiger Scan
    QUICK = "quick"  # Schneller Scan (kritische Services)
    COMPLIANCE = "compliance"  # Compliance-fokussierter Scan
    CUSTOM = "custom"  # Benutzerdefinierter Scan
    DELTA = "delta"  # Delta-Scan (Änderungen seit letztem Scan)


class ScanSchedule(Enum):
    """Scan-Zeitpläne"""

    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class CloudAccount:
    """Repräsentiert ein Cloud-Konto"""

    id: str
    name: str
    provider: CloudProvider
    credentials: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_scan: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider.value,
            "metadata": self.metadata,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
        }


@dataclass
class ScheduledScan:
    """Geplanter Scan"""

    id: str
    account_id: str
    scan_type: ScanType
    schedule: ScanSchedule
    config: ScoutSuiteConfig
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "scan_type": self.scan_type.value,
            "schedule": self.schedule.value,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
        }


@dataclass
class ScanResult:
    """Ergebnis eines Cloud-Scans"""

    scan_id: str
    account_id: str
    scan_type: ScanType
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "pending"
    report: Optional[ScoutSuiteReport] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "account_id": self.account_id,
            "scan_type": self.scan_type.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class FindingDelta:
    """Delta zwischen zwei Scans"""

    new_findings: List[ScoutSuiteFinding] = field(default_factory=list)
    resolved_findings: List[ScoutSuiteFinding] = field(default_factory=list)
    changed_findings: List[Dict[str, Any]] = field(default_factory=list)
    unchanged_findings: List[ScoutSuiteFinding] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "new_findings": [f.to_dict() for f in self.new_findings],
            "resolved_findings": [f.to_dict() for f in self.resolved_findings],
            "changed_findings": self.changed_findings,
            "unchanged_findings_count": len(self.unchanged_findings),
        }


class CloudAccountManager:
    """Verwaltet Cloud-Konten"""

    def __init__(self, storage_path: str = "./cloud_accounts.json"):
        self.storage_path = Path(storage_path)
        self.accounts: Dict[str, CloudAccount] = {}
        self._load_accounts()

    def _load_accounts(self):
        """Lädt Konten aus Speicher"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for account_data in data.get("accounts", []):
                    account = CloudAccount(
                        id=account_data["id"],
                        name=account_data["name"],
                        provider=CloudProvider(account_data["provider"]),
                        metadata=account_data.get("metadata", {}),
                        enabled=account_data.get("enabled", True),
                        created_at=datetime.fromisoformat(account_data["created_at"]),
                        last_scan=datetime.fromisoformat(account_data["last_scan"]) if account_data.get("last_scan") else None,
                    )
                    self.accounts[account.id] = account

                logger.info(f"{len(self.accounts)} Cloud-Konten geladen")
            except Exception as e:
                logger.error(f"Fehler beim Laden der Konten: {e}")

    def _save_accounts(self):
        """Speichert Konten"""
        try:
            data = {
                "accounts": [account.to_dict() for account in self.accounts.values()],
                "updated_at": datetime.now().isoformat(),
            }

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.info("Cloud-Konten gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konten: {e}")

    def add_account(
        self, name: str, provider: CloudProvider, credentials: Dict[str, str], metadata: Optional[Dict[str, Any]] = None
    ) -> CloudAccount:
        """Fügt ein neues Cloud-Konto hinzu"""
        account_id = hashlib.md5(f"{provider.value}:{name}:{datetime.now()}".encode()).hexdigest()[:12]

        account = CloudAccount(id=account_id, name=name, provider=provider, credentials=credentials, metadata=metadata or {})

        self.accounts[account_id] = account
        self._save_accounts()

        logger.info(f"Cloud-Konto hinzugefügt: {name} ({provider.value})")
        return account

    def get_account(self, account_id: str) -> Optional[CloudAccount]:
        """Holt ein Konto nach ID"""
        return self.accounts.get(account_id)

    def get_accounts_by_provider(self, provider: CloudProvider) -> List[CloudAccount]:
        """Holt alle Konten eines Providers"""
        return [account for account in self.accounts.values() if account.provider == provider and account.enabled]

    def update_account(
        self,
        account_id: str,
        name: Optional[str] = None,
        credentials: Optional[Dict[str, str]] = None,
        enabled: Optional[bool] = None,
    ) -> bool:
        """Aktualisiert ein Konto"""
        account = self.accounts.get(account_id)
        if not account:
            return False

        if name:
            account.name = name
        if credentials:
            account.credentials = credentials
        if enabled is not None:
            account.enabled = enabled

        self._save_accounts()
        logger.info(f"Cloud-Konto aktualisiert: {account_id}")
        return True

    def delete_account(self, account_id: str) -> bool:
        """Löscht ein Konto"""
        if account_id in self.accounts:
            del self.accounts[account_id]
            self._save_accounts()
            logger.info(f"Cloud-Konto gelöscht: {account_id}")
            return True
        return False

    def list_accounts(self) -> List[CloudAccount]:
        """Listet alle Konten"""
        return list(self.accounts.values())


class CloudScanner:
    """
    Hauptklasse für Cloud-Scanning mit ScoutSuite
    """

    # Vordefinierte Service-Listen für verschiedene Scan-Typen
    QUICK_SCAN_SERVICES = {
        CloudProvider.AWS: ["iam", "s3", "ec2", "kms", "cloudtrail"],
        CloudProvider.AZURE: ["aad", "storage", "sql", "keyvault", "monitor"],
        CloudProvider.GCP: ["iam", "storage", "compute", "kms", "logging"],
    }

    COMPLIANCE_SCAN_SERVICES = {
        CloudProvider.AWS: ["iam", "s3", "ec2", "rds", "cloudtrail", "config", "kms"],
        CloudProvider.AZURE: ["aad", "storage", "sql", "keyvault", "securitycenter"],
        CloudProvider.GCP: ["iam", "storage", "compute", "kms", "logging", "monitoring"],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.scoutsuite = ScoutSuiteIntegration(config)
        self.account_manager = CloudAccountManager(self.config.get("accounts_file", "./cloud_accounts.json"))

        # Scan-Verwaltung
        self.scheduled_scans: Dict[str, ScheduledScan] = {}
        self.scan_results: Dict[str, ScanResult] = {}
        self.scan_history: List[str] = []

        # Monitoring
        self.monitoring_enabled = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # Callbacks
        self.scan_callbacks: List[Callable[[ScanResult], None]] = []

        # Executor für parallele Scans
        self.executor = ThreadPoolExecutor(max_workers=5)

    def create_scan_config(
        self, account: CloudAccount, scan_type: ScanType = ScanType.FULL, custom_services: Optional[List[str]] = None
    ) -> ScoutSuiteConfig:
        """Erstellt eine Scan-Konfiguration basierend auf Scan-Typ"""

        if scan_type == ScanType.QUICK:
            services = self.QUICK_SCAN_SERVICES.get(account.provider, [])
        elif scan_type == ScanType.COMPLIANCE:
            services = self.COMPLIANCE_SCAN_SERVICES.get(account.provider, [])
        elif scan_type == ScanType.CUSTOM and custom_services:
            services = custom_services
        else:
            services = []  # Full scan - alle Services

        config = ScoutSuiteConfig(
            provider=account.provider,
            services=services,
            output_dir=self.config.get("output_dir", "./scoutsuite_reports"),
            report_name=f"scan_{account.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )

        return config

    async def scan_account(
        self,
        account_id: str,
        scan_type: ScanType = ScanType.FULL,
        custom_services: Optional[List[str]] = None,
        progress_callback: Optional[Callable] = None,
    ) -> ScanResult:
        """Scannt ein Cloud-Konto"""

        account = self.account_manager.get_account(account_id)
        if not account:
            raise ValueError(f"Konto nicht gefunden: {account_id}")

        if not account.enabled:
            raise ValueError(f"Konto ist deaktiviert: {account_id}")

        # Erstelle Scan-Result
        scan_id = f"scan_{account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = ScanResult(scan_id=scan_id, account_id=account_id, scan_type=scan_type, start_time=datetime.now())
        self.scan_results[scan_id] = result

        try:
            # Richte Credentials ein
            self._setup_credentials(account)

            # Erstelle Scan-Konfiguration
            config = self.create_scan_config(account, scan_type, custom_services)

            # Führe Scan durch
            report = await self.scoutsuite.scan(config, progress_callback)

            # Aktualisiere Ergebnis
            result.report = report
            result.status = report.status
            result.end_time = datetime.now()

            # Aktualisiere Konto
            account.last_scan = datetime.now()
            self.account_manager._save_accounts()

            # Speichere in Historie
            self.scan_history.append(scan_id)

            # Benachrichtige Callbacks
            for callback in self.scan_callbacks:
                try:
                    callback(result)
                except Exception as e:
                    logger.warning(f"Callback-Fehler: {e}")

            logger.info(f"Scan abgeschlossen: {scan_id} - {len(report.findings)} Findings")

        except Exception as e:
            logger.error(f"Scan fehlgeschlagen: {e}")
            result.status = "error"
            result.error_message = str(e)
            result.end_time = datetime.now()

        return result

    def _setup_credentials(self, account: CloudAccount):
        """Richtet Credentials für ein Konto ein"""
        creds = account.credentials

        if account.provider == CloudProvider.AWS:
            self.scoutsuite.credential_manager.setup_aws_credentials(
                access_key_id=creds.get("aws_access_key_id", ""),
                secret_access_key=creds.get("aws_secret_access_key", ""),
                session_token=creds.get("aws_session_token"),
                region=creds.get("region", "us-east-1"),
                profile_name=creds.get("profile", "default"),
            )

        elif account.provider == CloudProvider.AZURE:
            self.scoutsuite.credential_manager.setup_azure_credentials(
                tenant_id=creds.get("tenant_id", ""),
                client_id=creds.get("client_id", ""),
                client_secret=creds.get("client_secret", ""),
                subscription_id=creds.get("subscription_id"),
            )

        elif account.provider == CloudProvider.GCP:
            self.scoutsuite.credential_manager.setup_gcp_credentials(
                service_account_key_path=creds.get("service_account_key_path", ""), project_id=creds.get("project_id")
            )

    async def scan_multiple_accounts(
        self, account_ids: List[str], scan_type: ScanType = ScanType.FULL, parallel: bool = True
    ) -> List[ScanResult]:
        """Scannt mehrere Konten"""

        if parallel:
            # Parallele Scans
            tasks = [self.scan_account(account_id, scan_type) for account_id in account_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filtere erfolgreiche Ergebnisse
            return [r for r in results if isinstance(r, ScanResult)]
        else:
            # Sequentielle Scans
            results = []
            for account_id in account_ids:
                result = await self.scan_account(account_id, scan_type)
                results.append(result)
            return results

    def scan_all_accounts(self, provider: Optional[CloudProvider] = None, scan_type: ScanType = ScanType.FULL) -> List[str]:
        """Startet Scans für alle aktivierten Konten"""

        accounts = self.account_manager.list_accounts()

        if provider:
            accounts = [a for a in accounts if a.provider == provider]

        accounts = [a for a in accounts if a.enabled]

        scan_ids = []
        for account in accounts:
            # Async-Scan starten
            asyncio.create_task(self.scan_account(account.id, scan_type))
            scan_ids.append(f"scan_{account.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        logger.info(f"Scans für {len(accounts)} Konten gestartet")
        return scan_ids

    def calculate_delta(self, current_report: ScoutSuiteReport, previous_report: ScoutSuiteReport) -> FindingDelta:
        """Berechnet Delta zwischen zwei Reports"""

        current_findings = {f.id: f for f in current_report.findings}
        previous_findings = {f.id: f for f in previous_report.findings}

        delta = FindingDelta()

        # Neue Findings
        for finding_id, finding in current_findings.items():
            if finding_id not in previous_findings:
                delta.new_findings.append(finding)

        # Gelöste Findings
        for finding_id, finding in previous_findings.items():
            if finding_id not in current_findings:
                delta.resolved_findings.append(finding)

        # Unveränderte Findings
        for finding_id in current_findings:
            if finding_id in previous_findings:
                delta.unchanged_findings.append(current_findings[finding_id])

        return delta

    def schedule_scan(
        self, account_id: str, scan_type: ScanType, schedule: ScanSchedule, custom_services: Optional[List[str]] = None
    ) -> ScheduledScan:
        """Plant einen wiederkehrenden Scan"""

        scan_id = hashlib.md5(f"{account_id}:{scan_type.value}:{schedule.value}:{datetime.now()}".encode()).hexdigest()[:12]

        account = self.account_manager.get_account(account_id)
        if not account:
            raise ValueError(f"Konto nicht gefunden: {account_id}")

        config = self.create_scan_config(account, scan_type, custom_services)

        scheduled = ScheduledScan(id=scan_id, account_id=account_id, scan_type=scan_type, schedule=schedule, config=config)

        self.scheduled_scans[scan_id] = scheduled

        # Plane nächste Ausführung
        self._schedule_next_run(scheduled)

        logger.info(f"Scan geplant: {scan_id} ({schedule.value})")
        return scheduled

    def _schedule_next_run(self, scheduled: ScheduledScan):
        """Plant die nächste Ausführung"""
        now = datetime.now()

        if scheduled.schedule == ScanSchedule.HOURLY:
            scheduled.next_run = now + timedelta(hours=1)
        elif scheduled.schedule == ScanSchedule.DAILY:
            scheduled.next_run = now + timedelta(days=1)
        elif scheduled.schedule == ScanSchedule.WEEKLY:
            scheduled.next_run = now + timedelta(weeks=1)
        elif scheduled.schedule == ScanSchedule.MONTHLY:
            scheduled.next_run = now + timedelta(days=30)

    def start_monitoring(self):
        """Startet kontinuierliches Monitoring"""
        if self.monitoring_enabled:
            logger.warning("Monitoring bereits aktiv")
            return

        self.monitoring_enabled = True

        def monitor_loop():
            while self.monitoring_enabled:
                now = datetime.now()

                # Prüfe geplante Scans
                for scan_id, scheduled in self.scheduled_scans.items():
                    if not scheduled.enabled:
                        continue

                    if scheduled.next_run and scheduled.next_run <= now:
                        # Führe Scan durch
                        asyncio.create_task(self.scan_account(scheduled.account_id, scheduled.scan_type))

                        scheduled.last_run = now
                        scheduled.run_count += 1
                        self._schedule_next_run(scheduled)

                time.sleep(60)  # Prüfe jede Minute

        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info("Monitoring gestartet")

    def stop_monitoring(self):
        """Stoppt Monitoring"""
        self.monitoring_enabled = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Monitoring gestoppt")

    def add_scan_callback(self, callback: Callable[[ScanResult], None]):
        """Fügt einen Callback für Scan-Ergebnisse hinzu"""
        self.scan_callbacks.append(callback)

    def get_scan_result(self, scan_id: str) -> Optional[ScanResult]:
        """Holt ein Scan-Ergebnis"""
        return self.scan_results.get(scan_id)

    def get_scan_history(self, account_id: Optional[str] = None, limit: int = 100) -> List[ScanResult]:
        """Holt Scan-Historie"""
        results = list(self.scan_results.values())

        if account_id:
            results = [r for r in results if r.account_id == account_id]

        # Sortiere nach Startzeit (neueste zuerst)
        results.sort(key=lambda r: r.start_time, reverse=True)

        return results[:limit]

    def export_scan_report(self, scan_id: str, output_path: str, format: str = "json") -> bool:
        """Exportiert einen Scan-Report"""
        result = self.scan_results.get(scan_id)
        if not result or not result.report:
            return False

        try:
            if format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result.report.to_dict(), f, indent=2)

            elif format == "csv":
                self.scoutsuite.export_findings_to_csv(result.report, output_path)

            elif format == "sarif":
                self.scoutsuite.report_parser.export_to_sarif(result.report, output_path)

            logger.info(f"Report exportiert: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Export: {e}")
            return False

    def generate_compliance_report(self, scan_id: str, frameworks: List[ComplianceFramework], output_path: str) -> bool:
        """Generiert einen Compliance-Report"""
        result = self.scan_results.get(scan_id)
        if not result or not result.report:
            return False

        try:
            compliance_results = self.scoutsuite.compliance_checker.check_compliance(result.report, frameworks)

            self.scoutsuite.compliance_checker.generate_compliance_report(compliance_results, output_path)

            return True

        except Exception as e:
            logger.error(f"Fehler beim Compliance-Report: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Scan-Statistiken zurück"""
        total_scans = len(self.scan_results)
        successful_scans = sum(1 for r in self.scan_results.values() if r.status == "completed")
        failed_scans = sum(1 for r in self.scan_results.values() if r.status == "error")

        findings_by_severity: Dict[str, int] = {}
        for result in self.scan_results.values():
            if result.report:
                for finding in result.report.findings:
                    severity = finding.severity
                    findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1

        return {
            "total_scans": total_scans,
            "successful_scans": successful_scans,
            "failed_scans": failed_scans,
            "success_rate": (successful_scans / total_scans * 100) if total_scans > 0 else 0,
            "findings_by_severity": findings_by_severity,
            "total_findings": sum(findings_by_severity.values()),
            "active_accounts": len([a for a in self.account_manager.list_accounts() if a.enabled]),
            "scheduled_scans": len(self.scheduled_scans),
        }

    def cleanup_old_reports(self, days: int = 30):
        """Löscht alte Reports"""
        cutoff = datetime.now() - timedelta(days=days)

        to_remove = [scan_id for scan_id, result in self.scan_results.items() if result.start_time < cutoff]

        for scan_id in to_remove:
            del self.scan_results[scan_id]

        logger.info(f"{len(to_remove)} alte Reports gelöscht")


# API-Endpunkte für Integration
class CloudScannerAPI:
    """API-Schnittstelle für Cloud Scanner"""

    def __init__(self, scanner: CloudScanner):
        self.scanner = scanner

    async def handle_scan_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet einen Scan-Request"""
        account_id = request.get("account_id")
        scan_type = ScanType(request.get("scan_type", "full"))

        if not account_id:
            return {"error": "account_id erforderlich"}

        try:
            result = await self.scanner.scan_account(account_id, scan_type)
            return {
                "scan_id": result.scan_id,
                "status": result.status,
                "findings_count": len(result.report.findings) if result.report else 0,
            }
        except Exception as e:
            return {"error": str(e)}

    def handle_add_account(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Fügt ein Konto hinzu"""
        try:
            account = self.scanner.account_manager.add_account(
                name=request["name"],
                provider=CloudProvider(request["provider"]),
                credentials=request["credentials"],
                metadata=request.get("metadata", {}),
            )
            return {"account_id": account.id, "status": "created"}
        except Exception as e:
            return {"error": str(e)}

    def handle_get_results(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Holt Scan-Ergebnisse"""
        scan_id = request.get("scan_id")

        if scan_id:
            result = self.scanner.get_scan_result(scan_id)
            if result:
                return result.to_dict()
            return {"error": "Scan nicht gefunden"}

        # Liste alle Ergebnisse
        account_id = request.get("account_id")
        limit = request.get("limit", 100)

        results = self.scanner.get_scan_history(account_id, limit)
        return {"results": [r.to_dict() for r in results], "total": len(results)}

    def handle_get_statistics(self) -> Dict[str, Any]:
        """Holt Statistiken"""
        return self.scanner.get_statistics()


# Beispiel-Nutzung und Demo
async def demo():
    """Demo der Cloud Scanner Funktionalität"""

    print("=" * 60)
    print("Zen-Ai-Pentest Cloud Scanner Demo")
    print("=" * 60)

    # Initialisiere Scanner
    scanner = CloudScanner({"output_dir": "./demo_reports", "accounts_file": "./demo_accounts.json"})

    # API initialisieren
    api = CloudScannerAPI(scanner)

    print("\n1. Cloud-Konto hinzufügen (Beispiel)")
    print("-" * 40)

    # Beispiel: AWS-Konto hinzufügen
    # In Produktion: Credentials aus Umgebungsvariablen oder Secrets Manager
    account_response = api.handle_add_account(
        {
            "name": "Demo AWS Account",
            "provider": "aws",
            "credentials": {
                "aws_access_key_id": "AKIA...",
                "aws_secret_access_key": "...",
                "region": "us-east-1",
                "profile": "default",
            },
            "metadata": {"environment": "production", "team": "security"},
        }
    )
    print(f"Konto hinzugefügt: {account_response}")

    # Beispiel: Azure-Konto hinzufügen
    azure_response = api.handle_add_account(
        {
            "name": "Demo Azure Subscription",
            "provider": "azure",
            "credentials": {"tenant_id": "...", "client_id": "...", "client_secret": "...", "subscription_id": "..."},
        }
    )
    print(f"Azure-Konto hinzugefügt: {azure_response}")

    print("\n2. Konten auflisten")
    print("-" * 40)
    accounts = scanner.account_manager.list_accounts()
    for account in accounts:
        print(f"  - {account.name} ({account.provider.value}): {account.id}")

    print("\n3. Statistiken anzeigen")
    print("-" * 40)
    stats = api.handle_get_statistics()
    print(json.dumps(stats, indent=2))

    print("\n4. Scan-Konfigurationen")
    print("-" * 40)

    for account in accounts:
        for scan_type in ScanType:
            config = scanner.create_scan_config(account, scan_type)
            print(f"\n{account.provider.value.upper()} - {scan_type.value}:")
            print(f"  Services: {config.services if config.services else 'ALL'}")

    print("\n5. Compliance-Frameworks")
    print("-" * 40)
    frameworks = list(ComplianceFramework)
    for fw in frameworks:
        print(f"  - {fw.value.upper()}")

    print("\n" + "=" * 60)
    print("Demo abgeschlossen!")
    print("=" * 60)

    return scanner


if __name__ == "__main__":
    # Führe Demo aus
    # asyncio.run(demo())

    print("""
Cloud Scanner für Zen-Ai-Pentest
================================

Verfügbare Komponenten:
- CloudScanner: Hauptklasse für Cloud-Scanning
- CloudAccountManager: Verwaltung von Cloud-Konten
- CloudScannerAPI: API-Schnittstelle

Nutzung:
    scanner = CloudScanner()

    # Konto hinzufügen
    account = scanner.account_manager.add_account(
        name="AWS Production",
        provider=CloudProvider.AWS,
        credentials={...}
    )

    # Scan durchführen
    result = await scanner.scan_account(account.id, ScanType.QUICK)

    # Compliance-Check
    scanner.generate_compliance_report(
        result.scan_id,
        [ComplianceFramework.CIS, ComplianceFramework.NIST],
        "compliance_report.json"
    )

Führe 'asyncio.run(demo())' für eine vollständige Demo aus.
""")
