"""Configuration loader for repository settings."""

import logging
from typing import Optional

import yaml

from ..models.config import AppConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and parse repository configuration."""

    CONFIG_PATH = ".github/zen-ai-app.yml"

    @staticmethod
    async def load_config(github_api, owner: str, repo: str, ref: Optional[str] = None) -> AppConfig:
        """Load configuration from repository.

        Args:
            github_api: GitHubAPI instance
            owner: Repository owner
            repo: Repository name
            ref: Git reference (branch/commit)

        Returns:
            Parsed AppConfig
        """
        try:
            content = await github_api.get_file_content(owner, repo, ConfigLoader.CONFIG_PATH, ref)

            if content:
                config_data = yaml.safe_load(content)
                logger.info(f"Loaded config from {owner}/{repo}")
                return AppConfig(**config_data)

        except Exception as e:
            logger.warning(f"Failed to load config: {e}. Using defaults.")

        # Return default configuration
        logger.info(f"Using default configuration for {owner}/{repo}")
        return AppConfig()

    @staticmethod
    def validate_config(config: AppConfig) -> tuple[bool, list[str]]:
        """Validate configuration.

        Args:
            config: AppConfig to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Validate PR config
        pr_config = config.get_pr_config()
        if pr_config.fail_on not in ["none", "low", "medium", "high", "critical"]:
            errors.append(f"Invalid fail_on value: {pr_config.fail_on}")

        if not pr_config.tools:
            errors.append("At least one tool must be specified for PR scans")

        # Validate push config
        push_config = config.get_push_config()
        if not push_config.branches:
            errors.append("At least one branch must be specified for push scans")

        # Validate schedule config
        schedule_config = config.get_schedule_config()
        if schedule_config.enabled and not schedule_config.cron:
            errors.append("Cron expression required when schedule is enabled")

        return len(errors) == 0, errors
