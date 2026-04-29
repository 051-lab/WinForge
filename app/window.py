"""WinForge main window UI."""
from __future__ import annotations

import threading
import webbrowser

import customtkinter as ctk
from loguru import logger

from app import __version__
from app.updater import check_for_updates


class WinForgeApp(ctk.CTk):
    def __init__(self, config=None):
        super().__init__()
        self.config_obj = config
        self.title(f"WinForge v{__version__}")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        self._build_ui()

    def _build_ui(self):
        self.label = ctk.CTkLabel(self, text=f"WinForge v{__version__}", font=("Arial", 24))
        self.label.pack(pady=10)

        self.status = ctk.CTkLabel(self, text="Ready", font=("Arial", 12))
        self.status.pack(pady=10)

        self.update_btn = ctk.CTkButton(
            self,
            text="Check for Updates",
            command=self._start_update_check,
        )
        self.update_btn.pack(pady=10)

        self.update_result_label = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.update_result_label.pack(pady=5)

        logger.info("UI initialized")

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
