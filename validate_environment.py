#!/usr/bin/env python3
"""
Comprehensive Environment Validation for VJLive3

Verifies all critical systems are working and no hangs exist.
"""

import sys
import time
import subprocess
import sqlite3
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test all critical module imports"""
    print("1. Testing module imports...")
    try:
        from vjlive3.plugins.api import PluginBase, PluginContext, EffectPlugin
        from vjlive3.plugins.loader import PluginLoader, PluginManifest
        from vjlive3.plugins.registry import PluginRegistry
        from vjlive3.plugins.plugin_runtime import PluginRuntime, SandboxResult
        from vjlive3.plugins.sandbox import PluginSandbox
        from vjlive3.plugins.validator import PluginValidator
        from vjlive3.plugins.hot_reload import PluginHotReloadWatcher
        print("   ✅ All plugin modules import successfully")
        return True
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_instantiation():
    """Test plugin system class instantiation"""
    print("2. Testing plugin system instantiation...")
    try:
        from vjlive3.plugins.api import PluginContext
        from vjlive3.plugins.loader import PluginLoader
        from vjlive3.plugins.registry import PluginRegistry
        from vjlive3.plugins.plugin_runtime import PluginRuntime
        
        class MockEngine:
            def set_parameter(self, path, value): pass
            def get_parameter(self, path): return None
            def emit_event(self, name, data): pass
            def broadcast_event(self, name, data): pass
            def subscribe(self, name, callback): pass
            def schedule(self, delay, callback): pass
        
        context = PluginContext(MockEngine())
        loader = PluginLoader(context)
        registry = PluginRegistry()
        runtime = PluginRuntime(registry)
        print("   ✅ All plugin classes instantiate correctly")
        return True
    except Exception as e:
        print(f"   ❌ Instantiation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_discovery_performance(loader):
    """Test plugin discovery completes quickly (no hangs)"""
    print("3. Testing plugin discovery performance...")
    try:
        start = time.time()
        manifests = loader.discover_plugins()
        elapsed = time.time() - start
        print(f"   ✅ Discovery completed in {elapsed:.6f}s")
        if elapsed > 1.0:
            print(f"   ⚠️  Warning: Discovery took >1s (potential hang risk)")
            return False
        return True
    except Exception as e:
        print(f"   ❌ Discovery error: {e}")
        return False

def test_mcp_servers():
    """Test MCP server responsiveness"""
    print("4. Testing MCP server connectivity...")
    try:
        # Test brain server
        result = subprocess.run(
            [sys.executable, '-m', 'mcp_servers.vjlive3brain.server', '--test'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            print(f"   ❌ Brain server test failed: {result.stderr}")
            return False
        
        # Test switchboard server
        result = subprocess.run(
            [sys.executable, '-m', 'mcp_servers.vjlive_switchboard.server', '--test'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            print(f"   ❌ Switchboard server test failed: {result.stderr}")
            return False
        
        print("   ✅ Both MCP servers responding correctly")
        return True
    except subprocess.TimeoutExpired:
        print("   ❌ MCP server test timed out (hang detected)")
        return False
    except Exception as e:
        print(f"   ❌ MCP server test error: {e}")
        return False

def test_database():
    """Test database connectivity and integrity"""
    print("5. Testing database connectivity...")
    try:
        db_path = Path('mcp_servers/vjlive3brain/brain.db')
        if not db_path.exists():
            print(f"   ❌ Database not found: {db_path}")
            return False
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM concepts")
        count = cursor.fetchone()[0]
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = len(cursor.fetchall())
        conn.close()
        print(f"   ✅ Database OK: {count} concepts, {tables} tables")
        return True
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def test_file_locking():
    """Test file locking system"""
    print("6. Testing file locking system...")
    try:
        locks_file = Path('WORKSPACE/COMMS/LOCKS.md')
        if not locks_file.exists():
            print(f"   ❌ Locks file not found")
            return False
        content = locks_file.read_text()
        if '## Active Locks' not in content:
            print(f"   ❌ Invalid locks file format")
            return False
        print("   ✅ File locking system operational")
        return True
    except Exception as e:
        print(f"   ❌ File locking error: {e}")
        return False

def test_no_hanging_processes():
    """Check for any Python processes in uninterruptible sleep"""
    print("7. Checking for hanging processes...")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')
        python_procs = [l for l in lines if 'python' in l.lower() and 'grep' not in l]
        hanging = [l for l in python_procs if len(l.split()) >= 8 and l.split()[7] == 'D']
        if hanging:
            print(f"   ⚠️  Found {len(hanging)} processes in uninterruptible sleep")
            for h in hanging[:3]:
                print(f"     {h}")
            return False
        print(f"   ✅ No hanging processes ({len(python_procs)} Python processes total)")
        return True
    except Exception as e:
        print(f"   ❌ Process check error: {e}")
        return False

def main():
    print("=" * 60)
    print("VJLive3 Environment Validation")
    print("=" * 60)
    print()
    
    # Create loader for tests that need it
    from vjlive3.plugins.loader import PluginLoader
    from vjlive3.plugins.api import PluginContext
    
    class MockEngine:
        def set_parameter(self, path, value): pass
        def get_parameter(self, path): return None
        def emit_event(self, name, data): pass
        def broadcast_event(self, name, data): pass
        def subscribe(self, name, callback): pass
        def schedule(self, delay, callback): pass
    
    context = PluginContext(MockEngine())
    loader = PluginLoader(context)
    
    tests = [
        test_imports,
        test_instantiation,
        lambda: test_discovery_performance(loader),
        test_mcp_servers,
        test_database,
        test_file_locking,
        test_no_hanging_processes,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
        print()
    
    print("=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("✅ ENVIRONMENT VALIDATED - All systems operational, no hangs")
        return 0
    else:
        print("❌ ENVIRONMENT ISSUES DETECTED - Review failures above")
        return 1

if __name__ == "__main__":
    sys.exit(main())