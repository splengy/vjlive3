#!/usr/bin/env bash
#
# VJLive3 Project Initialization Script
#
# This script sets up a complete development environment for VJLive3.
# It creates the virtual environment, installs dependencies, sets up
# pre-commit hooks, and verifies the installation.
#
# Usage:
#   ./setup.sh [options]
#
# Options:
#   --skip-venv      Skip virtual environment creation
#   --skip-deps      Skip dependency installation
#   --skip-hooks     Skip pre-commit hook installation
#   --force          Force reinstallation even if already set up
#   --help           Show this help message
#
# Example:
#   ./setup.sh
#   ./setup.sh --skip-venv  # If you already have a venv

set -e  # Exit on error
set -u  # Error on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
SKIP_VENV=false
SKIP_DEPS=false
SKIP_HOOKS=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-venv)
            SKIP_VENV=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --skip-hooks)
            SKIP_HOOKS=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            grep "^# " "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}VJLive3 Project Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if already set up
if [[ -d ".venv" ]] && [[ "$FORCE" == "false" ]]; then
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
    echo -e "${YELLOW}Use --force to reinstall.${NC}"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Step 1: Check Python
echo -e "${BLUE}[1/7] Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.9+ and try again.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Python $PYTHON_VERSION detected, but Python $REQUIRED_VERSION+ is required.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION is compatible${NC}"

# Step 2: Create virtual environment
if [[ "$SKIP_VENV" == "false" ]]; then
    echo -e "${BLUE}[2/7] Creating virtual environment...${NC}"

    # Remove existing venv if force
    if [[ -d ".venv" ]] && [[ "$FORCE" == "true" ]]; then
        echo -e "${YELLOW}Removing existing virtual environment...${NC}"
        rm -rf .venv
    fi

    # Create venv
    python3 -m venv .venv

    # Activate venv
    source .venv/bin/activate

    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}[2/7] Skipping virtual environment creation${NC}"
    source .venv/bin/activate 2>/dev/null || true
fi

# Step 3: Upgrade pip
echo -e "${BLUE}[3/7] Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✓ pip upgraded${NC}"

# Step 4: Install dependencies
if [[ "$SKIP_DEPS" == "false" ]]; then
    echo -e "${BLUE}[4/7] Installing dependencies...${NC}"

    # Install package with dev dependencies
    pip install -e ".[dev]"

    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${YELLOW}[4/7] Skipping dependency installation${NC}"
fi

# Step 5: Set up pre-commit hooks
if [[ "$SKIP_HOOKS" == "false" ]]; then
    echo -e "${BLUE}[5/7] Setting up pre-commit hooks...${NC}"

    if command -v pre-commit &> /dev/null; then
        pre-commit install
        echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
    else
        echo -e "${YELLOW}⚠ pre-commit not found, skipping${NC}"
    fi
else
    echo -e "${YELLOW}[5/7] Skipping pre-commit hooks${NC}"
fi

# Step 6: Create necessary directories
echo -e "${BLUE}[6/7] Creating necessary directories...${NC}"

# Create logs directory
mkdir -p logs

# Create config directory if not exists
mkdir -p config

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo "# VJLive3 Environment Configuration" > .env
    echo "# Copy this file to .env and fill in values" >> .env
    echo "" >> .env
    echo "# Development settings" >> .env
    echo "DEBUG=True" >> .env
    echo "LOG_LEVEL=INFO" >> .env
    echo "" >> .env
    echo "# Add your API keys and secrets below" >> .env
    echo "# API_KEY=your_key_here" >> .env
    echo "" >> .env
    echo -e "${GREEN}✓ Created .env template${NC}"
else
    echo -e "${YELLOW}⚠ .env already exists, skipping${NC}"
fi

# Create .gitkeep files in empty directories
find . -type d -empty -not -path "*/\.*" -exec touch {}/.gitkeep \;

echo -e "${GREEN}✓ Directories created${NC}"

# Step 7: Verify installation
echo -e "${BLUE}[7/7] Verifying installation...${NC}"

# Check if we can import the package
if python3 -c "import vjlive3; print(f'VJLive3 {vjlive3.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✓ VJLive3 package imports successfully${NC}"
else
    echo -e "${RED}✗ VJLive3 package import failed${NC}"
    echo -e "${YELLOW}Try running: pip install -e .${NC}"
fi

# Check if pytest is available
if command -v pytest &> /dev/null; then
    echo -e "${GREEN}✓ pytest is available${NC}"
else
    echo -e "${YELLOW}⚠ pytest not found${NC}"
fi

# Check if pre-commit is available
if command -v pre-commit &> /dev/null; then
    echo -e "${GREEN}✓ pre-commit is available${NC}"
else
    echo -e "${YELLOW}⚠ pre-commit not found${NC}"
fi

# Check if black, isort, ruff, mypy are available
for tool in black isort ruff mypy bandit safety; do
    if command -v "$tool" &> /dev/null; then
        echo -e "${GREEN}✓ $tool is available${NC}"
    else
        echo -e "${YELLOW}⚠ $tool not found${NC}"
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Setup complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  1. Activate the virtual environment:"
echo -e "     ${YELLOW}source .venv/bin/activate${NC}  (or on Windows: .venv\\Scripts\\activate)"
echo ""
echo "  2. Run the demo application:"
echo -e "     ${YELLOW}make run${NC}"
echo ""
echo "  3. Run tests to verify everything works:"
echo -e "     ${YELLOW}make test${NC}"
echo ""
echo "  4. Check code quality:"
echo -e "     ${YELLOW}make quality${NC}"
echo ""
echo "  5. Read the getting started guide:"
echo -e "     ${YELLOW}cat GETTING_STARTED.md${NC}"
echo ""
echo "For more information, see:"
echo "  - README.md (project overview)"
echo "  - GETTING_STARTED.md (detailed guide)"
echo "  - CONTRIBUTING.md (contribution guidelines)"
echo "  - STYLE_GUIDE.md (coding standards)"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""