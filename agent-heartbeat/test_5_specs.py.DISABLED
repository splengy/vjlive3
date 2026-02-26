#!/usr/bin/env python3
"""
Test 5 specs through the Julie pipeline.
Runs heartbeat for 5 representative tasks and reports results.
"""
import subprocess
import sys
import time

TASKS = [
    ("P3-EXT001", "ascii_effect (ASCIIEffect) - Port the ASCII art post-processing effect from VJlive-2"),
    ("P3-EXT006", "analog_tv (AnalogTVEffect) - Port the analog TV scanline/static/tracking effect from VJlive-2"),
    ("P3-EXT007", "arbhar_granular_engine (ArbharGranularEngine) - Port the Arbhar granular audio engine from VJlive-2"),
    ("P3-EXT013", "bad_trip_datamosh (BadTripDatamoshEffect) - Port the horror-style datamosh effect from VJlive-2"),
    ("P3-EXT017", "pop_art_effects (BenDayDotsEffect) - Port the Ben Day halftone pop art effect from VJlive-2"),
]

PROJECT = str(Path(os.path.dirname(os.path.abspath(__file__))).parent)
results = []

for i, (task_id, desc) in enumerate(TASKS, 1):
    output = f"docs/specs/{task_id}_spec.md"
    print(f"\n{'='*60}")
    print(f"[{i}/5] {task_id}: {desc[:60]}...")
    print(f"{'='*60}")

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, "agent-heartbeat/heartbeat.py", task_id, desc, output],
            capture_output=True,
            text=True,
            timeout=180,  # 3 minutes per task
            cwd=PROJECT,
        )
        elapsed = time.time() - start
        success = result.returncode == 0
        results.append((task_id, success, elapsed, result.returncode))

        print(f"  {'✅ PASS' if success else '❌ FAIL'} ({elapsed:.1f}s)")
        if not success:
            # Show last 10 lines of output for debugging
            lines = (result.stdout + result.stderr).strip().split('\n')
            for line in lines[-10:]:
                print(f"  | {line}")
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        results.append((task_id, False, elapsed, -1))
        print(f"  ⏰ TIMEOUT ({elapsed:.1f}s)")
    except Exception as e:
        elapsed = time.time() - start
        results.append((task_id, False, elapsed, -2))
        print(f"  💥 ERROR: {e}")

print(f"\n{'='*60}")
print("RESULTS SUMMARY")
print(f"{'='*60}")
passed = sum(1 for _, s, _, _ in results if s)
for task_id, success, elapsed, rc in results:
    status = "✅" if success else "❌"
    print(f"  {status} {task_id}: {elapsed:.1f}s (exit={rc})")
print(f"\n  {passed}/5 passed")
