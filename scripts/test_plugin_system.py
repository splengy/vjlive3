#!/usr/bin/env python3
"""Test the plugin system for Phase 1 Gate verification."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vjlive3.plugins.registry import get_registry
from vjlive3.plugins.loader import get_loader


def test_plugin_system():
    """Test that plugin discovery and loading works."""
    print("=" * 60)
    print("Plugin System Test — Phase 1 Gate Verification")
    print("=" * 60)
    
    # Get registry and loader
    registry = get_registry()
    loader = get_loader()
    
    # Discover plugins
    print("\n1. Discovering plugins...")
    manifests = registry.discover()
    print(f"   Found {len(manifests)} plugin manifest(s)")
    for manifest in manifests:
        print(f"   - {manifest.name} v{manifest.version} ({manifest.plugin_type})")
    
    # Load all plugins
    print("\n2. Loading plugins...")
    plugins = loader.discover_and_load_all()
    print(f"   Loaded {len(plugins)} plugin(s)")
    for plugin in plugins:
        print(f"   - {plugin.manifest.name} v{plugin.manifest.version}")
    
    # Test plugin functionality
    print("\n3. Testing plugin functionality...")
    for plugin in plugins:
        try:
            # Test process with sample data
            test_data = {"test": "data"}
            result = plugin.process(test_data)
            print(f"   ✓ {plugin.manifest.name}.process() returned {type(result).__name__}")
            
            # Test parameters
            params = plugin.get_parameters()
            print(f"   ✓ {plugin.manifest.name}.get_parameters() = {params}")
            
        except Exception as e:
            print(f"   ✗ {plugin.manifest.name} failed: {e}")
            return False
    
    # Unload plugins
    print("\n4. Unloading plugins...")
    loader.unload_all()
    print("   All plugins unloaded")
    
    print("\n" + "=" * 60)
    print("✅ Plugin system test PASSED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_plugin_system()
    sys.exit(0 if success else 1)