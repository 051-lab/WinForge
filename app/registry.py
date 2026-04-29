"""Plugin registry client for fetching plugins from remote sources."""

import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Default registry URL - GitHub repo with plugin manifests
DEFAULT_REGISTRY_URL = "https://raw.githubusercontent.com/051-lab/WinForge-Plugins/main/registry.json"

class PluginRegistry:
    """Client for interacting with the remote plugin registry."""
    
    def __init__(self, registry_url: str = DEFAULT_REGISTRY_URL):
        self.registry_url = registry_url
        self._cache: Optional[Dict] = None
    
    def fetch_registry(self) -> Dict:
        """Fetch the plugin registry from remote source.
        
        Returns:
            Dict containing plugin registry data
        """
        try:
            response = requests.get(self.registry_url, timeout=10)
            response.raise_for_status()
            self._cache = response.json()
            logger.info(f"Successfully fetched registry from {self.registry_url}")
            return self._cache
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch registry: {e}")
            return {"plugins": []}
    
    def list_plugins(self) -> List[Dict]:
        """List all available plugins in the registry.
        
        Returns:
            List of plugin metadata dictionaries
        """
        if not self._cache:
            self.fetch_registry()
        return self._cache.get("plugins", [])
    
    def get_plugin(self, plugin_id: str) -> Optional[Dict]:
        """Get metadata for a specific plugin.
        
        Args:
            plugin_id: Unique identifier for the plugin
        
        Returns:
            Plugin metadata dict or None if not found
        """
        plugins = self.list_plugins()
        for plugin in plugins:
            if plugin.get("id") == plugin_id:
                return plugin
        return None
    
    def download_plugin(self, plugin_id: str, dest_path: str) -> bool:
        """Download a plugin from the registry.
        
        Args:
            plugin_id: Unique identifier for the plugin
            dest_path: Destination path to save the plugin file
        
        Returns:
            True if download successful, False otherwise
        """
        plugin_meta = self.get_plugin(plugin_id)
        if not plugin_meta:
            logger.error(f"Plugin {plugin_id} not found in registry")
            return False
        
        download_url = plugin_meta.get("download_url")
        if not download_url:
            logger.error(f"No download URL for plugin {plugin_id}")
            return False
        
        try:
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()
            
            with open(dest_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded plugin {plugin_id} to {dest_path}")
            return True
        except (requests.exceptions.RequestException, IOError) as e:
            logger.error(f"Failed to download plugin {plugin_id}: {e}")
            return False
