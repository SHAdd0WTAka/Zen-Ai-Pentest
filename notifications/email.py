"""
Email Notifications für Zen-AI-Pentest
"""

import logging
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Sendet Email-Benachrichtigungen"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int = 587,
        username: str = None,
        password: str = None,
        use_tls: bool = True,
        from_addr: str = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_addr = from_addr or username

    def send_email(
        self,
        to_addrs: List[str],
        subject: str,
        body_text: str,
        body_html: str = None,
        attachments: List[str] = None,
    ) -> bool:
        """Sendet Email"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(to_addrs)

            # Text body
            msg.attach(MIMEText(body_text, "plain"))

            # HTML body
            if body_html:
                msg.attach(MIMEText(body_html, "html"))

            # Attachments
            if attachments:
                for filepath in attachments:
                    with open(filepath, "rb") as f:
                        part = MIMEApplication(f.read())
                        part.add_header(
                            "Content-Disposition",
                            "attachment",
                            filename=filepath.split("/")[-1],
                        )
                        msg.attach(part)

            # Send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(self.from_addr, to_addrs, msg.as_string())

            logger.info(f"Email sent to {', '.join(to_addrs)}")
            return True

        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False

    def send_scan_report(
        self,
        to_addrs: List[str],
        scan_id: int,
        target: str,
        report_file: str,
        findings: List[Dict],
    ) -> bool:
        """Sendet Scan-Report per Email"""
        subject = f"Pentest Report: {target}"

        # Count findings
        critical = sum(1 for f in findings if f.get("severity") == "critical")
        high = sum(1 for f in findings if f.get("severity") == "high")
        medium = sum(1 for f in findings if f.get("severity") == "medium")

        body_text = f"""
Pentest Scan Completed

Target: {target}
Scan ID: {scan_id}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

Summary:
- Critical: {critical}
- High: {high}
- Medium: {medium}
- Total: {len(findings)}

See attached report for details.

This is an automated message from Zen-AI-Pentest.
        """

        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2>Pentest Scan Completed</h2>
    <table>
        <tr><td><strong>Target:</strong></td><td>{target}</td></tr>
        <tr><td><strong>Scan ID:</strong></td><td>{scan_id}</td></tr>
        <tr><td><strong>Date:</strong></td><td>{datetime.now().strftime("%Y-%m-%d %H:%M")}</td></tr>
    </table>

    <h3>Summary</h3>
    <ul>
        <li>Critical: <span style="color: red;">{critical}</span></li>
        <li>High: <span style="color: orange;">{high}</span></li>
        <li>Medium: <span style="color: yellow;">{medium}</span></li>
        <li>Total: {len(findings)}</li>
    </ul>

    <p>See attached report for details.</p>
</body>
</html>
        """

        return self.send_email(
            to_addrs=to_addrs,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            attachments=[report_file] if report_file else None,
        )


def email_scan_report(recipient: str, scan_id: int, report_file: str) -> str:
    """Sendet Scan-Report per Email"""
    import os

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if not all([smtp_user, smtp_pass]):
        return "SMTP credentials not configured"

    notifier = EmailNotifier(smtp_host, username=smtp_user, password=smtp_pass)
    success = notifier.send_email(
        to_addrs=[recipient],
        subject=f"Pentest Report - Scan {scan_id}",
        body_text=f"See attached report for scan {scan_id}",
        attachments=[report_file] if report_file else None,
    )
    return "Email sent" if success else "Failed to send email"
