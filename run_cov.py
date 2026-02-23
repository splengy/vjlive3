import coverage
import pytest
import sys

cov = coverage.Coverage(source=['vjlive3.plugins.depth_color_grade'])
cov.start()

sys.argv = ['pytest', 'tests/plugins/test_depth_color_grade.py', '-v']
pytest.main()

cov.stop()
cov.save()

percent = cov.html_report()
print(f"COVERAGE_PERCENTAGE={percent}")
