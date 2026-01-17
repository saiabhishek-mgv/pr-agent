"""Configuration management for PR Agent."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field

from src.utils.exceptions import ConfigurationError
from src.utils.logger import logger


class AnalysisConfig(BaseModel):
    """Analysis configuration settings."""
    max_files_full_analysis: int = Field(default=50, ge=1)
    max_diff_size_per_file: int = Field(default=1000, ge=100)
    enable_security_check: bool = True
    enable_performance_check: bool = True
    enable_breaking_change_check: bool = True
    enable_test_coverage_check: bool = True


class CommentConfig(BaseModel):
    """Comment formatting configuration."""
    include_summary: bool = True
    include_key_files: bool = True
    include_risks: bool = True
    collapse_file_list: bool = True
    max_key_files: int = Field(default=10, ge=1)


class AIConfig(BaseModel):
    """AI service configuration."""
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = Field(default=4096, ge=100, le=8192)
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)


class Settings(BaseModel):
    """Main configuration settings."""
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    comment: CommentConfig = Field(default_factory=CommentConfig)
    ai: AIConfig = Field(default_factory=AIConfig)

    # Required secrets from environment
    github_token: str = ""
    anthropic_api_key: str = ""

    # GitHub Actions context
    repository: str = ""
    pr_number: int = 0


def load_yaml_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to .pr-agent.yml in repo root.

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = ".pr-agent.yml"

    config_file = Path(config_path)

    if not config_file.exists():
        logger.info(f"Config file not found: {config_path}, using defaults")
        return {}

    try:
        with open(config_file) as f:
            config = yaml.safe_load(f) or {}
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.warning(f"Failed to load config file {config_path}: {e}, using defaults")
        return {}


def load_settings(config_path: Optional[str] = None) -> Settings:
    """
    Load settings from YAML file and environment variables.
    Environment variables override file configuration.

    Args:
        config_path: Path to YAML config file

    Returns:
        Settings instance

    Raises:
        ConfigurationError: If required settings are missing
    """
    # Load from YAML file
    file_config = load_yaml_config(config_path)

    # Load required secrets from environment
    github_token = os.getenv("GITHUB_TOKEN", "")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

    # Load GitHub Actions context
    repository = os.getenv("GITHUB_REPOSITORY", "")
    pr_number_str = os.getenv("GITHUB_EVENT_NUMBER", "0")

    try:
        pr_number = int(pr_number_str)
    except ValueError:
        pr_number = 0

    # Apply environment variable overrides for analysis settings
    analysis_config = file_config.get("analysis", {})
    if os.getenv("PR_AGENT_MAX_FILES"):
        try:
            analysis_config["max_files_full_analysis"] = int(os.getenv("PR_AGENT_MAX_FILES"))
        except ValueError:
            pass

    if os.getenv("PR_AGENT_ENABLE_SECURITY") is not None:
        analysis_config["enable_security_check"] = os.getenv("PR_AGENT_ENABLE_SECURITY").lower() == "true"

    if os.getenv("PR_AGENT_ENABLE_PERFORMANCE") is not None:
        analysis_config["enable_performance_check"] = os.getenv("PR_AGENT_ENABLE_PERFORMANCE").lower() == "true"

    if os.getenv("PR_AGENT_ENABLE_BREAKING") is not None:
        analysis_config["enable_breaking_change_check"] = os.getenv("PR_AGENT_ENABLE_BREAKING").lower() == "true"

    if os.getenv("PR_AGENT_ENABLE_TEST_COVERAGE") is not None:
        analysis_config["enable_test_coverage_check"] = os.getenv("PR_AGENT_ENABLE_TEST_COVERAGE").lower() == "true"

    file_config["analysis"] = analysis_config

    # Build settings object
    settings = Settings(
        **file_config,
        github_token=github_token,
        anthropic_api_key=anthropic_api_key,
        repository=repository,
        pr_number=pr_number
    )

    # Validate required settings
    if not settings.github_token:
        raise ConfigurationError("GITHUB_TOKEN environment variable is required")

    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not set, AI features will be disabled")

    if not settings.repository:
        raise ConfigurationError("GITHUB_REPOSITORY environment variable is required")

    if settings.pr_number <= 0:
        raise ConfigurationError("GITHUB_EVENT_NUMBER must be a valid PR number")

    logger.info(f"Configuration loaded for {settings.repository} PR #{settings.pr_number}")

    return settings
