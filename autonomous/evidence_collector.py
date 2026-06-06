#!/usr/bin/env python3
"""
Evidence Collection System for Zen AI Pentest Framework

Automatische Beweissicherung für Exploit-Validierung:
- Screenshots bei erfolgreicher Exploitation
- Video Recording (optional)
- Log Collection für Audit
- Chain of Custody Tracking
- Evidence Hashing für Integrität

FOR AUTHORIZED SECURITY TESTING ONLY

Author: SHAdd0WTAka
Version: 2.0.0
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

# Optional imports
try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available. Screenshot capture disabled.")

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from PIL import Image  # noqa: F401

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger("ZenAI.EvidenceCollector")


@dataclass
class ExploitEvidence:
    """
    Container für Exploit-Beweise.

    Attributes:
        cve_id: CVE Identifier
        target: Target URL/Host
        timestamp: Zeitpunkt der Erfassung
        screenshot: Screenshot als Bytes
        video: Video Aufnahme (optional)
        logs: Ausführungslogs
        success: Ob Exploit erfolgreich war
        risk_level: Risikostufe
        validator_id: ID des Validators
        metadata: Zusätzliche Metadaten
        hashes: SHA256 Hashes für Integrität
    """

    cve_id: str
    target: str
    timestamp: datetime
    screenshot: Optional[bytes] = None
    video: Optional[bytes] = None
    logs: List[str] = field(default_factory=list)
    success: bool = False
    risk_level: str = "unknown"
    validator_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)
    hashes: Dict[str, str] = field(default_factory=dict)
    chain_of_custody: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (with base64 encoding for binary data)."""
        return {
            "cve_id": self.cve_id,
            "target": self.target,
            "timestamp": self.timestamp.isoformat(),
            "screenshot_base64": base64.b64encode(self.screenshot).decode() if self.screenshot else None,
            "video_base64": base64.b64encode(self.video).decode() if self.video else None,
            "logs": self.logs,
            "success": self.success,
            "risk_level": self.risk_level,
            "validator_id": self.validator_id,
            "metadata": self.metadata,
            "hashes": self.hashes,
            "chain_of_custody": self.chain_of_custody,
        }

    def save_to_disk(self, output_dir: str) -> Dict[str, str]:
        """
        Save evidence to disk.

        Args:
            output_dir: Directory to save evidence

        Returns:
            Dictionary of saved file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        saved_files = {}

        # Save metadata
        metadata_path = os.path.join(output_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        saved_files["metadata"] = metadata_path

        # Save screenshot
        if self.screenshot:
            screenshot_path = os.path.join(output_dir, "screenshot.png")
            with open(screenshot_path, "wb") as f:
                f.write(self.screenshot)
            saved_files["screenshot"] = screenshot_path

        # Save video
        if self.video:
            video_path = os.path.join(output_dir, "recording.mp4")
            with open(video_path, "wb") as f:
                f.write(self.video)
            saved_files["video"] = video_path

        # Save logs
        logs_path = os.path.join(output_dir, "execution_logs.txt")
        with open(logs_path, "w") as f:
            f.write("\n".join(self.logs))
        saved_files["logs"] = logs_path

        # Save chain of custody
        custody_path = os.path.join(output_dir, "chain_of_custody.json")
        with open(custody_path, "w") as f:
            json.dump(self.chain_of_custody, f, indent=2)
        saved_files["chain_of_custody"] = custody_path

        return saved_files

    def verify_integrity(self) -> bool:
        """
        Verify evidence integrity using hashes.

        Returns:
            True if integrity check passes
        """
        if not self.hashes:
            return True

        # Verify screenshot hash
        if self.screenshot and "screenshot" in self.hashes:
            current_hash = hashlib.sha256(self.screenshot).hexdigest()
            if current_hash != self.hashes["screenshot"]:
                return False

        # Verify video hash
        if self.video and "video" in self.hashes:
            current_hash = hashlib.sha256(self.video).hexdigest()
            if current_hash != self.hashes["video"]:
                return False

        return True

    def add_chain_of_custody_entry(self, action: str, actor: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Add entry to chain of custody.

        Args:
            action: Action performed
            actor: Who performed the action
            details: Additional details
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "actor": actor,
            "details": details or {},
        }
        self.chain_of_custody.append(entry)


@dataclass
class VideoConfig:
    """Configuration for video recording."""

    enabled: bool = False
    resolution: Tuple[int, int] = (1920, 1080)
    fps: int = 30
    duration_limit: int = 300  # 5 minutes max
    output_format: str = "mp4"  # mp4, webm


class EvidenceCollector:
    """
    Collects and manages evidence from exploit execution.

    Features:
    - Automatic screenshot capture on successful exploitation
    - Optional video recording
    - Complete audit logging
    - Chain of custody tracking
    - Evidence integrity verification

    Usage:
        collector = EvidenceCollector()
        evidence = await collector.collect(
            cve_id="CVE-2024-1234",
            target="http://vulnerable.com",
            success=True,
            logs=["Exploit output..."]
        )
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        video_config: Optional[VideoConfig] = None,
        enable_playwright: bool = True,
        enable_http_capture: bool = True,
    ):
        """
        Initialize EvidenceCollector.

        Args:
            output_dir: Directory for evidence storage
            video_config: Video recording configuration
            enable_playwright: Enable browser automation
            enable_http_capture: Enable HTTP traffic capture
        """
        self.output_dir = output_dir or tempfile.gettempdir()
        self.video_config = video_config or VideoConfig()
        self.enable_playwright = enable_playwright and PLAYWRIGHT_AVAILABLE
        self.enable_http_capture = enable_http_capture and AIOHTTP_AVAILABLE

        self._evidence_counter = 0
        self._audit_log: List[Dict[str, Any]] = []

        # Video recording state
        self._recording = False
        self._video_buffer: List[bytes] = []

        logger.info(f"EvidenceCollector initialized (playwright={self.enable_playwright})")

    async def collect(
        self,
        cve_id: str,
        target: str,
        success: bool,
        logs: List[str],
        risk_level: str = "unknown",
        capture_screenshot: bool = True,
        capture_video: bool = False,
        http_responses: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExploitEvidence:
        """
        Collect evidence from exploit execution.

        Args:
            cve_id: CVE identifier
            target: Target URL/Host
            success: Whether exploit was successful
            logs: Execution logs
            risk_level: Risk level of exploit
            capture_screenshot: Capture screenshot
            capture_video: Capture video
            http_responses: HTTP response data
            metadata: Additional metadata

        Returns:
            ExploitEvidence object
        """
        timestamp = datetime.now(timezone.utc)
        validator_id = str(uuid.uuid4())[:8]

        # Initialize chain of custody
        chain_of_custody = [
            {
                "timestamp": timestamp.isoformat(),
                "action": "evidence_collection_started",
                "actor": "EvidenceCollector",
                "details": {"cve_id": cve_id, "target": target},
            }
        ]

        screenshot = None
        video = None

        try:
            # Capture screenshot for successful web exploits
            if success and capture_screenshot and self.enable_playwright:
                screenshot = await self._capture_screenshot(target)
                chain_of_custody.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action": "screenshot_captured",
                        "actor": "EvidenceCollector",
                        "details": {"size": len(screenshot) if screenshot else 0},
                    }
                )

            # Capture video if enabled
            if capture_video and self.video_config.enabled:
                video = await self._capture_video(target)
                chain_of_custody.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action": "video_captured",
                        "actor": "EvidenceCollector",
                        "details": {"size": len(video) if video else 0},
                    }
                )

            # Compile metadata
            full_metadata = {
                "user_agent": "ZenAI-ExploitValidator/2.0",
                "source_ip": await self._get_source_ip(),
                "http_responses": http_responses or [],
                **(metadata or {}),
            }

            # Compute hashes
            hashes = {}
            if screenshot:
                hashes["screenshot"] = hashlib.sha256(screenshot).hexdigest()
            if video:
                hashes["video"] = hashlib.sha256(video).hexdigest()

            evidence = ExploitEvidence(
                cve_id=cve_id,
                target=target,
                timestamp=timestamp,
                screenshot=screenshot,
                video=video,
                logs=logs,
                success=success,
                risk_level=risk_level,
                validator_id=validator_id,
                metadata=full_metadata,
                hashes=hashes,
                chain_of_custody=chain_of_custody,
            )

            self._audit(
                "evidence_collected",
                {
                    "cve_id": cve_id,
                    "target": target,
                    "success": success,
                    "has_screenshot": screenshot is not None,
                    "has_video": video is not None,
                },
            )

            return evidence

        except Exception as e:
            logger.exception("Evidence collection failed")
            # Return partial evidence
            return ExploitEvidence(
                cve_id=cve_id,
                target=target,
                timestamp=timestamp,
                logs=logs + [f"Evidence collection error: {str(e)}"],
                success=success,
                risk_level=risk_level,
                validator_id=validator_id,
                metadata={"error": str(e)},
                chain_of_custody=chain_of_custody,
            )

    async def collect_http_evidence(self, target: str, payloads: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Collect HTTP response evidence.

        Args:
            target: Target URL
            payloads: List of payloads to test

        Returns:
            List of HTTP response data
        """
        if not self.enable_http_capture:
            return []

        responses = []

        try:
            # Ensure URL has scheme
            if not target.startswith(("http://", "https://")):
                target = f"http://{target}"

            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Test base URL
                try:
                    async with session.get(target, ssl=False) as response:
                        body_text = await response.text()
                        response_data = {
                            "url": str(response.url),
                            "status": response.status,
                            "headers": dict(response.headers),
                            "body_preview": body_text[:5000],
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "type": "baseline",
                        }
                        responses.append(response_data)
                except Exception as e:
                    logger.warning(f"HTTP baseline capture failed: {e}")

                # Test with payloads if provided
                if payloads:
                    parsed = urlparse(target)
                    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

                    for payload in payloads[:3]:  # Limit to 3 payloads
                        try:
                            # Try as query parameter
                            test_url = f"{base_url}?test={payload}"
                            async with session.get(test_url, ssl=False) as response:
                                body_text = await response.text()
                                responses.append(
                                    {
                                        "url": str(response.url),
                                        "status": response.status,
                                        "payload": payload,
                                        "body_preview": body_text[:2000],
                                        "timestamp": datetime.now(timezone.utc).isoformat(),
                                        "type": "payload_test",
                                    }
                                )
                        except Exception as e:
                            logger.debug(f"Payload test failed: {e}")

        except Exception as e:
            logger.warning(f"HTTP evidence collection failed: {e}")

        return responses

    async def capture_screenshot(self, target: str, full_page: bool = True, wait_for_load: bool = True) -> Optional[bytes]:
        """
        Capture screenshot of target.

        Args:
            target: Target URL
            full_page: Capture full page
            wait_for_load: Wait for page load

        Returns:
            Screenshot as bytes
        """
        if not self.enable_playwright:
            return None

        return await self._capture_screenshot(target, full_page, wait_for_load)

    async def start_video_recording(self, target: str) -> None:
        """
        Start video recording (not implemented - requires external tools).

        Args:
            target: Target URL to record
        """
        if not self.video_config.enabled:
            return

        logger.info(f"Video recording started for {target}")
        self._recording = True
        self._video_buffer = []

        # Note: Full video recording would require screen capture tools
        # This is a placeholder for the infrastructure

    async def stop_video_recording(self) -> Optional[bytes]:
        """
        Stop video recording.

        Returns:
            Video data as bytes
        """
        self._recording = False

        # Placeholder - would combine frames into video
        if self._video_buffer:
            return b"".join(self._video_buffer)

        return None

    def save_evidence_package(self, evidence: ExploitEvidence, case_id: str, output_dir: Optional[str] = None) -> str:
        """
        Save complete evidence package.

        Args:
            evidence: Evidence to save
            case_id: Case identifier
            output_dir: Output directory

        Returns:
            Path to evidence package
        """
        if output_dir is None:
            output_dir = os.path.join(self.output_dir, f"evidence_{case_id}_{evidence.validator_id}")

        evidence_dir = os.path.join(
            output_dir, evidence.cve_id.replace("-", "_"), datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        )

        os.makedirs(evidence_dir, exist_ok=True)

        # Save evidence files
        saved_files = evidence.save_to_disk(evidence_dir)

        # Create manifest
        manifest = {
            "case_id": case_id,
            "evidence_id": evidence.validator_id,
            "cve_id": evidence.cve_id,
            "target": evidence.target,
            "timestamp": evidence.timestamp.isoformat(),
            "files": saved_files,
            "hashes": evidence.hashes,
            "integrity_verified": evidence.verify_integrity(),
        }

        manifest_path = os.path.join(evidence_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Evidence package saved to {evidence_dir}")
        return evidence_dir

    # Private methods

    async def _capture_screenshot(self, target: str, full_page: bool = True, wait_for_load: bool = True) -> Optional[bytes]:
        """Capture screenshot using Playwright."""
        if not PLAYWRIGHT_AVAILABLE:
            return None

        try:
            # Ensure URL has scheme
            if not target.startswith(("http://", "https://")):
                target = f"http://{target}"

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)

                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080}, user_agent="ZenAI-ExploitValidator/2.0"
                )

                page = await context.new_page()

                try:
                    # Navigate with timeout
                    await page.goto(target, wait_until="networkidle" if wait_for_load else "load", timeout=30000)

                    # Wait a moment for any dynamic content
                    await asyncio.sleep(2)

                    # Capture screenshot
                    screenshot = await page.screenshot(full_page=full_page, type="png")

                    # Also capture page content
                    await page.content()

                    await browser.close()

                    logger.debug(f"Screenshot captured: {len(screenshot)} bytes")
                    return screenshot

                except Exception as e:
                    logger.warning(f"Page navigation failed: {e}")
                    await browser.close()
                    return None

        except Exception as e:
            logger.warning(f"Screenshot capture failed: {e}")
            return None

    async def _capture_video(self, target: str) -> Optional[bytes]:
        """
        Capture video of exploitation.

        Note: This is a placeholder. Full implementation would require
        tools like FFmpeg for screen recording.

        Args:
            target: Target URL

        Returns:
            Video data or None
        """
        # Video recording requires external tools
        # For now, return None
        logger.debug("Video recording not implemented")
        return None

    async def _get_source_ip(self) -> str:
        """Get source IP address."""
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection("8.8.8.8", 53), timeout=5)
            sock = writer.get_extra_info("socket")
            ip = sock.getsockname()[0]
            writer.close()
            await writer.wait_closed()
            return ip
        except Exception:
            return "unknown"

    def _audit(self, action: str, details: Dict[str, Any]) -> None:
        """Add audit log entry."""
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "action": action, "details": details}
        self._audit_log.append(entry)
        logger.info(f"[AUDIT] {action}: {details}")


class EvidenceArchive:
    """
    Archive for long-term evidence storage.

    Manages evidence retention, compression, and retrieval.
    """

    def __init__(self, archive_dir: str, retention_days: int = 365):
        """
        Initialize archive.

        Args:
            archive_dir: Directory for archived evidence
            retention_days: Days to retain evidence
        """
        self.archive_dir = archive_dir
        self.retention_days = retention_days
        os.makedirs(archive_dir, exist_ok=True)

    async def archive_evidence(self, evidence: ExploitEvidence, case_id: str) -> str:
        """
        Archive evidence package.

        Args:
            evidence: Evidence to archive
            case_id: Case identifier

        Returns:
            Path to archived package
        """
        import zipfile

        # Create temporary directory with evidence
        temp_dir = tempfile.mkdtemp()

        try:
            evidence_dir = os.path.join(temp_dir, f"{case_id}_{evidence.cve_id}_{evidence.validator_id}")
            os.makedirs(evidence_dir, exist_ok=True)

            # Save evidence
            evidence.save_to_disk(evidence_dir)

            # Create zip archive
            archive_name = f"{case_id}_{evidence.cve_id}_{int(datetime.now(timezone.utc).timestamp())}.zip"
            archive_path = os.path.join(self.archive_dir, archive_name)

            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(evidence_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, evidence_dir)
                        zf.write(file_path, arcname)

            logger.info(f"Evidence archived: {archive_path}")
            return archive_path

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def list_archives(self, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List archived evidence.

        Args:
            case_id: Filter by case ID

        Returns:
            List of archive metadata
        """
        archives = []

        for filename in os.listdir(self.archive_dir):
            if not filename.endswith(".zip"):
                continue

            if case_id and not filename.startswith(case_id):
                continue

            filepath = os.path.join(self.archive_dir, filename)
            stat = os.stat(filepath)

            archives.append(
                {
                    "filename": filename,
                    "path": filepath,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )

        return sorted(archives, key=lambda x: x["created"], reverse=True)


import uuid

# Export public API
__all__ = ["EvidenceCollector", "EvidenceArchive", "ExploitEvidence", "VideoConfig"]
