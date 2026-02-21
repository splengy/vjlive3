#!/usr/bin/env python3
"""
Project Setup Verification Script

This script verifies that the VJLive3 project is correctly set up
and all required files and directories are in place.

Usage:
    python scripts/verify_setup.py [--fix]

Options:
    --fix    Attempt to fix missing files/directories
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.resolve()


def check_file(path: Path, description: str) -> bool:
    """Check if a file exists and report."""
    if path.exists():
        print(f"  ✓ {description}: {path.name}")
        return True
    else:
        print(f"  ✗ {description}: MISSING - {path}")
        return False


def check_directory(path: Path, description: str) -> bool:
    """Check if a directory exists and report."""
    if path.exists() and path.is_dir():
        print(f"  ✓ {description}: {path.name}/")
        return True
    else:
        print(f"  ✗ {description}: MISSING - {path}/")
        return False


def verify_project_structure() -> bool:
    """Verify the complete project structure."""
    print("\n" + "=" * 60)
    print("VJLive3 Project Structure Verification")
    print("=" * 60 + "\n")

    all_ok = True

    # Check root files
    print("Root Files:")
    all_ok &= check_file(project_root / "README.md", "Project README")
    all_ok &= check_file(project_root / "GETTING_STARTED.md", "Getting Started Guide")
    all_ok &= check_file(project_root / "CONTRIBUTING.md", "Contributing Guide")
    all_ok &= check_file(project_root / "STYLE_GUIDE.md", "Style Guide")
    all_ok &= check_file(project_root / "TESTING_STRATEGY.md", "Testing Strategy")
    all_ok &= check_file(project_root / "ARCHITECTURE.md", "Architecture Document")
    all_ok &= check_file(project_root / "MODULE_MANIFEST.md", "Module Manifest")
    all_ok &= check_file(project_root / "SECURITY.md", "Security Policy")
    all_ok &= check_file(project_root / "DEFINITION_OF_DONE.md", "Definition of Done")
    all_ok &= check_file(project_root / "CHANGELOG.md", "Changelog")
    all_ok &= check_file(project_root / "CODE_OF_CONDUCT.md", "Code of Conduct")
    all_ok &= check_file(project_root / "LICENSE", "License")
    all_ok &= check_file(project_root / "pyproject.toml", "Project Configuration")
    all_ok &= check_file(project_root / "Makefile", "Makefile")
    all_ok &= check_file(project_root / ".pre-commit-config.yaml", "Pre-commit Config")
    all_ok &= check_file(project_root / ".editorconfig", "EditorConfig")
    all_ok &= check_file(project_root / ".gitignore", "Git Ignore")
    all_ok &= check_file(project_root / ".env.example", "Environment Example")
    all_ok &= check_file(project_root / "setup.sh", "Setup Script")

    # Check directories
    print("\nDirectories:")
    all_ok &= check_directory(project_root / "src", "Source Code")
    all_ok &= check_directory(project_root / "tests", "Tests")
    all_ok &= check_directory(project_root / "docs", "Documentation")
    all_ok &= check_directory(project_root / "config", "Configuration")
    all_ok &= check_directory(project_root / "scripts", "Scripts")
    all_ok &= check_directory(project_root / ".github", "GitHub Config")
    all_ok &= check_directory(project_root / ".github/workflows", "CI/CD Workflows")

    # Check source structure
    print("\nSource Code Structure:")
    all_ok &= check_directory(project_root / "src/vjlive3", "Main Package")
    all_ok &= check_directory(project_root / "src/vjlive3/core", "Core Module")
    all_ok &= check_directory(project_root / "src/vjlive3/effects", "Effects Module")
    all_ok &= check_directory(project_root / "src/vjlive3/sources", "Sources Module")
    all_ok &= check_directory(project_root / "src/vjlive3/utils", "Utils Module")

    # Check source files
    print("\nSource Files:")
    all_ok &= check_file(project_root / "src/vjlive3/__init__.py", "Package Init")
    all_ok &= check_file(project_root / "src/vjlive3/main.py", "Main Entry Point")
    all_ok &= check_file(project_root / "src/vjlive3/core/__init__.py", "Core Init")
    all_ok &= check_file(project_root / "src/vjlive3/core/pipeline.py", "Pipeline")
    all_ok &= check_file(project_root / "src/vjlive3/effects/__init__.py", "Effects Init")
    all_ok &= check_file(project_root / "src/vjlive3/effects/base.py", "Effect Base")
    all_ok &= check_file(project_root / "src/vjlive3/effects/blur.py", "Blur Effect")
    all_ok &= check_file(project_root / "src/vjlive3/effects/color.py", "Color Effect")
    all_ok &= check_file(project_root / "src/vjlive3/effects/distort.py", "Distort Effect")
    all_ok &= check_file(project_root / "src/vjlive3/sources/__init__.py", "Sources Init")
    all_ok &= check_file(project_root / "src/vjlive3/sources/base.py", "Source Base")
    all_ok &= check_file(project_root / "src/vjlive3/sources/generator.py", "Generator Source")
    all_ok &= check_file(project_root / "src/vjlive3/utils/__init__.py", "Utils Init")
    all_ok &= check_file(project_root / "src/vjlive3/utils/logging.py", "Logging Utils")
    all_ok &= check_file(project_root / "src/vjlive3/utils/image.py", "Image Utils")
    all_ok &= check_file(project_root / "src/vjlive3/utils/perf.py", "Performance Utils")
    all_ok &= check_file(project_root / "src/vjlive3/utils/security.py", "Security Utils")
    all_ok &= check_file(project_root / "src/vjlive3/utils/quality.py", "Quality Utils")

    # Check test structure
    print("\nTest Structure:")
    all_ok &= check_directory(project_root / "tests/unit", "Unit Tests")
    all_ok &= check_directory(project_root / "tests/integration", "Integration Tests")
    all_ok &= check_directory(project_root / "tests/e2e", "E2E Tests")
    all_ok &= check_directory(project_root / "tests/performance", "Performance Tests")
    all_ok &= check_file(project_root / "tests/conftest.py", "Test Configuration")
    all_ok &= check_file(project_root / "tests/unit/test_core_pipeline.py", "Pipeline Tests")
    all_ok &= check_file(project_root / "tests/unit/test_effects.py", "Effects Tests")
    all_ok &= check_file(project_root / "tests/unit/test_sources.py", "Sources Tests")

    # Check documentation
    print("\nDocumentation:")
    all_ok &= check_directory(project_root / "docs/decisions", "ADR Directory")
    all_ok &= check_file(project_root / "docs/decisions/README.md", "ADR Guide")
    all_ok &= check_file(project_root / "docs/decisions/ADR_000_TEMPLATE.md", "ADR Template")
    all_ok &= check_file(project_root / "docs/decisions/ADR_001_initial-project-structure.md", "Initial ADR")
    all_ok &= check_file(project_root / "docs/README.md", "Documentation Index")

    # Check scripts
    print("\nScripts:")
    all_ok &= check_file(project_root / "scripts/quality_report.py", "Quality Report Script")
    all_ok &= check_file(project_root / "scripts/verify_setup.py", "Verification Script")

    # Check CI/CD
    print("\nCI/CD:")
    all_ok &= check_file(project_root / ".github/workflows/ci.yml", "CI/CD Pipeline")

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ All checks passed! Project structure is complete.")
    else:
        print("❌ Some checks failed. Review the output above.")
    print("=" * 60 + "\n")

    return all_ok


def verify_python_imports() -> bool:
    """Verify that Python imports work correctly."""
    print("\n" + "=" * 60)
    print("Python Import Verification")
    print("=" * 60 + "\n")

    all_ok = True

    # Add src to path
    sys.path.insert(0, str(project_root / "src"))

    # Test imports
    modules_to_test = [
        "vjlive3",
        "vjlive3.core",
        "vjlive3.core.pipeline",
        "vjlive3.effects",
        "vjlive3.effects.base",
        "vjlive3.effects.blur",
        "vjlive3.effects.color",
        "vjlive3.effects.distort",
        "vjlive3.sources",
        "vjlive3.sources.base",
        "vjlive3.sources.generator",
        "vjlive3.utils",
        "vjlive3.utils.logging",
        "vjlive3.utils.image",
        "vjlive3.utils.perf",
        "vjlive3.utils.security",
        "vjlive3.utils.quality",
    ]

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name}")
        except ImportError as e:
            print(f"  ✗ {module_name}: {e}")
            all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ All imports successful!")
    else:
        print("❌ Some imports failed.")
    print("=" * 60 + "\n")

    return all_ok


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify VJLive3 project setup")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix missing files/directories",
    )
    args = parser.parse_args()

    structure_ok = verify_project_structure()
    imports_ok = verify_python_imports()

    if structure_ok and imports_ok:
        print("\n✅ Project verification PASSED")
        print("You can now run: make install")
        print("Then: make test")
        return 0
    else:
        print("\n❌ Project verification FAILED")
        print("Please review the errors above and fix them.")
        if args.fix:
            print("\nAttempting to fix...")
            # Could add auto-fix logic here
        return 1


if __name__ == "__main__":
    sys.exit(main())