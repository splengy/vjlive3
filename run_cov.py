import coverage
import pytest
import sys

cov = coverage.Coverage(source=['vjlive3.plugins.depth_edge_glow'])
cov.start()

sys.argv = ['pytest', 'tests/plugins/test_depth_edge_glow.py', '-v']
pytest.main()

cov.stop()
cov.save()

percent = cov.html_report()
print(f"COVERAGE_PERCENTAGE={percent}")
