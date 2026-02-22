"""
P7-B2: Plugin Marketplace Integration

Connects VJLive3 to an online marketplace where users can discover, purchase, 
and download plugins. Handles basic plugin tracking, updates, and purchasing.
"""

import logging
import os
import tempfile
import zipfile
import shutil
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

import requests

from vjlive3.plugins.api import PluginBase, PluginContext
from vjlive3.plugins.license_server import LicenseServer

_logger = logging.getLogger("vjlive3.plugins.marketplace")


@dataclass
class MarketplacePlugin:
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    price_usd: float
    is_paid: bool
    download_url: str
    rating: float
    downloads: int


@dataclass
class PurchaseResult:
    success: bool
    message: str
    license_token: Optional[str] = None


@dataclass
class DownloadResult:
    success: bool
    plugin_path: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class PluginUpdate:
    plugin_id: str
    current_version: str
    new_version: str
    download_url: str


@dataclass
class InstalledPlugin:
    plugin_id: str
    name: str
    version: str
    path: str


class PluginMarketplace(PluginBase):
    """
    Plugin Marketplace Integration.
    Complies with P7-B2 specifications for plugin discovery, download, and installation.
    """
    
    METADATA = {
        "name": "Plugin Marketplace",
        "description": "Connects to the official VJLive plugin marketplace.",
        "version": "1.0.0",
        "author": "VJLive Team",
        "category": "core.business",
        "parameters": [
            {"name": "server_url", "type": "string", "default": "https://marketplace.vjlive.app"},
            {"name": "plugins_dir", "type": "string", "default": "plugins_installed"},
        ],
        "inputs": [],
        "outputs": []
    }

    def __init__(self, server_url: str = "https://marketplace.vjlive.app", license_server: Optional[LicenseServer] = None) -> None:
        super().__init__()
        self._server_url = server_url.rstrip("/")
        self._license_server = license_server
        self._is_connected = False
        self._plugins_dir = "plugins_installed"
        
        # Requests session for pooling/auth
        self._session = requests.Session()

    def initialize(self, context: PluginContext) -> None:
        """Initialize parameters from context and prepare directories."""
        super().initialize(context)
        
        param_url = self.context.get_parameter("server_url")
        if param_url:
            self._server_url = str(param_url).rstrip("/")
            
        param_dir = self.context.get_parameter("plugins_dir")
        if param_dir:
            self._plugins_dir = str(param_dir)
            
        os.makedirs(self._plugins_dir, exist_ok=True)

    def cleanup(self) -> None:
        """Cleanup network connections and temp files."""
        _logger.debug("Cleaning up PluginMarketplace connection pool.")
        self.disconnect()
        super().cleanup()

    # ─── Connection Management ───────────────────────────────────────────────

    def connect(self) -> None:
        """Attempt to connect to the marketplace API."""
        try:
            response = self._session.get(f"{self._server_url}/api/status", timeout=5)
            response.raise_for_status()
            self._is_connected = True
            _logger.info("Connected to marketplace at %s", self._server_url)
        except requests.RequestException as e:
            self._is_connected = False
            _logger.warning("Failed to connect to marketplace: %s", e)
            raise RuntimeError(f"Could not connect to marketplace: {e}")

    def disconnect(self) -> None:
        """Disconnect from the marketplace API."""
        self._session.close()
        self._is_connected = False
        _logger.info("Disconnected from marketplace.")

    def is_connected(self) -> bool:
        """Check if currently connected to the marketplace."""
        return self._is_connected

    # ─── Discovery ───────────────────────────────────────────────────────────

    def _parse_plugin(self, data: Dict[str, Any]) -> MarketplacePlugin:
        return MarketplacePlugin(
            plugin_id=data.get('plugin_id', ''),
            name=data.get('name', 'Unknown'),
            version=data.get('version', '0.0.0'),
            description=data.get('description', ''),
            author=data.get('author', 'Unknown'),
            price_usd=float(data.get('price_usd', 0.0)),
            is_paid=bool(data.get('is_paid', False)),
            download_url=data.get('download_url', ''),
            rating=float(data.get('rating', 0.0)),
            downloads=int(data.get('downloads', 0))
        )

    def search_plugins(self, query: str, filters: Dict[str, Any]) -> List[MarketplacePlugin]:
        """Search the marketplace for plugins matching query and filters."""
        if not self._is_connected:
            _logger.warning("Searching while disconnected; attempting auto-connect.")
            try:
                self.connect()
            except RuntimeError:
                return []
                
        params = {"q": query}
        if filters:
            params.update(filters)
            
        try:
            url = f"{self._server_url}/api/plugins/search?{urlencode(params)}"
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            for item in data.get('results', []):
                results.append(self._parse_plugin(item))
            return results
        except (requests.RequestException, ValueError) as e:
            _logger.error("Error searching plugins: %s", e)
            return []

    def get_plugin_details(self, plugin_id: str) -> Optional[MarketplacePlugin]:
        """Get detailed information about a specific plugin."""
        if not self._is_connected:
            return None
            
        try:
            url = f"{self._server_url}/api/plugins/{plugin_id}"
            response = self._session.get(url, timeout=5)
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            data = response.json()
            return self._parse_plugin(data)
        except (requests.RequestException, ValueError) as e:
            _logger.error("Error fetching plugin details for %s: %s", plugin_id, e)
            return None

    def get_featured_plugins(self) -> List[MarketplacePlugin]:
        """Fetch the current featured plugins curated by the marketplace."""
        if not self._is_connected:
            return []
            
        try:
            url = f"{self._server_url}/api/plugins/featured"
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            for item in data.get('results', []):
                results.append(self._parse_plugin(item))
            return results
        except (requests.RequestException, ValueError) as e:
            _logger.error("Error fetching featured plugins: %s", e)
            return []

    # ─── Commerce ────────────────────────────────────────────────────────────

    def purchase_plugin(self, plugin_id: str, payment_token: str) -> PurchaseResult:
        """
        Purchase a plugin using an external payment token.
        Delegates the final license creation to the LicenseServer.
        """
        if not self._is_connected:
            return PurchaseResult(success=False, message="Marketplace is offline.")
            
        if not self._license_server:
            return PurchaseResult(success=False, message="No LicenseServer configured for issuance.")
            
        try:
            # 1. Contact marketplace to validate payment token and authorize purchase
            url = f"{self._server_url}/api/payments/checkout"
            payload = {"plugin_id": plugin_id, "payment_token": payment_token}
            
            response = self._session.post(url, json=payload, timeout=15)
            
            if response.status_code != 200:
                msg = "Purchase failed"
                try:
                    msg = response.json().get('error', msg)
                except ValueError:
                    pass
                return PurchaseResult(success=False, message=msg)
                
            purchase_data = response.json()
            user_id = purchase_data.get('user_id', 'unknown_user')
            license_type = purchase_data.get('license_type', 'standard')
            expires_timestamp = purchase_data.get('expires_at')
            
            from datetime import datetime, timezone, timedelta
            
            # Construct expiration
            if expires_timestamp:
                expires_at = datetime.fromtimestamp(expires_timestamp, tz=timezone.utc)
            else:
                expires_at = datetime.now(timezone.utc) + timedelta(days=365) # Default 1 year
                
            # 2. Issue Local License via injected P7-B1 Server
            issued_license = self._license_server.issue_license(
                user_id=user_id,
                plugin_id=plugin_id,
                license_type=license_type,
                expires_at=expires_at
            )
            
            return PurchaseResult(
                success=True, 
                message="Purchase successful.", 
                license_token=issued_license.token
            )
            
        except requests.RequestException as e:
            _logger.error("Network error during purchase: %s", e)
            return PurchaseResult(success=False, message="Network error during transaction.")

    # ─── Download and Install ────────────────────────────────────────────────

    def download_plugin(self, plugin_id: str, version: str) -> DownloadResult:
        """Download a plugin package from the marketplace."""
        if not self._is_connected:
            return DownloadResult(success=False, error_message="Marketplace is offline.")
            
        # Get plugin details to find the correct download URL
        plugin = self.get_plugin_details(plugin_id)
        if not plugin:
            return DownloadResult(success=False, error_message="Plugin not found.")
            
        # Optional: in reality we might hit a specific /version/ endpoint
        download_url = plugin.download_url
        if not download_url:
            return DownloadResult(success=False, error_message="No download URL provided by marketplace.")
            
        try:
            # Create a temp file to hold the download
            fd, temp_path = tempfile.mkstemp(suffix=".zip", prefix=f"plugin_{plugin_id}_")
            os.close(fd)
            
            with self._session.get(download_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(temp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
            return DownloadResult(success=True, plugin_path=temp_path)
            
        except requests.RequestException as e:
            _logger.error("Download failed for %s: %s", plugin_id, e)
            return DownloadResult(success=False, error_message=f"Download failed: {e}")

    def install_plugin(self, plugin_path: str) -> bool:
        """Extract and install a downloaded plugin package."""
        if not plugin_path or not os.path.exists(plugin_path):
            _logger.error("Invalid plugin path for installation: %s", plugin_path)
            return False
            
        os.makedirs(self._plugins_dir, exist_ok=True)
            
        try:
            # Extract to a temporary directory first to inspect manifest
            extract_dir = tempfile.mkdtemp(prefix="vjlive_extract_")
            try:
                with zipfile.ZipFile(plugin_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                    
                # Look for manifest
                manifest_path = os.path.join(extract_dir, "manifest.json")
                if not os.path.exists(manifest_path):
                    # Sometimes the zip has a single root folder wrapping the contents
                    dirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
                    if len(dirs) == 1:
                        nested_dir = os.path.join(extract_dir, dirs[0])
                        nested_manifest = os.path.join(nested_dir, "manifest.json")
                        if os.path.exists(nested_manifest):
                            manifest_path = nested_manifest
                            extract_dir = nested_dir # Point to the nested directory
                            
                if not os.path.exists(manifest_path):
                    _logger.error("Invalid plugin package: missing manifest.json")
                    return False
                    
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    
                plugin_id = manifest.get('plugin_id') or manifest.get('id')
                if not plugin_id:
                    _logger.error("Invalid manifest: missing plugin_id")
                    return False
                    
                # Move to final destination
                final_dest = os.path.join(self._plugins_dir, plugin_id)
                
                # Remove existing prior to overwrite
                if os.path.exists(final_dest):
                    shutil.rmtree(final_dest)
                    
                shutil.copytree(extract_dir, final_dest)
                
                _logger.info("Successfully installed plugin %s to %s", plugin_id, final_dest)
                return True
                
            finally:
                # Clean up extraction temp dir
                parent_extract = extract_dir
                while parent_extract.startswith(tempfile.gettempdir()) and os.path.exists(parent_extract):
                    shutil.rmtree(parent_extract, ignore_errors=True)
                    break
        except Exception as e:
            _logger.error("Installation failed: %s", e)
            return False
        finally:
            # Clean up the original zip file
            if os.path.exists(plugin_path):
                try:
                    os.remove(plugin_path)
                except OSError:
                    pass

    # ─── Updates and Local State ─────────────────────────────────────────────

    def get_installed_plugins(self) -> List[InstalledPlugin]:
        """Scan local plugin directory to find installed plugins and their versions."""
        installed = []
        if not os.path.exists(self._plugins_dir):
            return installed
            
        for d in os.listdir(self._plugins_dir):
            plugin_path = os.path.join(self._plugins_dir, d)
            if not os.path.isdir(plugin_path):
                continue
                
            manifest_path = os.path.join(plugin_path, "manifest.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        plugin_id = manifest.get('plugin_id') or manifest.get('id') or d
                        installed.append(InstalledPlugin(
                            plugin_id=plugin_id,
                            name=manifest.get('name', 'Unknown'),
                            version=manifest.get('version', '0.0.0'),
                            path=plugin_path
                        ))
                except (json.JSONDecodeError, IOError):
                    continue
                    
        return installed

    def check_for_updates(self, plugin_id: str) -> Optional[PluginUpdate]:
        """Check if an update is available for a specific installed plugin."""
        if not self._is_connected:
            return None
            
        installed = [p for p in self.get_installed_plugins() if p.plugin_id == plugin_id]
        if not installed:
            return None
            
        local_plugin = installed[0]
        
        # Consult marketplace for latest
        remote_plugin = self.get_plugin_details(plugin_id)
        if not remote_plugin:
            return None
            
        # Naive string comparison for versions (assuming semver). 
        # In a real scenario, use pkg_resources.parse_version
        if remote_plugin.version > local_plugin.version:
            return PluginUpdate(
                plugin_id=plugin_id,
                current_version=local_plugin.version,
                new_version=remote_plugin.version,
                download_url=remote_plugin.download_url
            )
            
        return None
