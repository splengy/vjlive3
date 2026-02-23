import coverage
import pytest
import sys

cov = coverage.Coverage(source=['vjlive3.plugins.depth_erosion_datamosh'])
cov.start()

sys.argv = ['pytest', 'tests/plugins/test_depth_erosion_datamosh.py', '-v']
pytest.main()

cov.stop()
cov.save()

percent = cov.html_report()
print(f"COVERAGE_PERCENTAGE={percent}")
