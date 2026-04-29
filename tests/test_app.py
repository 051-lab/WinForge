"""Tests for WinForge app."""
import io
import json
import shutil
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


def test_telemetry_enabled_flag_in_features():
    with open("config/features.json") as f:
        feat = json.load(f)
    assert "telemetry_enabled" in feat
    assert feat["telemetry_enabled"] is False


def test_app_version():
    from app import __version__
    assert __version__ == "0.6.0"


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
    payload = {
        "tag_name": "v0.6.0",
        "html_url": "https://github.com/051-lab/WinForge/releases/tag/v0.6.0"
    }
    with patch("urllib.request.urlopen", return_value=_make_response(payload)):
        result = check_for_updates()
    assert result.available is False
    assert result.current == result.latest == "0.6.0"


def test_updater_update_available():
    from app.updater import check_for_updates
    payload = {
        "tag_name": "v0.7.0",
        "html_url": "https://github.com/051-lab/WinForge/releases/tag/v0.7.0"
    }
    with patch("urllib.request.urlopen", return_value=_make_response(payload)):
        result = check_for_updates()
    assert result.available is True
    assert result.latest == "0.7.0"
    assert "v0.7.0" in result.url


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


# --- Plugin marketplace tests ---
def test_discover_plugins_returns_list():
    from app.plugins import discover_plugins
    plugins = discover_plugins()
    assert isinstance(plugins, list)


def test_hello_plugin_discovered():
    from app.plugins import discover_plugins
    plugins = discover_plugins()
    names = [p.name for p in plugins]
    assert "Hello World" in names


def test_hello_plugin_metadata():
    from app.plugins import discover_plugins
    plugins = discover_plugins()
    hello = next(p for p in plugins if p.name == "Hello World")
    assert hello.version == "1.0.0"
    assert hello.author == "051-lab"
    assert "hello" in hello.description.lower()


# --- Telemetry tests ---
def test_telemetry_disabled_by_default(tmp_path, monkeypatch):
    """Telemetry must be opt-in; disabled unless explicitly enabled."""
    import app.telemetry as tel
    monkeypatch.setattr(tel, "_STATE_FILE", tmp_path / "telemetry.json")
    assert tel.is_enabled() is False


def test_telemetry_opt_in(tmp_path, monkeypatch):
    """set_enabled(True) should persist consent and generate install_id."""
    import app.telemetry as tel
    monkeypatch.setattr(tel, "_STATE_FILE", tmp_path / "telemetry.json")
    tel.set_enabled(True)
    assert tel.is_enabled() is True
    assert tel.get_install_id() is not None


def test_telemetry_opt_out(tmp_path, monkeypatch):
    """set_enabled(False) should disable telemetry and return no install_id."""
    import app.telemetry as tel
    monkeypatch.setattr(tel, "_STATE_FILE", tmp_path / "telemetry.json")
    tel.set_enabled(True)
    tel.set_enabled(False)
    assert tel.is_enabled() is False
    assert tel.get_install_id() is None


def test_telemetry_collect_event_disabled(tmp_path, monkeypatch):
    """collect_event returns None when telemetry is off."""
    import app.telemetry as tel
    monkeypatch.setattr(tel, "_STATE_FILE", tmp_path / "telemetry.json")
    result = tel.collect_event("app_start")
    assert result is None


def test_telemetry_collect_event_enabled(tmp_path, monkeypatch):
    """collect_event returns a payload dict when telemetry is on."""
    import app.telemetry as tel
    monkeypatch.setattr(tel, "_STATE_FILE", tmp_path / "telemetry.json")
    tel.set_enabled(True)
    payload = tel.collect_event("app_start", {"extra": "data"})
    assert payload is not None
    assert payload["event"] == "app_start"
    assert "install_id" in payload
    assert payload["extra"] == "data"


# --- Installer tests ---
def test_installer_enabled_by_default(tmp_path, monkeypatch):
    """Plugins not in registry are enabled by default."""
    import app.installer as inst
    monkeypatch.setattr(inst, "_REGISTRY_FILE", tmp_path / "plugins.json")
    assert inst.is_plugin_enabled("my_plugin") is True


def test_installer_disable_plugin(tmp_path, monkeypatch):
    """disable_plugin persists disabled state to registry."""
    import app.installer as inst
    monkeypatch.setattr(inst, "_REGISTRY_FILE", tmp_path / "plugins.json")
    inst.disable_plugin("my_plugin")
    assert inst.is_plugin_enabled("my_plugin") is False


def test_installer_enable_plugin(tmp_path, monkeypatch):
    """enable_plugin re-enables a previously disabled plugin."""
    import app.installer as inst
    monkeypatch.setattr(inst, "_REGISTRY_FILE", tmp_path / "plugins.json")
    inst.disable_plugin("my_plugin")
    inst.enable_plugin("my_plugin")
    assert inst.is_plugin_enabled("my_plugin") is True


def test_installer_uninstall_missing_plugin(tmp_path, monkeypatch):
    """uninstall_plugin returns False when the plugin folder does not exist."""
    import app.installer as inst
    monkeypatch.setattr(inst, "_REGISTRY_FILE", tmp_path / "plugins.json")
    monkeypatch.setattr(inst, "_PLUGINS_DIR", tmp_path / "plugins")
    result = inst.uninstall_plugin("nonexistent_plugin")
    assert result is False


def test_installer_uninstall_existing_plugin(tmp_path, monkeypatch):
    """uninstall_plugin moves plugin folder to archive and returns True."""
    import app.installer as inst
    monkeypatch.setattr(inst, "_REGISTRY_FILE", tmp_path / "plugins.json")
    plugins_dir = tmp_path / "plugins"
    archive_dir = tmp_path / "plugins" / "_uninstalled"
    monkeypatch.setattr(inst, "_PLUGINS_DIR", plugins_dir)
    monkeypatch.setattr(inst, "_ARCHIVE_DIR", archive_dir)
    fake_plugin = plugins_dir / "test_plugin"
    fake_plugin.mkdir(parents=True)
    (fake_plugin / "__init__.py").write_text("PLUGIN_NAME = 'Test'")
    result = inst.uninstall_plugin("test_plugin")
    assert result is True
    assert not fake_plugin.exists()
    assert (archive_dir / "test_plugin").exists()


def test_installer_list_enabled(tmp_path, monkeypatch):
    """list_enabled_plugins returns only plugins marked as enabled."""
    import app.installer as inst
    monkeypatch.setattr(inst, "_REGISTRY_FILE", tmp_path / "plugins.json")
    inst.enable_plugin("alpha")
    inst.enable_plugin("beta")
    inst.disable_plugin("gamma")
    enabled = inst.list_enabled_plugins()
    assert "alpha" in enabled
    assert "beta" in enabled
    assert "gamma" not in enabled


# --- Settings panel tests ---


def test_load_preferences_defaults(tmp_path, monkeypatch):
    """load_preferences returns sensible defaults when no file exists."""
    import app.settings_panel as sp
    monkeypatch.setattr(sp, "_SETTINGS_FILE", tmp_path / "settings.json")
    prefs = sp.load_preferences()
    assert prefs["theme"] == "dark"
    assert prefs["window_width"] == 900
    assert prefs["window_height"] == 650
    assert prefs["telemetry_enabled"] is False


def test_save_and_reload_preferences(tmp_path, monkeypatch):
    """Saved preferences round-trip correctly through load_preferences."""
    import app.settings_panel as sp
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(sp, "_SETTINGS_FILE", settings_file)
    prefs = sp.load_preferences()
    prefs["theme"] = "light"
    prefs["window_width"] = 1200
    prefs["window_height"] = 800
    sp.save_preferences(prefs)
    assert settings_file.exists()
    reloaded = sp.load_preferences()
    assert reloaded["theme"] == "light"
    assert reloaded["window_width"] == 1200
    assert reloaded["window_height"] == 800


def test_save_preferences_creates_parent_dir(tmp_path, monkeypatch):
    """save_preferences creates the config directory if it does not exist."""
    import app.settings_panel as sp
    nested = tmp_path / "a" / "b" / "settings.json"
    monkeypatch.setattr(sp, "_SETTINGS_FILE", nested)
    sp.save_preferences({"theme": "system"})
    assert nested.exists()
    data = json.loads(nested.read_text())
    assert data["theme"] == "system"


def test_load_preferences_merges_with_defaults(tmp_path, monkeypatch):
    """Partial stored prefs are merged with defaults so all keys are present."""
    import app.settings_panel as sp
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(sp, "_SETTINGS_FILE", settings_file)
    settings_file.write_text(json.dumps({"theme": "light"}))
    prefs = sp.load_preferences()
    assert prefs["theme"] == "light"
    assert "window_width" in prefs
    assert "window_height" in prefs


def test_app_version_bumped_to_0_6_0():
    """Version must be 0.6.0 for the Settings UI milestone."""
    from app import __version__
    assert __version__ == "0.6.0"
