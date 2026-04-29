"""WinForge plugin registry - discovers and describes installed plugins."""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from types import ModuleType
from typing import List, Optional

from loguru import logger

import plugins as plugins_pkg
from app.sandbox import PluginPermissions, load_permissions


@dataclass
class PluginInfo:
    name: str
    version: str = "0.0.0"
    description: str = ""
    author: str = "Unknown"
    enabled: bool = True
    module: Optional[ModuleType] = field(default=None, repr=False)
    permissions: PluginPermissions = field(
        default_factory=PluginPermissions, repr=False
    )


def discover_plugins() -> List[PluginInfo]:
    """Walk the plugins package and return metadata for each sub-plugin."""
    found: List[PluginInfo] = []
    for finder, name, _ispkg in pkgutil.iter_modules(plugins_pkg.__path__):
        full_name = f"plugins.{name}"
        try:
            mod = importlib.import_module(full_name)
            perms = load_permissions(mod)
            info = PluginInfo(
                name=getattr(mod, "PLUGIN_NAME", name),
                version=getattr(mod, "PLUGIN_VERSION", "0.0.0"),
                description=getattr(mod, "PLUGIN_DESCRIPTION", ""),
                author=getattr(mod, "PLUGIN_AUTHOR", "Unknown"),
                module=mod,
                permissions=perms,
            )
            found.append(info)
            logger.info(
                "Plugin loaded: {} v{} permissions={}",
                info.name, info.version, info.permissions.granted,
            )
        except Exception as exc:

            
def install_plugin_from_registry(plugin_id: str, plugins_path: str) -> bool:
    """Install a plugin from the remote registry.
    
    Args:
        plugin_id: Unique identifier for the plugin in registry
        plugins_path: Path to plugins directory
    
    Returns:
        True if installation successful, False otherwise
    """
    from app.registry import PluginRegistry
    import os
    
    registry = PluginRegistry()
    plugin_meta = registry.get_plugin(plugin_id)
    
    if not plugin_meta:
        logger.error(f"Plugin {plugin_id} not found in registry")
        return False
    
    # Create destination path
    plugin_filename = plugin_meta.get("filename", f"{plugin_id}.py")
    dest_path = os.path.join(plugins_path, plugin_filename)
    
    # Download the plugin
    if registry.download_plugin(plugin_id, dest_path):
        logger.info(f"Successfully installed plugin {plugin_id}")
        return True
    else:
        logger.error(f"Failed to install plugin {plugin_id}")
        return False
            logger.warning("Failed to load plugin {}: {}", name, exc)
    return found
