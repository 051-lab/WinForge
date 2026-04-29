"""Tests for WinForge app."""
import io
import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


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
    assert __version__ == "0.2.0"


def test_config_load():
    from app.config import Config
    c = Config()
    assert c.get("version") == "0.1.0"


# --- Updater tests ---

def _make_response(payload: dict):
    """Build a mock urlopen context manager returning JSON bytes."""
    data = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = data
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_updater_up_to_date():
    from app.updater import check_for_updates
    payload = {"tag_name": "v0.2.0", "html_url": "https://github.com/051-lab/WinForge/releases/tag/v0.2.0"}
    with patch("urllib.request.urlopen", return_value=_make_response(payload)):
        result = check_for_updates()
    assert result.available is False
    assert result.current == result.latest == "0.2.0"


def test_updater_update_available():
    from app.updater import check_for_updates
    payload = {"tag_name": "v0.3.0", "html_url": "https://github.com/051-lab/WinForge/releases/tag/v0.3.0"}
    with patch("urllib.request.urlopen", return_value=_make_response(payload)):
        result = check_for_updates()
    assert result.available is True
    assert result.latest == "0.3.0"
    assert "v0.3.0" in result.url


def test_updater_network_error():
    from app.updater import check_for_updates
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        result = check_for_updates()
    assert result.available is False


def test_updater_malformed_json():
    from app.updater import check_for_updates
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"not-json-at-all{{{"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = check_for_updates()
    assert result.available is False
