"""
Secure Configuration Management
Handles API keys with keyring, .env support, and encryption
"""

import base64
import json
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Literal, Optional

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Service name for keyring
KEYRING_SERVICE = "zen-ai-pentest"
ENV_PREFIX = "ZEN_"


@dataclass
class APIKeyConfig:
    """Configuration for API keys"""

    openrouter_key: Optional[str] = None
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    github_token: Optional[str] = None
    shodan_key: Optional[str] = None
    censys_id: Optional[str] = None
    censys_secret: Optional[str] = None

    def get_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider"""
        mapping = {
            "openrouter": self.openrouter_key,
            "openai": self.openai_key,
            "anthropic": self.anthropic_key,
            "claude": self.anthropic_key,
            "chatgpt": self.openai_key,
            "github": self.github_token,
            "shodan": self.shodan_key,
            "censys_id": self.censys_id,
            "censys_secret": self.censys_secret,
        }
        return mapping.get(provider.lower())


class SecureConfigManager:
    """
    Manages configuration securely using:
    1. Environment variables (highest priority)
    2. Keyring (system keychain)
    3. Encrypted config file
    4. Plain config file (fallback, not recommended)
    """

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = (
            config_dir or Path.home() / ".config" / "zen-ai-pentest"
        )
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "config.json"
        self.encrypted_config = self.config_dir / "config.enc"

        # Load .env file if exists
        env_file = self.config_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        # Also check project root
        load_dotenv(Path(".env"))

        self._cache: Dict[str, Any] = {}

    def _get_keyring_password(self, key_name: str) -> Optional[str]:
        """Get password from system keyring"""
        if not KEYRING_AVAILABLE:
            return None
        try:
            return keyring.get_password(KEYRING_SERVICE, key_name)
        except Exception as e:
            logger.debug(f"Keyring error for {key_name}: {e}")
            return None

    def _set_keyring_password(self, key_name: str, password: str) -> bool:
        """Store password in system keyring"""
        if not KEYRING_AVAILABLE:
            logger.warning(
                "Keyring not available, install with: pip install keyring"
            )
            return False
        try:
            keyring.set_password(KEYRING_SERVICE, key_name, password)
            return True
        except Exception as e:
            logger.error(f"Failed to store {key_name} in keyring: {e}")
            return False

    def get_api_key(
        self, provider: str, prefer_keyring: bool = True
    ) -> Optional[str]:
        """
        Get API key with priority:
        1. Environment variable (ZEN_{PROVIDER}_KEY)
        2. Keyring (if prefer_keyring=True)
        3. Encrypted config
        """
        env_var = f"{ENV_PREFIX}{provider.upper()}_KEY"

        # 1. Check environment variable
        env_value = os.getenv(env_var) or os.getenv(f"{provider.upper()}_KEY")
        if env_value:
            logger.debug(f"Using API key for {provider} from environment")
            return env_value

        # 2. Check keyring
        if prefer_keyring and KEYRING_AVAILABLE:
            keyring_value = self._get_keyring_password(f"{provider}_key")
            if keyring_value:
                logger.debug(f"Using API key for {provider} from keyring")
                return keyring_value

        # 3. Check encrypted config
        if CRYPTO_AVAILABLE and self.encrypted_config.exists():
            config = self._load_encrypted_config()
            if config and provider in config:
                return config[provider]

        return None

    def set_api_key(
        self,
        provider: str,
        key: str,
        storage: Literal["keyring", "encrypted", "env"] = "keyring",
    ) -> bool:
        """
        Store API key securely

        Args:
            provider: Provider name (openai, anthropic, etc.)
            key: The API key
            storage: Where to store - keyring, encrypted, or env
        """
        if storage == "keyring":
            return self._set_keyring_password(f"{provider}_key", key)

        elif storage == "encrypted":
            if not CRYPTO_AVAILABLE:
                logger.error(
                    "cryptography library required for encrypted storage"
                )
                return False
            config = self._load_encrypted_config() or {}
            config[provider] = key
            return self._save_encrypted_config(config)

        elif storage == "env":
            env_file = self.config_dir / ".env"
            env_var = f"{ENV_PREFIX}{provider.upper()}_KEY"

            # Read existing
            lines = []
            if env_file.exists():
                lines = env_file.read_text().splitlines()

            # Update or append
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{env_var}="):
                    lines[i] = f"{env_var}={key}"
                    updated = True
                    break

            if not updated:
                lines.append(f"{env_var}={key}")

            env_file.write_text("\n".join(lines) + "\n")
            # Secure permissions
            os.chmod(env_file, 0o600)
            return True

        return False

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _load_encrypted_config(self) -> Optional[Dict[str, str]]:
        """Load and decrypt config file"""
        if not self.encrypted_config.exists():
            return None

        try:
            # Get master password from keyring or prompt
            master = self._get_keyring_password("master")
            if not master:
                return None

            data = self.encrypted_config.read_bytes()
            salt = data[:16]
            encrypted = data[16:]

            key = self._derive_key(master, salt)
            f = Fernet(key)
            decrypted = f.decrypt(encrypted)

            return json.loads(decrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt config: {e}")
            return None

    def _save_encrypted_config(self, config: Dict[str, str]) -> bool:
        """Encrypt and save config file"""
        try:
            import secrets

            # Get or create master password
            master = self._get_keyring_password("master")
            if not master:
                master = secrets.token_urlsafe(32)
                self._set_keyring_password("master", master)

            salt = secrets.token_bytes(16)
            key = self._derive_key(master, salt)

            f = Fernet(key)
            encrypted = f.encrypt(json.dumps(config).encode())

            self.encrypted_config.write_bytes(salt + encrypted)
            os.chmod(self.encrypted_config, 0o600)
            return True
        except Exception as e:
            logger.error(f"Failed to encrypt config: {e}")
            return False

    def list_configured_keys(self) -> list:
        """List all configured API keys (names only, no values)"""
        keys = []
        providers = ["openai", "anthropic", "openrouter", "github", "shodan"]

        for provider in providers:
            if self.get_api_key(provider):
                keys.append(provider)

        return keys

    def remove_api_key(self, provider: str) -> bool:
        """Remove API key from all storage locations"""
        success = True

        # Remove from keyring
        if KEYRING_AVAILABLE:
            try:
                keyring.delete_password(KEYRING_SERVICE, f"{provider}_key")
            except Exception:
                pass

        # Remove from encrypted config
        if self.encrypted_config.exists():
            config = self._load_encrypted_config() or {}
            if provider in config:
                del config[provider]
                success = self._save_encrypted_config(config) and success

        return success


@lru_cache()
def get_secure_config() -> SecureConfigManager:
    """Get singleton instance of SecureConfigManager"""
    return SecureConfigManager()


def migrate_plain_config(config_path: Path) -> bool:
    """Migrate plain text config to secure storage"""
    if not config_path.exists():
        return False

    try:
        with open(config_path) as f:
            old_config = json.load(f)

        manager = get_secure_config()

        # Migrate API keys
        key_mapping = {
            "openai_key": "openai",
            "anthropic_key": "anthropic",
            "openrouter_key": "openrouter",
            "github_token": "github",
            "shodan_key": "shodan",
        }

        for old_key, provider in key_mapping.items():
            if old_key in old_config and old_config[old_key]:
                manager.set_api_key(
                    provider, old_config[old_key], storage="keyring"
                )

        # Backup old config
        backup_path = config_path.with_suffix(".json.backup")
        config_path.rename(backup_path)

        logger.info(
            f"Config migrated to secure storage. Old config backed up to {backup_path}"
        )
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
