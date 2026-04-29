"""WinForge main window UI."""
from __future__ import annotations
import threading
import webbrowser

import customtkinter as ctk
from loguru import logger

from app import __version__
from app.plugins import discover_plugins
from app.updater import check_for_updates
from app.telemetry import is_enabled, set_enabled


class WinForgeApp(ctk.CTk):
    def __init__(self, config=None):
        super().__init__()
        self.config_obj = config
        self.title(f"WinForge v{__version__}")
        self.geometry("900x650")
        ctk.set_appearance_mode("dark")
        self._build_ui()

    def _build_ui(self):
        # Tab view
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabs.add("Home")
        self.tabs.add("Marketplace")
        self.tabs.add("Privacy")

        self._build_home_tab()
        self._build_marketplace_tab()
        self._build_privacy_tab()
        logger.info("UI initialized")

    # ------------------------------------------------------------------
    # Home tab
    # ------------------------------------------------------------------
    def _build_home_tab(self):
        tab = self.tabs.tab("Home")
        self.label = ctk.CTkLabel(tab, text=f"WinForge v{__version__}", font=("Arial", 24))
        self.label.pack(pady=20)
        self.status = ctk.CTkLabel(tab, text="Ready", font=("Arial", 12))
        self.status.pack(pady=5)
        self.update_btn = ctk.CTkButton(
            tab,
            text="Check for Updates",
            command=self._start_update_check,
        )
        self.update_btn.pack(pady=10)
        self.update_result_label = ctk.CTkLabel(tab, text="", font=("Arial", 12))
        self.update_result_label.pack(pady=5)

    # ------------------------------------------------------------------
    # Marketplace tab
    # ------------------------------------------------------------------
    def _build_marketplace_tab(self):
        tab = self.tabs.tab("Marketplace")
        header = ctk.CTkLabel(tab, text="Plugin Marketplace", font=("Arial", 20, "bold"))
        header.pack(pady=(15, 5))
        subtitle = ctk.CTkLabel(tab, text="Installed plugins discovered automatically", font=("Arial", 11))
        subtitle.pack(pady=(0, 10))
        # Scrollable frame for plugin cards
        self.plugin_frame = ctk.CTkScrollableFrame(tab, label_text="")
        self.plugin_frame.pack(fill="both", expand=True, padx=10, pady=5)
        refresh_btn = ctk.CTkButton(tab, text="Refresh", width=100, command=self._load_plugins)
        refresh_btn.pack(pady=8)
        self._load_plugins()

    def _load_plugins(self):
        # Clear existing cards
        for widget in self.plugin_frame.winfo_children():
            widget.destroy()
        plugins = discover_plugins()
        if not plugins:
            empty = ctk.CTkLabel(
                self.plugin_frame,
                text="No plugins found. Drop a plugin folder into plugins/ to get started.",
                font=("Arial", 12),
                text_color="gray",
            )
            empty.pack(pady=20)
            return
        for info in plugins:
            self._add_plugin_card(info)

    def _add_plugin_card(self, info):
        card = ctk.CTkFrame(self.plugin_frame, corner_radius=8)
        card.pack(fill="x", padx=8, pady=6)
        name_lbl = ctk.CTkLabel(
            card,
            text=f"{info.name} v{info.version}",
            font=("Arial", 14, "bold"),
            anchor="w",
        )
        name_lbl.pack(anchor="w", padx=12, pady=(10, 2))
        desc_lbl = ctk.CTkLabel(
            card,
            text=info.description or "No description provided.",
            font=("Arial", 11),
            anchor="w",
            text_color="gray",
        )
        desc_lbl.pack(anchor="w", padx=12, pady=(0, 2))
        author_lbl = ctk.CTkLabel(
            card,
            text=f"by {info.author}",
            font=("Arial", 10),
            anchor="w",
            text_color="#888888",
        )
        author_lbl.pack(anchor="w", padx=12, pady=(0, 10))

    # ------------------------------------------------------------------
    # Privacy tab
    # ------------------------------------------------------------------
    def _build_privacy_tab(self):
        tab = self.tabs.tab("Privacy")
        header = ctk.CTkLabel(tab, text="Privacy & Telemetry", font=("Arial", 20, "bold"))
        header.pack(pady=(20, 5))

        desc = ctk.CTkLabel(
            tab,
            text=(
                "WinForge can collect anonymous usage data to help improve the app.\n"
                "No personal data is ever collected. You can opt in or out at any time."
            ),
            font=("Arial", 12),
            text_color="gray",
            justify="center",
        )
        desc.pack(pady=(0, 20))

        # Toggle switch
        self._telemetry_var = ctk.BooleanVar(value=is_enabled())
        self.telemetry_switch = ctk.CTkSwitch(
            tab,
            text="Enable anonymous usage telemetry",
            variable=self._telemetry_var,
            command=self._on_telemetry_toggle,
            font=("Arial", 13),
        )
        self.telemetry_switch.pack(pady=10)

        self.telemetry_status_label = ctk.CTkLabel(
            tab,
            text=self._telemetry_status_text(),
            font=("Arial", 11),
            text_color="gray",
        )
        self.telemetry_status_label.pack(pady=5)

        privacy_note = ctk.CTkLabel(
            tab,
            text="Your choice is saved locally and never shared without your consent.",
            font=("Arial", 10),
            text_color="#666666",
        )
        privacy_note.pack(pady=(20, 0))

    def _telemetry_status_text(self) -> str:
        return "Status: Opted IN" if is_enabled() else "Status: Opted OUT (default)"

    def _on_telemetry_toggle(self):
        new_value = bool(self._telemetry_var.get())
        set_enabled(new_value)
        self.telemetry_status_label.configure(text=self._telemetry_status_text())
        logger.info("Telemetry toggled to: {}", new_value)

    # ------------------------------------------------------------------
    # Update checker
    # ------------------------------------------------------------------
    def _start_update_check(self):
        self.update_btn.configure(state="disabled", text="Checking...")
        self.update_result_label.configure(text="", text_color="white")
        threading.Thread(target=self._run_update_check, daemon=True).start()

    def _run_update_check(self):
        result = check_for_updates()
        self.after(0, self._show_update_result, result)

    def _show_update_result(self, result):
        self.update_btn.configure(state="normal", text="Check for Updates")
        if result.available:
            msg = f"Update available: v{result.latest}"
            self.update_result_label.configure(text=msg, text_color="yellow", cursor="hand2")
            self.update_result_label.bind(
                "<Button-1>",
                lambda _e: webbrowser.open(result.url),
            )
        else:
            self.update_result_label.configure(
                text="Up to date", text_color="green", cursor=""
            )
        self.update_result_label.unbind("<Button-1>")
