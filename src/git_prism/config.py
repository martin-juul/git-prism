"""Configuration management for git-prism with user overrides."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

# Default config location (bundled with package)
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "file_patterns.yaml"

# User config locations (checked in order)
USER_CONFIG_PATHS = [
    Path.home() / ".config" / "git-prism" / "file_patterns.yaml",
    Path.home() / ".git-prism" / "file_patterns.yaml",
]


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries, with override taking precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            # For lists, replace entirely (user can fully override)
            result[key] = value
        else:
            result[key] = value
    return result


def load_config() -> dict[str, Any]:
    """Load configuration with user overrides.

    Loads the default config and merges any user config on top.

    Returns:
        Merged configuration dictionary.
    """
    # Load default config
    config: dict[str, Any] = {}
    if DEFAULT_CONFIG_PATH.exists():
        try:
            with open(DEFAULT_CONFIG_PATH) as f:
                config = yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError) as e:
            logger.warning("Failed to load default config: %s", e)

    # Check for user override
    for user_path in USER_CONFIG_PATHS:
        if user_path.exists():
            try:
                with open(user_path) as f:
                    user_config = yaml.safe_load(f) or {}
                config = _deep_merge(config, user_config)
                logger.debug("Loaded user config from %s", user_path)
                break
            except (yaml.YAMLError, OSError) as e:
                logger.warning("Failed to load user config from %s: %s", user_path, e)

    return config


# Singleton config instance
_config: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    """Get the loaded configuration (cached).

    Returns:
        Configuration dictionary.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> dict[str, Any]:
    """Reload configuration from files.

    Returns:
        Freshly loaded configuration dictionary.
    """
    global _config
    _config = load_config()
    return _config


def get_language_map() -> dict[str, str]:
    """Get language extension mapping.

    Returns:
        Dict mapping file extension to language name.
    """
    config = get_config()
    return config.get("language_map", {})


def get_binary_extensions() -> set[str]:
    """Get set of binary file extensions.

    Returns:
        Set of extensions to exclude as binary.
    """
    config = get_config()
    return set(config.get("binary_extensions", []))


def get_generated_patterns() -> set[str]:
    """Get set of generated file patterns.

    Returns:
        Set of patterns for generated files to exclude.
    """
    config = get_config()
    return set(config.get("generated_patterns", []))


def get_ignore_directories() -> set[str]:
    """Get set of directories to ignore.

    Returns:
        Set of directory names to skip during scanning.
    """
    config = get_config()
    return set(config.get("ignore_directories", []))


def get_project_indicators() -> dict[str, str]:
    """Get project file indicators for area type detection.

    Returns:
        Dict mapping filename to area type (frontend/backend).
    """
    config = get_config()
    return config.get("project_indicators", {})


def get_monorepo_patterns() -> list[str]:
    """Get monorepo directory patterns.

    Returns:
        List of directory names that indicate monorepo structure.
    """
    config = get_config()
    return config.get("monorepo_patterns", [])


def get_area_type_names() -> dict[str, str]:
    """Get area type inference from directory names.

    Returns:
        Dict mapping directory name to area type.
    """
    config = get_config()
    return config.get("area_type_names", {})


def get_framework_detection() -> dict[str, Any]:
    """Get framework detection configuration.

    Returns:
        Dict with framework_files, js_frameworks, python_frameworks, etc.
    """
    config = get_config()
    return {
        "framework_files": config.get("framework_files", {}),
        "js_frameworks": config.get("js_frameworks", {}),
        "python_frameworks": config.get("python_frameworks", {}),
        "php_frameworks": config.get("php_frameworks", {}),
        "ruby_frameworks": config.get("ruby_frameworks", {}),
        "go_frameworks": config.get("go_frameworks", {}),
    }
