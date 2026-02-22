"""
Tests for P7-B2 Plugin Marketplace Integration.
"""

import pytest
import os
import tempfile
import zipfile
import json
import shutil
from unittest.mock import MagicMock, patch

import requests
from requests.exceptions import RequestException

from vjlive3.plugins.marketplace import (
    PluginMarketplace, MarketplacePlugin, PurchaseResult, 
    DownloadResult, PluginUpdate, InstalledPlugin
)
from vjlive3.plugins.api import PluginContext
from vjlive3.plugins.license_server import LicenseServer, License
from datetime import datetime, timezone

# ─── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def temp_plugins_dir():
    dir_path = tempfile.mkdtemp(prefix="vjlive_test_plugins_")
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)

@pytest.fixture
def mock_license_server():
    server = MagicMock(spec=LicenseServer)
    server.issue_license.return_value = License(
        token="mock_token",
        user_id="user_123",
        plugin_id="p1",
        license_type="standard",
        expires_at=datetime.now(timezone.utc),
        issued_at=datetime.now(timezone.utc),
        revoked=False
    )
    return server

@pytest.fixture
def marketplace(temp_plugins_dir, mock_license_server):
    mp = PluginMarketplace(
        server_url="https://test.marketplace.vjlive.app",
        license_server=mock_license_server
    )
    # mock initialization context
    ctx = MagicMock(spec=PluginContext)
    ctx.get_parameter.side_effect = lambda name: temp_plugins_dir if name == "plugins_dir" else None
    mp.initialize(ctx)
    return mp


# ─── Tests ─────────────────────────────────────────────────────────────

def test_init_no_hardware(marketplace, temp_plugins_dir):
    """Module starts without crashing and initializes directories."""
    assert marketplace.METADATA["name"] == "Plugin Marketplace"
    assert marketplace._server_url == "https://test.marketplace.vjlive.app"
    assert marketplace._plugins_dir == temp_plugins_dir
    assert os.path.exists(temp_plugins_dir)
    marketplace.cleanup()
    assert marketplace.is_connected() is False

@patch("requests.Session.get")
def test_marketplace_connection(mock_get, marketplace):
    """Connects to marketplace server and handles disconnects."""
    # Build a fake response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    marketplace.connect()
    assert marketplace.is_connected() is True
    
    marketplace.disconnect()
    assert marketplace.is_connected() is False
    
    # Simulate network failure
    mock_get.side_effect = RequestException("Network unreachable")
    with pytest.raises(RuntimeError):
        marketplace.connect()
    assert marketplace.is_connected() is False

@patch("requests.Session.get")
def test_plugin_search(mock_get, marketplace):
    """Searches plugins correctly."""
    marketplace._is_connected = True
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "plugin_id": "test_plug",
                "name": "Test Plug",
                "version": "1.0",
                "price_usd": 10.0,
                "is_paid": True
            }
        ]
    }
    mock_get.return_value = mock_response

    results = marketplace.search_plugins("test", {"category": "effects"})
    assert len(results) == 1
    plugin = results[0]
    assert plugin.plugin_id == "test_plug"
    assert plugin.name == "Test Plug"
    assert plugin.is_paid is True
    
    # Auto-connect if offline
    marketplace._is_connected = False
    with patch.object(marketplace, 'connect') as mock_connect:
        mock_connect.side_effect = lambda: setattr(marketplace, '_is_connected', True)
        results = marketplace.search_plugins("test", {})
        assert mock_connect.called
        assert len(results) == 1
        
    # Http error
    mock_get.side_effect = RequestException("Timeout")
    assert marketplace.search_plugins("test", {}) == []

@patch("requests.Session.get")
def test_plugin_details(mock_get, marketplace):
    """Retrieves plugin details and handles featured endpoints."""
    marketplace._is_connected = True
    
    # 1. Detail fetch
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"plugin_id": "details_plug", "name": "Detailed"}
    mock_get.return_value = mock_response
    
    plug = marketplace.get_plugin_details("details_plug")
    assert plug is not None
    assert plug.name == "Detailed"
    
    # 2. 404 handling
    mock_missing = MagicMock()
    mock_missing.status_code = 404
    mock_get.return_value = mock_missing
    
    assert marketplace.get_plugin_details("missing") is None
    
    # 3. Featured
    mock_featured_response = MagicMock()
    mock_featured_response.status_code = 200
    mock_featured_response.json.return_value = {
        "results": [{"plugin_id": "feat_1"}, {"plugin_id": "feat_2"}]
    }
    mock_get.return_value = mock_featured_response
    
    featured = marketplace.get_featured_plugins()
    assert len(featured) == 2
    assert featured[0].plugin_id == "feat_1"
    
    # 4. RequestException in details
    mock_get.side_effect = RequestException("Fail")
    assert marketplace.get_plugin_details("plug") is None

@patch("requests.Session.post")
def test_purchase_flow(mock_post, marketplace, mock_license_server):
    """Purchases plugins successfully and interacts with LicenseServer."""
    marketplace._is_connected = True
    
    # Build success mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "user_id": "user_123",
        "license_type": "pro"
        # No expires_at, should default
    }
    mock_post.return_value = mock_response
    
    result = marketplace.purchase_plugin("p1", "token123")
    assert result.success is True
    assert result.license_token == "mock_token"
    mock_license_server.issue_license.assert_called_once()
    
    # Offline scenario
    marketplace._is_connected = False
    fail1 = marketplace.purchase_plugin("p1", "tok")
    assert fail1.success is False
    assert "offline" in fail1.message.lower()
    
    # Missing LicenseServer
    marketplace._is_connected = True
    marketplace._license_server = None
    fail2 = marketplace.purchase_plugin("p1", "tok")
    assert fail2.success is False
    assert "No LicenseServer" in fail2.message
    
    # API Rejection
    marketplace._license_server = mock_license_server
    mock_reject = MagicMock()
    mock_reject.status_code = 400
    mock_reject.json.return_value = {"error": "Card declined"}
    mock_post.return_value = mock_reject
    fail3 = marketplace.purchase_plugin("p1", "tok")
    assert fail3.success is False
    assert fail3.message == "Card declined"

@patch("requests.Session.get")
@patch.object(PluginMarketplace, "get_plugin_details")
def test_download_install(mock_details, mock_get, marketplace, temp_plugins_dir):
    """Downloads and installs plugins validating zip structure."""
    marketplace._is_connected = True
    
    # Setup details mock
    mock_details.return_value = MarketplacePlugin(
        plugin_id="myplug", name="MyPlug", version="1.0",
        description="", author="", price_usd=0, is_paid=False,
        download_url="http://download.url", rating=0, downloads=0
    )
    
    # We will "mock" the _session.get by writing a real zip to the request mock context.
    # To do this cleanly, we directly create a zip and pass its path to install_plugin.
    # But first test download_plugin's structure
    mock_response_context = MagicMock()
    mock_response_context.__enter__.return_value = MagicMock(
        iter_content=lambda chunk_size: [b"dummy_data"]
    )
    mock_get.return_value = mock_response_context
    
    res = marketplace.download_plugin("myplug", "1.0")
    assert res.success is True
    assert res.plugin_path is not None
    assert os.path.exists(res.plugin_path)
    
    # We need to test install_plugin with a valid zip
    # Clean up the dummy file first
    os.remove(res.plugin_path)
    
    # Create valid zip
    fd, valid_zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    
    with zipfile.ZipFile(valid_zip_path, 'w') as zf:
        manifest = {"plugin_id": "real_plug", "name": "Real Plug", "version": "1.0"}
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("logic.py", "print('hello')")
        
    install_res = marketplace.install_plugin(valid_zip_path)
    assert install_res is True
    assert os.path.exists(os.path.join(temp_plugins_dir, "real_plug", "logic.py"))
    
    # Install invalid zip (no manifest)
    fd2, invalid_zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(fd2)
    with zipfile.ZipFile(invalid_zip_path, 'w') as zf:
        zf.writestr("just_code.py", "pass")
    
    assert marketplace.install_plugin(invalid_zip_path) is False

def test_update_check(marketplace, temp_plugins_dir):
    """Checks for updates correctly."""
    marketplace._is_connected = True
    
    # Create local plugin mock
    os.makedirs(os.path.join(temp_plugins_dir, "local_plug"))
    manifest = {"plugin_id": "local_plug", "version": "1.0"}
    with open(os.path.join(temp_plugins_dir, "local_plug", "manifest.json"), "w") as f:
        json.dump(manifest, f)
        
    assert len(marketplace.get_installed_plugins()) == 1
    
    # Update check returning newer version
    with patch.object(marketplace, 'get_plugin_details') as mock_details:
        mock_details.return_value = MarketplacePlugin(
            plugin_id="local_plug", name="Plug", version="2.0",
            description="", author="", price_usd=0, is_paid=False,
            download_url="test", rating=0, downloads=0
        )
        
        up = marketplace.check_for_updates("local_plug")
        assert up is not None
        assert up.new_version == "2.0"
        
        # Test no update
        mock_details.return_value.version = "1.0"
        assert marketplace.check_for_updates("local_plug") is None

def test_edge_cases(marketplace):
    """Handles various error cases cleanly."""
    # invalid install path
    assert marketplace.install_plugin("/nonexistent/file.zip") is False
    
    # offline calls
    marketplace._is_connected = False
    assert marketplace.get_featured_plugins() == []
    assert marketplace.get_plugin_details("anything") is None
    assert marketplace.check_for_updates("anything") is None
    assert marketplace.download_plugin("anything", "1.0").success is False
    
    # Broken manifest in local install scan
    bad_dir = os.path.join(marketplace._plugins_dir, "bad")
    os.makedirs(bad_dir)
    with open(os.path.join(bad_dir, "manifest.json"), "w") as f:
        f.write("{invalid json")
        
    installed = marketplace.get_installed_plugins()
    # It should skip the bad one, length might be 0 if only bad exists
    assert len(installed) == 0
