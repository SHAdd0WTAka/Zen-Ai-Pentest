"""
Email Notification Module for Zen-AI-Pentest
============================================

Sends automated email reports after scan completion.
Supports SMTP, TLS/SSL, and HTML/text formats.

Usage:
    from notifications.email_sender import EmailReporter

    reporter = EmailReporter()
    reporter.send_scan_report(
        to_email="admin@company.com",
        scan_results=results,
        report_path="/path/to/report.pdf"
    )
"""

import logging
import os
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Email configuration settings"""

    smtp_host: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True
    from_email: Optional[str] = None
    from_name: str = "Zen-AI-Pentest"

    @classmethod
    def from_env(cls) -> "EmailConfig":
        """Create config from environment variables"""
        return cls(
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASS", ""),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            from_email=os.getenv("FROM_EMAIL", os.getenv("SMTP_USER", "")),
            from_name=os.getenv("FROM_NAME", "Zen-AI-Pentest"),
        )

    def validate(self) -> bool:
        """Validate configuration"""
        return all(
            [
                self.smtp_host,
                self.smtp_port,
                self.username,
                self.password,
            ]
        )


class EmailReporter:
    """
    Automated email reporter for pentest scans.

    Sends formatted HTML emails with scan summaries and
    optionally attaches full reports.
    """

    def __init__(self, config: Optional[EmailConfig] = None):
        """
        Initialize email reporter.

        Args:
            config: Email configuration. If None, loads from environment.
        """
        self.config = config or EmailConfig.from_env()
        if not self.config.validate():
            logger.warning("Email config incomplete - emails will fail")

    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create SMTP connection"""
        if self.config.use_tls:
            server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port)

        server.login(self.config.username, self.config.password)
        return server

    def _build_html_report(
        self,
        scan_target: str,
        findings: List[Dict],
        duration: float,
        scan_id: str,
    ) -> str:
        """Build HTML email body"""

        # Count severities
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        for finding in findings:
            sev = finding.get("severity", "info").lower()
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        total = len(findings)
        critical = severity_counts.get("critical", 0)

        # Determine overall status
        if critical > 0:
            status = "🔴 CRITICAL ISSUES FOUND"
            status_color = "#dc3545"
        elif severity_counts.get("high", 0) > 0:
            status = "🟠 HIGH SEVERITY ISSUES"
            status_color = "#fd7e14"
        elif total > 0:
            status = "🟡 ISSUES FOUND"
            status_color = "#ffc107"
        else:
            status = "🟢 NO ISSUES FOUND"
            status_color = "#28a745"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
                .header {{ text-align: center; border-bottom: 3px solid {status_color}; padding-bottom: 20px; margin-bottom: 30px; }}
                .status {{ color: {status_color}; font-size: 24px; font-weight: bold; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ text-align: center; padding: 15px; background: #f8f9fa; border-radius: 5px; min-width: 80px; }}
                .stat-number {{ font-size: 28px; font-weight: bold; }}
                .critical {{ color: #dc3545; }}
                .high {{ color: #fd7e14; }}
                .medium {{ color: #ffc107; }}
                .low {{ color: #28a745; }}
                .info {{ color: #6c757d; }}
                .findings {{ margin-top: 30px; }}
                .finding {{ border-left: 4px solid #ddd; padding: 15px; margin: 10px 0; background: #f8f9fa; }}
                .finding.critical {{ border-left-color: #dc3545; }}
                .finding.high {{ border-left-color: #fd7e14; }}
                .finding.medium {{ border-left-color: #ffc107; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #6c757d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Zen-AI-Pentest Report</h1>
                    <div class="status">{status}</div>
                </div>

                <h2>Scan Summary</h2>
                <p><strong>Target:</strong> {scan_target}</p>
                <p><strong>Scan ID:</strong> {scan_id}</p>
                <p><strong>Duration:</strong> {duration:.1f} seconds</p>
                <p><strong>Completed:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}</p>

                <h3>Severity Breakdown</h3>
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number critical">{severity_counts.get("critical", 0)}</div>
                        <div>Critical</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number high">{severity_counts.get("high", 0)}</div>
                        <div>High</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number medium">{severity_counts.get("medium", 0)}</div>
                        <div>Medium</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number low">{severity_counts.get("low", 0)}</div>
                        <div>Low</div>
                    </div>
                </div>

                <div class="findings">
                    <h3>Top Findings</h3>
        """

        # Add top 5 findings
        for i, finding in enumerate(findings[:5], 1):
            severity = finding.get("severity", "info").lower()
            title = finding.get("title", "Unknown")
            description = finding.get("description", "")[:150]

            html += f"""
                    <div class="finding {severity}">
                        <strong>#{i} [{severity.upper()}]</strong> {title}
                        <p style="margin: 5px 0; color: #666;">{description}...</p>
                    </div>
            """

        if len(findings) > 5:
            html += f"<p style='text-align: center; color: #666;'>... and {len(findings) - 5} more findings</p>"

        html += f"""
                </div>

                <div class="footer">
                    <p>Generated by Zen-AI-Pentest</p>
                    <p>Scan ID: {scan_id}</p>
                    <p>This is an automated report. Please review all findings carefully.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def send_scan_report(
        self,
        to_email: Union[str, List[str]],
        scan_target: str,
        findings: List[Dict],
        duration: float,
        scan_id: str,
        report_path: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> bool:
        """
        Send scan report via email.

        Args:
            to_email: Recipient email(s)
            scan_target: Target that was scanned
            findings: List of findings from scan
            duration: Scan duration in seconds
            scan_id: Unique scan identifier
            report_path: Optional path to full report attachment
            subject: Optional custom subject line

        Returns:
            True if email sent successfully
        """
        if not self.config.validate():
            logger.error("Email configuration incomplete")
            return False

        try:
            # Build email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject or f"Pentest Report: {scan_target} - {len(findings)} findings"
            msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"

            if isinstance(to_email, list):
                msg["To"] = ", ".join(to_email)
                recipients = to_email
            else:
                msg["To"] = to_email
                recipients = [to_email]

            # Build HTML content
            html_content = self._build_html_report(scan_target, findings, duration, scan_id)

            # Attach HTML
            msg.attach(MIMEText(html_content, "html"))

            # Attach report file if provided
            if report_path and Path(report_path).exists():
                attachment = MIMEBase("application", "octet-stream")
                with open(report_path, "rb") as f:
                    attachment.set_payload(f.read())
                encoders.encode_base64(attachment)

                filename = Path(report_path).name
                attachment.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )
                msg.attach(attachment)
                logger.info(f"Attached report: {filename}")

            # Send email
            with self._create_smtp_connection() as server:
                server.sendmail(self.config.from_email, recipients, msg.as_string())

            logger.info(f"Email sent successfully to {recipients}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_simple_notification(
        self,
        to_email: str,
        subject: str,
        message: str,
    ) -> bool:
        """
        Send simple text email notification.

        Args:
            to_email: Recipient email
            subject: Email subject
            message: Plain text message

        Returns:
            True if sent successfully
        """
        if not self.config.validate():
            logger.error("Email configuration incomplete")
            return False

        try:
            msg = MIMEText(message)
            msg["Subject"] = subject
            msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            msg["To"] = to_email

            with self._create_smtp_connection() as server:
                server.sendmail(self.config.from_email, [to_email], msg.as_string())

            logger.info(f"Notification sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False


# Convenience function for integration
def send_report_after_scan(
    to_email: str,
    scan_results: Dict,
    report_path: Optional[str] = None,
) -> bool:
    """
    Convenience function to send report after scan completion.

    Args:
        to_email: Recipient email
        scan_results: Dictionary with keys: target, findings, duration, scan_id
        report_path: Optional full report attachment

    Returns:
        True if email sent successfully

    Example:
        send_report_after_scan(
            "admin@company.com",
            {
                "target": "example.com",
                "findings": [{"severity": "high", "title": "SQL Injection"}],
                "duration": 120.5,
                "scan_id": "scan-123",
            },
            "/reports/scan-123.pdf"
        )
    """
    reporter = EmailReporter()
    return reporter.send_scan_report(
        to_email=to_email,
        scan_target=scan_results.get("target", "Unknown"),
        findings=scan_results.get("findings", []),
        duration=scan_results.get("duration", 0),
        scan_id=scan_results.get("scan_id", "unknown"),
        report_path=report_path,
    )


if __name__ == "__main__":
    # Example usage
    import os

    # Set these environment variables or pass config directly
    os.environ.setdefault("SMTP_HOST", "smtp.gmail.com")
    os.environ.setdefault("SMTP_PORT", "587")
    os.environ.setdefault("SMTP_USER", "your-email@gmail.com")
    os.environ.setdefault("SMTP_PASS", "your-app-password")

    reporter = EmailReporter()

    # Example scan results
    test_results = {
        "target": "example.com",
        "findings": [
            {
                "severity": "critical",
                "title": "SQL Injection",
                "description": "SQLi in login form",
            },
            {
                "severity": "high",
                "title": "XSS",
                "description": "Reflected XSS in search",
            },
            {
                "severity": "medium",
                "title": "CSRF",
                "description": "Missing CSRF token",
            },
        ],
        "duration": 125.5,
        "scan_id": "scan-2024-001",
    }

    # Send report
    success = reporter.send_scan_report(
        to_email="admin@example.com",
        scan_target=test_results["target"],
        findings=test_results["findings"],
        duration=test_results["duration"],
        scan_id=test_results["scan_id"],
    )

    logger.info(f"Email sent: {success}")
