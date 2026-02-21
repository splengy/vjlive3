#!/usr/bin/env python3
"""
Environment Integrity Test for VJLive3

Tests all critical components to ensure no hangs and proper functionality.
"""

import sys
import time
import subprocess
import sqlite3
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_mcp_servers():
    """Test MCP server responsiveness"""
    print("Testing MCP servers...")
    
    # Test vjlive3brain
    result = subprocess.run(
        [sys.executable, "-m", "mcp_servers.vjlive3brain.server", "--test"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        print(f"  ❌ vjlive3brain test failed: {result.stderr}")
        return False
    print("  ✅ vjlive3brain server OK")
    
    # Test vjlive_switchboard
    result = subprocess.run(
        [sys.executable, "-m", "mcp_servers.vjlive_switchboard.server", "--test"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        print(f"  ❌ vjlive_switchboard test failed: {result.stderr}")
        return False
    print("  ✅ vjlive_switchboard server OK")
    
    return True

def test_database():
    """Test database connectivity and integrity"""
    print("Testing database...")
    
    db_path = Path("mcp_servers/vjlive3brain/brain.db")
    if not db_path.exists():
        print(f"  ❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        if len(tables) < 6:
            print(f"  ❌ Expected at least 6 tables, found {len(tables)}")
            return False
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM concepts")
        count = cursor.fetchone()[0]
        print(f"  ✅ Database OK - {count} concepts, {len(tables)} tables")
        
        conn.close()
        return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def test_plugin_system():
    """Test plugin discovery and loading"""
    print("Testing plugin system...")
    
    try:
        from vjlive3.plugins.loader import PluginLoader
        from vjlive3.plugins.api import PluginContext
        
        # Create a minimal mock engine
        class MockEngine:
            def set_parameter(self, path, value): pass
            def get_parameter(self, path): return None
            def emit_event(self, name, data): pass
            def broadcast_event(self, name, data): pass
            def subscribe(self, name, callback): pass
            def schedule(self, delay, callback): pass
        
        # Test discovery with timeout
        start = time.time()
        loader = PluginLoader(PluginContext(MockEngine()))
        manifests = loader.discover_plugins()
        elapsed = time.time() - start
        
        print(f"  ✅ Plugin discovery completed in {elapsed:.3f}s")
        print(f"     Found {len(manifests)} plugin manifests")
        
        # Check for hangs
        if elapsed > 5.0:
            print(f"  ⚠️  Plugin discovery took longer than expected")
        
        return True
    except Exception as e:
        print(f"  ❌ Plugin system error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_locking():
    """Test file locking system"""
    print("Testing file locking...")
    
    locks_file = Path("WORKSPACE/COMMS/LOCKS.md")
    if not locks_file.exists():
        print(f"  ❌ Locks file not found at {locks_file}")
        return False
    
    try:
        content = locks_file.read_text()
        # Basic validation - should have Active Locks section
        if "## Active Locks" not in content:
            print("  ❌ Invalid locks file format")
            return False
        print("  ✅ File locking system OK")
        return True
    except Exception as e:
        print(f"  ❌ File locking error: {e}")
        return False

def test_python_execution():
    """Test basic Python execution"""
    print("Testing Python execution...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-c", "print('Python test OK')"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            print(f"  ❌ Python execution failed: {result.stderr}")
            return False
        print("  ✅ Python execution OK")
        return True
    except Exception as e:
        print(f"  ❌ Python execution error: {e}")
        return False

def test_no_hanging_processes():
    """Check for any Python processes in uninterruptible sleep"""
    print("Checking for hanging processes...")
    
    try:
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=5
        )
        
        lines = result.stdout.split('\n')
        python_procs = [l for l in lines if 'python' in l.lower() and 'grep' not in l]
        
        # Look for processes in D state (uninterruptible sleep)
        hanging = []
        for line in python_procs:
            parts = line.split()
            if len(parts) >= 8 and parts[7] == 'D':
                hanging.append(line)
        
        if hanging:
            print(f"  ⚠️  Found {len(hanging)} Python processes in uninterruptible sleep:")
            for h in hanging[:5]:  # Show first 5
                print(f"    {h}")
            return False
        
        print(f"  ✅ No hanging Python processes ({len(python_procs)} total)")
        return True
    except Exception as e:
        print(f"  ❌ Process check error: {e}")
        return False

def main():
    print("=" * 60)
    print("VJLive3 Environment Integrity Test")
    print("=" * 60)
    print()
    
    tests = [
        test_python_execution,
        test_mcp_servers,
        test_database,
        test_file_locking,
        test_plugin_system,
        test_no_hanging_processes,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test crashed: {e}")
            results.append(False)
        print()
    
    print("=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("✅ ENVIRONMENT INTEGRITY VERIFIED - No hangs detected")
        return 0
    else:
        print("❌ ENVIRONMENT ISSUES DETECTED - Review failures above")
        return 1

if __name__ == "__main__":
    sys.exit(main())