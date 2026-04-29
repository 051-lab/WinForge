"""WinForge plugin registry - discovers and describes installed plugins."""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from types import ModuleType
from typing import List, Optional

from loguru import logger

import plugins as plugins_pkg


@dataclass
class PluginInfo:
    name: str
    version: str = "0.0.0"
    description: str = ""
    author: str = "Unknown"
    enabled: bool = True
    module: Optional[ModuleType] = field(default=None, repr=False)


def discover_plugins() -> List[PluginInfo]:
    """Walk the plugins package and return metadata for each sub-plugin."""
    found: List[PluginInfo] = []
    for finder, name, _ispkg in pkgutil.iter_modules(plugins_pkg.__path__):
        full_name = f"plugins.{name}"
        try:
            mod = importlib.import_module(full_name)
            info = PluginInfo(
                name=getattr(mod, "PLUGIN_NAME", name),
                version=getattr(mod, "PLUGIN_VERSION", "0.0.0"),
                description=getattr(mod, "PLUGIN_DESCRIPTION", ""),
                author=getattr(mod, "PLUGIN_AUTHOR", "Unknown"),
                module=mod,
            )
            found.append(info)
            logger.info("Plugin loaded: {} v{}", info.name, info.version)
        except Exception as exc:
            logger.warning("Failed to load plugin {}: {}", name, exc)
    return found
