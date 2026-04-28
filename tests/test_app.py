import pytest
import json
from pathlib import Path

def test_settings_json_exists():
    assert Path("config/settings.json").exists()

def test_features_json_exists():
    assert Path("config/features.json").exists()

def test_settings_version():
    with open("config/settings.json") as f:
        s = json.load(f)
    assert s["version"] == "0.1.0"

def test_feature_flags_present():
    with open("config/features.json") as f:
        feat = json.load(f)
    assert "plugin_system" in feat

def test_app_version():
    from app import __version__
    assert __version__ == "0.1.0"

def test_config_load():
    from app.config import Config
    c = Config()
    assert c.get("version") == "0.1.0"
