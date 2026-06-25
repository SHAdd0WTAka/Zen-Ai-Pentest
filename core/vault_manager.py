"""
🔐 Secure Vault Manager for Obsidian and Credentials.

Manages encryption/decryption of Obsidian Vault and GitHub CLI authentication.
Only operates when Kill Switch permits (system unlocked).
"""

__all__ = [
    "SecureVaultManager",
    "VaultConfig",
    "get_vault_manager",
]

import asyncio
import base64
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


@dataclass
class VaultConfig:
    """Configuration for vault paths."""

    vault_path: Path = Path.home() / "obsidian-vault"
    encrypted_vault_path: Path = Path.home() / ".secure" / "vault.enc"
    key_file: Path = Path.home() / ".secure" / "vault.key"
    github_config_path: Path = Path.home() / ".config" / "gh"


class SecureVaultManager:
    """
    Manages secure vault for Obsidian and credentials.

    All operations require system to be unlocked via Kill Switch.
    """

    def __init__(self, config: Optional[VaultConfig] = None):
        self.config = config or VaultConfig()
        self._master_key: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None
        self._is_unlocked = False

        # Ensure secure directory exists
        self.config.encrypted_vault_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    async def decrypt_vault(self, auth_token: str) -> bool:
        """
        Decrypt Obsidian Vault using auth token.

        Args:
            auth_token: Kimi OAuth token used as decryption key

        Returns:
            True if successful
        """
        try:
            logger.info("🔓 Decrypting vault...")

            # Check if encrypted vault exists
            if not self.config.encrypted_vault_path.exists():
                logger.warning("No encrypted vault found - creating new")
                await self._create_new_vault(auth_token)
                return True

            # Read encrypted data
            with open(self.config.encrypted_vault_path, "rb") as f:
                data = json.loads(f.read())

            salt = base64.b64decode(data["salt"])
            encrypted_vault = base64.b64decode(data["vault"])

            # Derive key from auth token
            self._master_key = self._derive_key(auth_token, salt)
            self._fernet = Fernet(self._master_key)

            # Decrypt vault
            decrypted = self._fernet.decrypt(encrypted_vault)

            # Extract to vault directory
            await self._extract_vault(decrypted)

            self._is_unlocked = True
            logger.info("✅ Vault decrypted successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Vault decryption failed: {e}")
            self._master_key = None
            self._fernet = None
            return False

    async def encrypt_vault(self) -> bool:
        """
        Encrypt Obsidian Vault and secure credentials.

        Returns:
            True if successful
        """
        try:
            logger.info("🔐 Encrypting vault...")

            if not self._is_unlocked:
                logger.warning("Vault already locked")
                return True

            if not self._fernet:
                logger.error("No encryption key available")
                return False

            # Read vault contents
            vault_data = await self._read_vault_contents()

            # Encrypt
            encrypted = self._fernet.encrypt(vault_data)

            # Save encrypted vault
            salt = os.urandom(16)
            data = {
                "salt": base64.b64encode(salt).decode(),
                "vault": base64.b64encode(encrypted).decode(),
                "timestamp": str(asyncio.get_event_loop().time()),
            }

            # Atomic write
            temp_file = self.config.encrypted_vault_path.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(data, f)

            os.chmod(temp_file, 0o600)
            temp_file.replace(self.config.encrypted_vault_path)

            # Clear vault directory (secure wipe)
            await self._secure_wipe_vault()

            # Clear keys from memory
            self._master_key = None
            self._fernet = None
            self._is_unlocked = False

            logger.info("✅ Vault encrypted and secured")
            return True

        except Exception as e:
            logger.error(f"❌ Vault encryption failed: {e}")
            return False

    async def _create_new_vault(self, auth_token: str):
        """Create a new encrypted vault."""
        salt = os.urandom(16)
        self._master_key = self._derive_key(auth_token, salt)
        self._fernet = Fernet(self._master_key)

        # Create empty vault structure
        empty_vault = json.dumps(
            {
                "version": "1.0",
                "created": str(asyncio.get_event_loop().time()),
                "files": {},
            }
        ).encode()

        encrypted = self._fernet.encrypt(empty_vault)

        data = {
            "salt": base64.b64encode(salt).decode(),
            "vault": base64.b64encode(encrypted).decode(),
            "timestamp": str(asyncio.get_event_loop().time()),
        }

        with open(self.config.encrypted_vault_path, "w") as f:
            json.dump(data, f)

        os.chmod(self.config.encrypted_vault_path, 0o600)

    async def _read_vault_contents(self) -> bytes:
        """Read all files from vault directory."""
        files = {}

        if self.config.vault_path.exists():
            for file_path in self.config.vault_path.rglob("*"):
                if file_path.is_file():
                    try:
                        rel_path = str(file_path.relative_to(self.config.vault_path))
                        with open(file_path, "rb") as f:
                            files[rel_path] = base64.b64encode(f.read()).decode()
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")

        vault_data = {
            "version": "1.0",
            "timestamp": str(asyncio.get_event_loop().time()),
            "files": files,
        }

        return json.dumps(vault_data).encode()

    async def _extract_vault(self, decrypted_data: bytes):
        """Extract decrypted vault to directory."""
        data = json.loads(decrypted_data)

        # Clear and recreate vault directory
        if self.config.vault_path.exists():
            await self._secure_wipe_vault()

        self.config.vault_path.mkdir(mode=0o700, parents=True, exist_ok=True)

        # Extract files
        for rel_path, content in data.get("files", {}).items():
            file_path = self.config.vault_path / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "wb") as f:
                f.write(base64.b64decode(content))

            os.chmod(file_path, 0o600)

    async def _secure_wipe_vault(self):
        """Securely wipe vault directory."""
        if not self.config.vault_path.exists():
            return

        # Overwrite files with zeros before deletion
        for file_path in self.config.vault_path.rglob("*"):
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    with open(file_path, "wb") as f:
                        f.write(b"\x00" * size)
                    file_path.unlink()
                except Exception:
                    pass

        # Remove directories
        import shutil

        shutil.rmtree(self.config.vault_path, ignore_errors=True)

    # GitHub CLI Integration

    async def setup_github_cli(self, token: str) -> bool:
        """
        Authenticate GitHub CLI with token.

        Args:
            token: GitHub personal access token

        Returns:
            True if successful
        """
        try:
            logger.info("🔑 Setting up GitHub CLI...")

            import shutil

            gh_path = shutil.which("gh")
            if not gh_path:
                logger.error("❌ gh CLI not found in PATH")
                return False

            # Use token to authenticate
            result = subprocess.run(
                [gh_path, "auth", "login", "--with-token"],
                input=token,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info("✅ GitHub CLI authenticated")
                return True
            else:
                logger.error(f"GitHub auth failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"GitHub CLI setup failed: {e}")
            return False

    async def logout_github_cli(self):
        """Logout GitHub CLI and clear credentials."""
        try:
            import shutil

            gh_path = shutil.which("gh")
            if gh_path:
                subprocess.run([gh_path, "auth", "logout"], capture_output=True, timeout=10)

            # Clear config directory
            if self.config.github_config_path.exists():
                import shutil

                shutil.rmtree(self.config.github_config_path, ignore_errors=True)

            logger.info("✅ GitHub CLI logged out")
        except Exception as e:
            logger.warning(f"GitHub logout error: {e}")

    # Credential Management

    def get_credential(self, name: str) -> Optional[str]:
        """Get credential from vault (only when unlocked)."""
        if not self._is_unlocked:
            raise SecurityError("Vault is locked")

        creds_file = self.config.vault_path / "credentials.json"
        if not creds_file.exists():
            return None

        try:
            with open(creds_file) as f:
                creds = json.load(f)
            return creds.get(name)
        except Exception:
            return None

    def store_credential(self, name: str, value: str):
        """Store credential in vault."""
        if not self._is_unlocked:
            raise SecurityError("Vault is locked")

        creds_file = self.config.vault_path / "credentials.json"

        creds = {}
        if creds_file.exists():
            with open(creds_file) as f:
                creds = json.load(f)

        creds[name] = value

        with open(creds_file, "w") as f:
            json.dump(creds, f)

        os.chmod(creds_file, 0o600)

    def is_unlocked(self) -> bool:
        """Check if vault is currently unlocked."""
        return self._is_unlocked


class SecurityError(Exception):
    """Security-related error."""


# Global instance
_vault_manager: Optional[SecureVaultManager] = None


def get_vault_manager() -> SecureVaultManager:
    """Get global vault manager instance."""
    global _vault_manager
    if _vault_manager is None:
        _vault_manager = SecureVaultManager()
    return _vault_manager


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage
    async def main():
        vm = get_vault_manager()
        logger.info(f"Vault path: {vm.config.vault_path}")
        logger.info(f"Encrypted path: {vm.config.encrypted_vault_path}")
        logger.info(f"Is unlocked: {vm.is_unlocked()}")

    asyncio.run(main())
