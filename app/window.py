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
from app.installer import (
    is_plugin_enabled,
    enable_plugin,
    disable_plugin,
    uninstall_plugin,
)


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
        subtitle = ctk.CTkLabel(tab, text="Manage installed plugins", font=("Arial", 11))
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
        """Render a plugin card with Enable/Disable and Uninstall controls."""
        # Use folder name (module name) as the key for installer operations
        folder_name = info.module.__name__.split(".")[-1] if info.module else info.name.lower()
        enabled = is_plugin_enabled(folder_name)

        card = ctk.CTkFrame(self.plugin_frame, corner_radius=8)
        card.pack(fill="x", padx=8, pady=6)

        # Left side: metadata
        meta_frame = ctk.CTkFrame(card, fg_color="transparent")
        meta_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        name_lbl = ctk.CTkLabel(
            meta_frame,
            text=f"{info.name} v{info.version}",
            font=("Arial", 14, "bold"),
            anchor="w",
        )
        name_lbl.pack(anchor="w")

        desc_lbl = ctk.CTkLabel(
            meta_frame,
            text=info.description or "No description provided.",
            font=("Arial", 11),
            anchor="w",
            text_color="gray",
        )
        desc_lbl.pack(anchor="w")

        author_lbl = ctk.CTkLabel(
            meta_frame,
            text=f"by {info.author}",
            font=("Arial", 10),
            anchor="w",
            text_color="#888888",
        )
        author_lbl.pack(anchor="w")

        # Right side: action buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=12, pady=10)

        # Enable/Disable toggle button
        toggle_text = "Disable" if enabled else "Enable"
        toggle_color = "#555555" if enabled else "#2a7a2a"
        status_lbl = ctk.CTkLabel(
            btn_frame,
            text="● Enabled" if enabled else "○ Disabled",
            font=("Arial", 10),
            text_color="#4caf50" if enabled else "#888888",
        )
        status_lbl.pack(pady=(0, 4))

        toggle_btn = ctk.CTkButton(
            btn_frame,
            text=toggle_text,
            width=90,
            fg_color=toggle_color,
            command=lambda fn=folder_name, sl=status_lbl, tb=None: None,  # placeholder
        )

        def make_toggle(fn, sl, tb_ref):
            def _toggle():
                currently = is_plugin_enabled(fn)
                if currently:
                    disable_plugin(fn)
                    sl.configure(text="○ Disabled", text_color="#888888")
                    tb_ref[0].configure(text="Enable", fg_color="#2a7a2a")
                else:
                    enable_plugin(fn)
                    sl.configure(text="● Enabled", text_color="#4caf50")
                    tb_ref[0].configure(text="Disable", fg_color="#555555")
                logger.info("Plugin '{}' toggled", fn)
            return _toggle

        tb_ref = [toggle_btn]
        toggle_btn.configure(command=make_toggle(folder_name, status_lbl, tb_ref))
        toggle_btn.pack(pady=2)

        # Uninstall button
        uninstall_btn = ctk.CTkButton(
            btn_frame,
            text="Uninstall",
            width=90,
            fg_color="#8b0000",
            hover_color="#cc0000",
            command=lambda fn=folder_name: self._confirm_uninstall(fn),
        )
        uninstall_btn.pack(pady=2)

    def _confirm_uninstall(self, folder_name: str):
        """Show a confirmation dialog before uninstalling a plugin."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Uninstall")
        dialog.geometry("380x160")
        dialog.grab_set()

        msg = ctk.CTkLabel(
            dialog,
            text=f"Uninstall plugin '{folder_name}'?\nIt will be archived and removed from the marketplace.",
            font=("Arial", 12),
            justify="center",
        )
        msg.pack(pady=20)

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=5)

        def _do_uninstall():
            dialog.destroy()
            success = uninstall_plugin(folder_name)
            if success:
                self._load_plugins()
                logger.info("Uninstalled plugin: {}", folder_name)
            else:
                logger.warning("Uninstall failed for: {}", folder_name)

        ctk.CTkButton(btn_row, text="Uninstall", fg_color="#8b0000",
                      hover_color="#cc0000", command=_do_uninstall).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Cancel", command=dialog.destroy).pack(side="left", padx=8)

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
