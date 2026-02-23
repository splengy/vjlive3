import coverage
import pytest
import sys
import json

cov = coverage.Coverage(source=['vjlive3.plugins.depth_r16_wave'])
cov.start()

sys.argv = ['pytest', 'tests/plugins/test_depth_r16_wave.py', '-v']
pytest.main()

cov.stop()
cov.save()

percent = cov.html_report()
print(f"COVERAGE_PERCENTAGE={percent}")
