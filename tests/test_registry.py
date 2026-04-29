"""Tests for plugin registry and auto-install functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.registry import PluginRegistry
from app.plugins import install_plugin_from_registry
import requests


class TestPluginRegistry:
    """Test cases for PluginRegistry class."""
    
    def test_registry_init(self):
        """Test registry initialization."""
        registry = PluginRegistry()
        assert registry.registry_url is not None
        assert registry._cache is None
    
    def test_fetch_registry_success(self):
        """Test successful registry fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {"plugins": [{"id": "test-plugin"}]}
        
        with patch('requests.get', return_value=mock_response):
            registry = PluginRegistry()
            data = registry.fetch_registry()
            
            assert "plugins" in data
            assert len(data["plugins"]) == 1
            assert data["plugins"][0]["id"] == "test-plugin"
    
    def test_fetch_registry_failure(self):
        """Test registry fetch with network error."""
        with patch('requests.get', side_effect=requests.exceptions.RequestException("Network error")):
            registry = PluginRegistry()
            data = registry.fetch_registry()
            
            assert data == {"plugins": []}
    
    def test_list_plugins(self):
        """Test listing all plugins."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "plugins": [
                {"id": "plugin1", "name": "Plugin 1"},
                {"id": "plugin2", "name": "Plugin 2"}
            ]
        }
        
        with patch('requests.get', return_value=mock_response):
            registry = PluginRegistry()
            plugins = registry.list_plugins()
            
            assert len(plugins) == 2
            assert plugins[0]["id"] == "plugin1"
            assert plugins[1]["id"] == "plugin2"
    
    def test_get_plugin_found(self):
        """Test getting a specific plugin that exists."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "plugins": [
                {"id": "test-plugin", "name": "Test Plugin", "version": "1.0.0"}
            ]
        }
        
        with patch('requests.get', return_value=mock_response):
            registry = PluginRegistry()
            plugin = registry.get_plugin("test-plugin")
            
            assert plugin is not None
            assert plugin["id"] == "test-plugin"
            assert plugin["version"] == "1.0.0"
    
    def test_get_plugin_not_found(self):
        """Test getting a plugin that doesn't exist."""
        mock_response = Mock()
        mock_response.json.return_value = {"plugins": []}
        
        with patch('requests.get', return_value=mock_response):
            registry = PluginRegistry()
            plugin = registry.get_plugin("nonexistent-plugin")
            
            assert plugin is None
    
    def test_download_plugin_success(self, tmp_path):
        """Test successful plugin download."""
        mock_plugin_response = Mock()
        mock_plugin_response.json.return_value = {
            "plugins": [{
                "id": "test-plugin",
                "download_url": "https://example.com/plugin.py"
            }]
        }
        
        mock_download_response = Mock()
        mock_download_response.content = b"# Plugin code"
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [mock_plugin_response, mock_download_response]
            
            registry = PluginRegistry()
            dest_file = tmp_path / "plugin.py"
            result = registry.download_plugin("test-plugin", str(dest_file))
            
            assert result is True
            assert dest_file.exists()
            assert dest_file.read_text() == "# Plugin code"
    
    def test_download_plugin_not_found(self):
        """Test downloading a plugin that doesn't exist."""
        mock_response = Mock()
        mock_response.json.return_value = {"plugins": []}
        
        with patch('requests.get', return_value=mock_response):
            registry = PluginRegistry()
            result = registry.download_plugin("nonexistent", "/tmp/plugin.py")
            
            assert result is False
    
    def test_download_plugin_no_url(self):
        """Test downloading a plugin with no download URL."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "plugins": [{"id": "test-plugin"}]  # Missing download_url
        }
        
        with patch('requests.get', return_value=mock_response):
            registry = PluginRegistry()
            result = registry.download_plugin("test-plugin", "/tmp/plugin.py")
            
            assert result is False


class TestInstallPluginFromRegistry:
    """Test cases for install_plugin_from_registry function."""
    
    def test_install_success(self, tmp_path):
        """Test successful plugin installation."""
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        
        mock_registry = Mock(spec=PluginRegistry)
        mock_registry.get_plugin.return_value = {
            "id": "test-plugin",
            "filename": "test_plugin.py"
        }
        mock_registry.download_plugin.return_value = True
        
        with patch('app.plugins.PluginRegistry', return_value=mock_registry):
            result = install_plugin_from_registry("test-plugin", str(plugins_dir))
            
            assert result is True
            mock_registry.get_plugin.assert_called_once_with("test-plugin")
    
    def test_install_plugin_not_found(self, tmp_path):
        """Test installing a plugin that doesn't exist in registry."""
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        
        mock_registry = Mock(spec=PluginRegistry)
        mock_registry.get_plugin.return_value = None
        
        with patch('app.plugins.PluginRegistry', return_value=mock_registry):
            result = install_plugin_from_registry("nonexistent", str(plugins_dir))
            
            assert result is False
    
    def test_install_download_fails(self, tmp_path):
        """Test installation when download fails."""
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        
        mock_registry = Mock(spec=PluginRegistry)
        mock_registry.get_plugin.return_value = {
            "id": "test-plugin",
            "filename": "test_plugin.py"
        }
        mock_registry.download_plugin.return_value = False
        
        with patch('app.plugins.PluginRegistry', return_value=mock_registry):
            result = install_plugin_from_registry("test-plugin", str(plugins_dir))
            
            assert result is False
