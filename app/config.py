from pathlib import Path
import json
from loguru import logger

class Config:
    def __init__(self):
        self.config_dir = Path("config")
        self.settings_path = self.config_dir / "settings.json"
        self.features_path = self.config_dir / "features.json"
        self._settings = {}
        self._features = {}
        self._load()

    def _load(self):
        try:
            if self.settings_path.exists():
                with open(self.settings_path) as f:
                    self._settings = json.load(f)
            if self.features_path.exists():
                with open(self.features_path) as f:
                    self._features = json.load(f)
        except Exception as e:
            logger.error(f"Config load error: {e}")

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def feature_enabled(self, name):
        return self._features.get(name, False)
