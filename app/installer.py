"""WinForge plugin installer - enable, disable, and remove plugins."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List

from loguru import logger

# Registry file that persists enabled/disabled state
_REGISTRY_FILE = Path("config/plugins.json")
# Root folder where plugins live
_PLUGINS_DIR = Path("plugins")
# Folder where uninstalled plugins are archived (not deleted, for safety)
_ARCHIVE_DIR = Path("plugins/_uninstalled")


def _load_registry() -> Dict[str, bool]:
    """Load the plugin enabled/disabled registry from disk."""
    if _REGISTRY_FILE.exists():
        try:
            return json.loads(_REGISTRY_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to read plugin registry: {}", exc)
    return {}


def _save_registry(registry: Dict[str, bool]) -> None:
    """Persist the plugin registry to disk."""
    try:
        _REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        _REGISTRY_FILE.write_text(
            json.dumps(registry, indent=2), encoding="utf-8"
        )
    except Exception as exc:
        logger.warning("Failed to save plugin registry: {}", exc)


def is_plugin_enabled(plugin_name: str) -> bool:
    """Return True if the plugin is enabled (default: True if not in registry)."""
    registry = _load_registry()
    return registry.get(plugin_name, True)


def set_plugin_enabled(plugin_name: str, enabled: bool) -> None:
    """Enable or disable a plugin by name. Persists to registry."""
    registry = _load_registry()
    registry[plugin_name] = enabled
    _save_registry(registry)
    state = "enabled" if enabled else "disabled"
    logger.info("Plugin '{}' {}", plugin_name, state)


def enable_plugin(plugin_name: str) -> None:
    """Enable a plugin."""
    set_plugin_enabled(plugin_name, True)


def disable_plugin(plugin_name: str) -> None:
    """Disable a plugin."""
    set_plugin_enabled(plugin_name, False)


def uninstall_plugin(plugin_folder_name: str) -> bool:
    """Move a plugin folder to the _uninstalled archive.

    Args:
        plugin_folder_name: The subfolder name inside plugins/ (e.g. 'hello').

    Returns:
        True on success, False if the plugin folder was not found.
    """
    plugin_path = _PLUGINS_DIR / plugin_folder_name
    if not plugin_path.exists():
        logger.warning(
            "Cannot uninstall '{}': folder not found at {}",
            plugin_folder_name,
            plugin_path,
        )
        return False

    _ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    dest = _ARCHIVE_DIR / plugin_folder_name

    # If a previous archive copy exists, remove it first
    if dest.exists():
        shutil.rmtree(dest)

    shutil.move(str(plugin_path), str(dest))

    # Remove from registry too
    registry = _load_registry()
    registry.pop(plugin_folder_name, None)
    _save_registry(registry)

    logger.info("Plugin '{}' uninstalled (archived to {})", plugin_folder_name, dest)
    return True


def list_enabled_plugins() -> List[str]:
    """Return the names of all plugins currently marked as enabled in registry."""
    registry = _load_registry()
    return [name for name, enabled in registry.items() if enabled]
