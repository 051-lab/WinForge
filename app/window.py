import customtkinter as ctk
from loguru import logger
from app import __version__

class WinForgeWindow(ctk.CTk):
    def __init__(self, config):
        super().__init__()
        self.config_obj = config
        self.title(f"WinForge v{__version__}")
        self.geometry("800x600")
        ctk.set_appearance_mode(self.config_obj.get("theme", "dark"))
        self._build_ui()

    def _build_ui(self):
        self.label = ctk.CTkLabel(self, text=f"WinForge v{__version__}", font=("Arial", 24))
        self.label.pack(pady=40)
        self.status = ctk.CTkLabel(self, text="Ready", font=("Arial", 12))
        self.status.pack(pady=10)
        logger.info("UI initialized")
