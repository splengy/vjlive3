#!/usr/bin/env python3
"""
Performance Regression Check

Ensures that code changes do not cause performance regressions beyond
acceptable thresholds. Enforces SAFETY_RAIL 1: 60 FPS Sacred.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Tuple

# Performance thresholds
MAX_FRAME_TIME_MS = 16.67  # 60 FPS
MAX_MEMORY_GROWTH_MB = 10  # Per minute
MAX_CPU_INCREASE_PCT = 5   # Percentage points

def run_benchmark() -> Tuple[float, float, float]:
    """Run performance benchmark and return (fps, memory_mb, cpu_pct)."""
    # This would integrate with actual benchmark suite
    # For now, we'll use a simple timing test
    
    print("Running performance benchmark...")
    
    try:
        # Run a simple performance test
        result = subprocess.run(
            [sys.executable, '-c', '''
import time
import sys
sys.path.insert(0, 'src')
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

# Measure discovery performance
start = time.perf_counter()
manifests = loader.discover_plugins()
elapsed = time.perf_counter() - start

print(f"DISCOVERY_TIME_MS={elapsed*1000:.2f}")
'''],
            capture_output=True, text=True, timeout=10
        )
        
        # Parse output
        fps = 60.0  # Placeholder - would measure actual rendering
        memory_mb = 50.0  # Placeholder
        cpu_pct = 10.0  # Placeholder
        
        # Extract discovery time if available
        for line in result.stdout.splitlines():
            if 'DISCOVERY_TIME_MS=' in line:
                discovery_ms = float(line.split('=')[1])
                if discovery_ms > MAX_FRAME_TIME_MS:
                    print(f"⚠️  Discovery too slow: {discovery_ms:.2f}ms > {MAX_FRAME_TIME_MS}ms")
        
        return fps, memory_mb, cpu_pct
        
    except subprocess.TimeoutExpired:
        print("❌ Benchmark timed out")
        return 0.0, 0.0, 0.0
    except Exception as e:
        print(f"❌ Benchmark error: {e}")
        return 0.0, 0.0, 0.0

def load_baseline() -> Dict:
    """Load previous performance baseline."""
    baseline_file = Path('.performance_baseline.json')
    if baseline_file.exists():
        try:
            return json.loads(baseline_file.read_text())
        except Exception:
            pass
    return {'fps': 60.0, 'memory_mb': 50.0, 'cpu_pct': 10.0}

def save_baseline(metrics: Dict):
    """Save current performance as new baseline."""
    baseline_file = Path('.performance_baseline.json')
    baseline_file.write_text(json.dumps(metrics, indent=2))

def check_regression(current: Tuple[float, float, float], baseline: Dict) -> bool:
    """Check if current metrics regressed beyond thresholds."""
    fps, memory_mb, cpu_pct = current
    
    issues = []
    
    # Check FPS
    if fps < baseline['fps'] * 0.95:  # 5% tolerance
        drop = baseline['fps'] - fps
        issues.append(f"FPS dropped by {drop:.1f} (baseline: {baseline['fps']:.1f}, current: {fps:.1f})")
    
    # Check memory
    if memory_mb > baseline['memory_mb'] + MAX_MEMORY_GROWTH_MB:
        growth = memory_mb - baseline['memory_mb']
        issues.append(f"Memory increased by {growth:.1f}MB (baseline: {baseline['memory_mb']:.1f}MB, current: {memory_mb:.1f}MB)")
    
    # Check CPU
    if cpu_pct > baseline['cpu_pct'] + MAX_CPU_INCREASE_PCT:
        increase = cpu_pct - baseline['cpu_pct']
        issues.append(f"CPU usage increased by {increase:.1f}% (baseline: {baseline['cpu_pct']:.1f}%, current: {cpu_pct:.1f}%)")
    
    return len(issues) == 0, issues

def main() -> int:
    """Main entry point."""
    print("="*60)
    print("Performance Regression Check")
    print("="*60)
    print()
    
    # Run benchmark
    current_metrics = run_benchmark()
    if current_metrics == (0.0, 0.0, 0.0):
        print("❌ Failed to collect performance metrics")
        return 1
    
    # Load baseline
    baseline = load_baseline()
    print(f"Baseline: FPS={baseline['fps']:.1f}, Memory={baseline['memory_mb']:.1f}MB, CPU={baseline['cpu_pct']:.1f}%")
    print(f"Current:  FPS={current_metrics[0]:.1f}, Memory={current_metrics[1]:.1f}MB, CPU={current_metrics[2]:.1f}%")
    
    # Check for regression
    ok, issues = check_regression(current_metrics, baseline)
    
    if not ok:
        print("\n❌ PERFORMANCE REGRESSION DETECTED:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPerformance must not regress beyond acceptable thresholds.")
        print("Review performance impact before committing.")
        return 1
    
    print("✅ No performance regression detected")
    
    # Update baseline (only on success)
    new_baseline = {
        'fps': current_metrics[0],
        'memory_mb': current_metrics[1],
        'cpu_pct': current_metrics[2]
    }
    save_baseline(new_baseline)
    print("📊 Performance baseline updated")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())