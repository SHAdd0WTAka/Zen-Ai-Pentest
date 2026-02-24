"""
Input Validation & Sanitization
Prevents injection attacks and ensures data integrity
"""

import html
import logging
import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Pattern
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """Validation rule configuration"""

    pattern: Pattern
    max_length: int = 255
    allow_empty: bool = False
    error_message: str = "Invalid input"


class InputValidator:
    """
    Centralized input validation for all user inputs
    """

    # Domain regex (RFC compliant)
    DOMAIN_PATTERN = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
    )

    # IP address regex
    IP_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    # Email regex (simplified)
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    # Safe filename regex
    FILENAME_PATTERN = re.compile(r"^[\w\-. ]+$")

    # Command injection pattern
    DANGEROUS_CHARS = re.compile(r'[;&|`$(){}[\]\\\'"<>]')

    # Path traversal pattern
    PATH_TRAVERSAL = re.compile(r"\.\.|^/|\\")

    def __init__(self):
        self.rules: dict[str, ValidationRule] = {
            "domain": ValidationRule(
                pattern=self.DOMAIN_PATTERN,
                max_length=253,
                error_message="Invalid domain format",
            ),
            "ip": ValidationRule(
                pattern=self.IP_PATTERN,
                max_length=15,
                error_message="Invalid IP address",
            ),
            "email": ValidationRule(
                pattern=self.EMAIL_PATTERN,
                max_length=254,
                error_message="Invalid email format",
            ),
            "filename": ValidationRule(
                pattern=self.FILENAME_PATTERN,
                max_length=255,
                error_message="Invalid filename (special chars not allowed)",
            ),
        }

    def validate_domain(self, domain: str) -> Optional[str]:
        """Validate and sanitize domain name"""
        if not domain:
            return None

        # Strip whitespace and lowercase
        domain = domain.strip().lower()

        # Check length
        if len(domain) > 253:
            logger.warning(f"Domain too long: {domain[:50]}...")
            return None

        # Validate pattern
        if not self.DOMAIN_PATTERN.match(domain):
            logger.warning(f"Invalid domain format: {domain}")
            return None

        # Check for dangerous characters
        if self.DANGEROUS_CHARS.search(domain):
            logger.warning(f"Domain contains dangerous chars: {domain}")
            return None

        return domain

    def validate_ip(self, ip: str) -> Optional[str]:
        """Validate IP address"""
        if not ip:
            return None

        ip = ip.strip()

        if not self.IP_PATTERN.match(ip):
            logger.warning(f"Invalid IP format: {ip}")
            return None

        return ip

    def validate_email(self, email: str) -> Optional[str]:
        """Validate email address"""
        if not email:
            return None

        email = email.strip().lower()

        if len(email) > 254:
            logger.warning(f"Email too long: {email[:50]}...")
            return None

        if not self.EMAIL_PATTERN.match(email):
            logger.warning(f"Invalid email format: {email}")
            return None

        return email

    def validate_url(
        self, url: str, allowed_schemes: List[str] = None
    ) -> Optional[str]:
        """Validate and sanitize URL"""
        if not url:
            return None

        allowed_schemes = allowed_schemes or ["http", "https"]

        try:
            parsed = urlparse(url.strip())

            # Check scheme
            if parsed.scheme not in allowed_schemes:
                logger.warning(f"URL scheme not allowed: {parsed.scheme}")
                return None

            # Validate hostname
            if not parsed.hostname:
                logger.warning(f"URL missing hostname: {url}")
                return None

            if not self.validate_domain(parsed.hostname):
                logger.warning(f"Invalid URL hostname: {parsed.hostname}")
                return None

            # Reconstruct safe URL
            safe_url = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                safe_url += f":{parsed.port}"
            if parsed.path:
                # Sanitize path
                safe_path = self.sanitize_path(parsed.path)
                safe_url += safe_path

            return safe_url

        except Exception as e:
            logger.warning(f"URL validation error: {e}")
            return None

    def validate_filename(self, filename: str) -> Optional[str]:
        """Validate filename to prevent path traversal"""
        if not filename:
            return None

        # Strip path components
        filename = filename.split("/")[-1].split("\\")[-1]

        if not self.FILENAME_PATTERN.match(filename):
            logger.warning(f"Invalid filename: {filename}")
            return None

        # Check for path traversal
        if self.PATH_TRAVERSAL.search(filename):
            logger.warning(f"Path traversal detected: {filename}")
            return None

        return filename

    def sanitize_path(self, path: str) -> str:
        """Sanitize file path"""
        if not path:
            return "/"

        # Normalize
        path = path.replace("\\", "/")

        # Remove path traversal
        parts = []
        for part in path.split("/"):
            if part == ".." or part == ".":
                continue
            if part:
                parts.append(part)

        return "/" + "/".join(parts)

    def sanitize_for_shell(self, value: str) -> str:
        """
        Sanitize string for safe use in shell commands.
        Uses shell=False approach internally.
        """
        if not value:
            return ""

        # Remove all shell metacharacters
        sanitized = self.DANGEROUS_CHARS.sub("", value)

        return sanitized

    def escape_html(self, text: str) -> str:
        """Escape HTML entities to prevent XSS"""
        return html.escape(str(text), quote=True)

    def sanitize_llm_output(
        self, output: str, allowed_tags: List[str] = None
    ) -> str:
        """
        Sanitize LLM output before storage/display.
        Removes potentially dangerous content.
        """
        if not output:
            return ""

        # Remove null bytes
        output = output.replace("\x00", "")

        # Remove control characters except newlines and tabs
        output = "".join(
            char
            for char in output
            if char == "\n"
            or char == "\t"
            or (ord(char) >= 32 and ord(char) < 127)
        )

        # Escape HTML
        output = self.escape_html(output)

        return output


class SecureSubprocess:
    """
    Secure subprocess execution wrapper.
    Prevents shell injection by using shell=False and argument lists.
    """

    @staticmethod
    def run(
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: int = 300,
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Execute command securely with shell=False.

        Args:
            command: List of command arguments (NEVER use shell=True)
            cwd: Working directory
            env: Environment variables
            timeout: Timeout in seconds
            capture_output: Capture stdout/stderr
            check: Raise exception on non-zero exit

        Returns:
            CompletedProcess instance

        Raises:
            subprocess.SubprocessError: On execution failure
        """
        if not command:
            raise ValueError("Command cannot be empty")

        # Validate all arguments
        validator = InputValidator()
        for arg in command:
            if validator.DANGEROUS_CHARS.search(str(arg)):
                logger.error(f"Dangerous character in command argument: {arg}")
                raise ValueError(f"Invalid command argument: {arg}")

        logger.debug(f"Executing: {' '.join(command)}")

        try:
            return subprocess.run(
                command,
                cwd=cwd,
                env=env,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
                check=check,
                shell=False,  # NEVER use shell=True
            )
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout after {timeout}s: {command[0]}")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Subprocess error: {e}")
            raise

    @staticmethod
    def validate_nuclei_args(args: List[str]) -> bool:
        """
        Validate Nuclei arguments for security.
        Blocks dangerous flags.
        """
        blocked_flags = [
            "-shell",
            "-exec",
            "-command",
            "-cmd",
            "--shell",
            "--exec",
            "--command",
            "--cmd",
        ]

        for arg in args:
            if any(arg.startswith(blocked) for blocked in blocked_flags):
                logger.error(f"Blocked dangerous Nuclei flag: {arg}")
                return False

        return True


# Global validator instance
_validator = None


def get_validator() -> InputValidator:
    """Get global validator instance"""
    global _validator
    if _validator is None:
        _validator = InputValidator()
    return _validator
