"""WinForge Plugin Sandbox - permissions manifest and enforcement layer.

Each plugin declares the capabilities it needs via a PLUGIN_PERMISSIONS list
in its __init__.py.  The sandbox validates those declarations against a known
catalogue and exposes helpers for the UI and runtime to query/enforce them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import ModuleType
from typing import Dict, List, Optional

from loguru import logger

# ---------------------------------------------------------------------------
# Permission catalogue
# ---------------------------------------------------------------------------

#: All recognised permission tokens.  Extend this dict when adding new scopes.
KNOWN_PERMISSIONS: Dict[str, str] = {
    "ui:read":        "Read the current UI state (theme, window size)",
    "ui:write":       "Modify UI elements at runtime",
    "fs:read":        "Read files from the application data directory",
    "fs:write":       "Write files to the application data directory",
    "network:fetch":  "Make outbound HTTP requests",
    "telemetry:send": "Emit anonymous telemetry events",
    "clipboard:read": "Read the system clipboard",
    "clipboard:write":"Write to the system clipboard",
    "system:info":    "Query basic OS/hardware information",
}

# Permissions that require an explicit user grant before the plugin may run
_SENSITIVE: frozenset[str] = frozenset({
    "fs:write",
    "network:fetch",
    "telemetry:send",
    "clipboard:read",
    "clipboard:write",
    "system:info",
})


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PluginPermissions:
    """Validated permission set for a single plugin."""

    #: Tokens the plugin declared and that are recognised.
    granted: List[str] = field(default_factory=list)
    #: Tokens the plugin declared but that are *not* in KNOWN_PERMISSIONS.
    unknown: List[str] = field(default_factory=list)
    #: Whether the plugin declared any sensitive permissions.
    has_sensitive: bool = False

    def is_allowed(self, token: str) -> bool:
        """Return True when *token* is in the granted set."""
        return token in self.granted

    def sensitive_list(self) -> List[str]:
        """Return the subset of granted tokens that are sensitive."""
        return [t for t in self.granted if t in _SENSITIVE]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SandboxViolation(RuntimeError):
    """Raised when a plugin attempts an action it has no permission for."""

    def __init__(self, plugin_name: str, token: str):
        self.plugin_name = plugin_name
        self.token = token
        super().__init__(
            f"Plugin '{plugin_name}' is not permitted to use '{token}'"
        )


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_permissions(module: Optional[ModuleType]) -> PluginPermissions:
    """Extract and validate permissions declared by *module*.

    A plugin declares its needs as a module-level list::

        PLUGIN_PERMISSIONS = ["ui:read", "fs:write"]

    Unknown tokens are collected but do not raise; the UI can warn the user.
    """
    perms = PluginPermissions()
    if module is None:
        return perms

    declared: List[str] = getattr(module, "PLUGIN_PERMISSIONS", [])
    if not isinstance(declared, list):
        logger.warning(
            "Plugin '{}' has invalid PLUGIN_PERMISSIONS (expected list)",
            getattr(module, "PLUGIN_NAME", module.__name__),
        )
        return perms

    for token in declared:
        if not isinstance(token, str):
            continue
        if token in KNOWN_PERMISSIONS:
            perms.granted.append(token)
        else:
            perms.unknown.append(token)
            logger.warning(
                "Plugin '{}' declared unknown permission '{}'",
                getattr(module, "PLUGIN_NAME", module.__name__),
                token,
            )

    perms.has_sensitive = bool(perms.sensitive_list())
    logger.debug(
        "Plugin '{}' permissions loaded: granted={} unknown={}",
        getattr(module, "PLUGIN_NAME", module.__name__),
        perms.granted,
        perms.unknown,
    )
    return perms


def enforce(permissions: PluginPermissions, plugin_name: str, token: str) -> None:
    """Raise :class:`SandboxViolation` if *token* is not in *permissions.granted*.

    Call this before executing any capability-gated operation inside a plugin.
    """
    if not permissions.is_allowed(token):
        raise SandboxViolation(plugin_name, token)
