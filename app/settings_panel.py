"""WinForge Settings Panel - persistent user preferences UI."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import customtkinter as ctk
from loguru import logger
from app import telemetry

_SETTINGS_FILE = Path("config/settings.json")

# Defaults shipped with the app
_DEFAULTS: Dict[str, Any] = {
    "theme": "dark",
    "window_width": 900,
    "window_height": 650,
    "telemetry_enabled": False,
}


def load_preferences() -> Dict[str, Any]:
    """Load user preferences from disk, merging with defaults."""
    prefs = dict(_DEFAULTS)
    if _SETTINGS_FILE.exists():
        try:
            stored = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
            prefs.update(stored)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to read settings: {}", exc)
    return prefs


def save_preferences(prefs: Dict[str, Any]) -> None:
    """Persist user preferences to disk."""
    try:
        _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SETTINGS_FILE.write_text(json.dumps(prefs, indent=2), encoding="utf-8")
        logger.info("Settings saved.")
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to save settings: {}", exc)


class SettingsPanel(ctk.CTkFrame):
    """A CustomTkinter frame that exposes user-configurable preferences.

    Preferences are loaded from / persisted to config/settings.json.
    The parent window is notified via *apply_callback* when the user
    saves changes so it can respond (e.g. resize or retheme itself).
    """

    def __init__(self, master: Any, apply_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self._prefs = load_preferences()
        self._apply_callback = apply_callback
        self._build()

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------

    def _build(self) -> None:
        """Construct all settings widgets."""
        pad = {"padx": 20, "pady": 8}

        # Header
        ctk.CTkLabel(
            self, text="Settings", font=("Arial", 22, "bold")
        ).pack(anchor="w", **pad)

        ctk.CTkLabel(
            self, text="Appearance", font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=20, pady=(16, 2))

        # Theme selector
        theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(theme_frame, text="Theme:", width=140, anchor="w").pack(
            side="left"
        )
        self._theme_var = ctk.StringVar(value=self._prefs.get("theme", "dark"))
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["dark", "light", "system"],
            variable=self._theme_var,
        )
        theme_menu.pack(side="left")

        ctk.CTkLabel(
            self, text="Window", font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=20, pady=(16, 2))

        # Window width
        width_frame = ctk.CTkFrame(self, fg_color="transparent")
        width_frame.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(width_frame, text="Window width:", width=140, anchor="w").pack(
            side="left"
        )
        self._width_var = ctk.StringVar(
            value=str(self._prefs.get("window_width", 900))
        )
        ctk.CTkEntry(width_frame, textvariable=self._width_var, width=80).pack(
            side="left"
        )

        # Window height
        height_frame = ctk.CTkFrame(self, fg_color="transparent")
        height_frame.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(height_frame, text="Window height:", width=140, anchor="w").pack(
            side="left"
        )
        self._height_var = ctk.StringVar(
            value=str(self._prefs.get("window_height", 650))
        )
        ctk.CTkEntry(height_frame, textvariable=self._height_var, width=80).pack(
            side="left"
        )

        ctk.CTkLabel(
            self, text="Privacy", font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=20, pady=(16, 2))

        # Telemetry toggle
        telem_frame = ctk.CTkFrame(self, fg_color="transparent")
        telem_frame.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(
            telem_frame, text="Enable telemetry:", width=140, anchor="w"
        ).pack(side="left")
        self._telem_var = ctk.BooleanVar(
            value=bool(self._prefs.get("telemetry_enabled", False))
        )
        ctk.CTkSwitch(
            telem_frame, text="", variable=self._telem_var, onvalue=True, offvalue=False
        ).pack(side="left")

        # Save button
        ctk.CTkButton(
            self, text="Save Settings", command=self._on_save, width=160
        ).pack(anchor="w", padx=20, pady=(24, 8))

        # Status label
        self._status_label = ctk.CTkLabel(self, text="", text_color="#4caf50")
        self._status_label.pack(anchor="w", padx=20)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_save(self) -> None:
        """Validate inputs, persist preferences and notify the app."""
        try:
            w = int(self._width_var.get())
            h = int(self._height_var.get())
            if w < 400 or w > 3840 or h < 300 or h > 2160:
                raise ValueError("Dimensions out of range")
        except ValueError:
            self._status_label.configure(
                text="Invalid dimensions (width 400-3840, height 300-2160).",
                text_color="#f44336",
            )
            return

        self._prefs["theme"] = self._theme_var.get()
        self._prefs["window_width"] = w
        self._prefs["window_height"] = h
        self._prefs["telemetry_enabled"] = self._telem_var.get()

        save_preferences(self._prefs)

        # Sync telemetry module
        telemetry.set_enabled(self._telem_var.get())

        # Apply appearance mode immediately
        ctk.set_appearance_mode(self._prefs["theme"])

        self._status_label.configure(
            text="Settings saved successfully.", text_color="#4caf50"
        )
        logger.info("Preferences applied: {}", self._prefs)

        if self._apply_callback:
            self._apply_callback(self._prefs)
