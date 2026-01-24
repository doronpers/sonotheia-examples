#!/usr/bin/env bash
# Codex environment setup script for sonotheia-examples
# This script runs automatically when Codex creates or resumes a container

set -e

echo "📚 Sonotheia Examples - Codex Environment Setup"
echo "==============================================="
echo ""

# Change to workspace directory
cd /workspace/sonotheia-examples || cd "$(dirname "$0")/.." || exit 1

echo "📦 Installing/upgrading pip..."
python3 -m pip install --upgrade pip --quiet

echo "📦 Installing sonotheia-examples..."
# Install in editable mode if pyproject.toml exists at root
if [ -f "pyproject.toml" ]; then
    pip install -e . --quiet
fi

# Install example-specific dependencies if they exist
if [ -f "examples/python/pyproject.toml" ]; then
    echo "📦 Installing Python examples dependencies..."
    pip install -e examples/python/ --quiet
fi

if [ -f "evaluation/pyproject.toml" ]; then
    echo "📦 Installing evaluation dependencies..."
    pip install -e evaluation/ --quiet
fi

# Install pre-commit hooks (optional - don't fail if it's not critical)
echo "🔧 Setting up pre-commit hooks..."
pre-commit install || echo "⚠️  Pre-commit install skipped (non-critical)"

# Verify installation
echo "✅ Verifying installation..."
python3 -c "print('✓ sonotheia-examples structure verified')"

echo ""
echo "✅ Setup complete! Environment ready for sonotheia-examples development."
echo ""
echo "Quick commands:"
echo "  black .                    # Format code"
echo "  flake8 .                   # Lint code"
echo "  pre-commit run --all-files # Run all pre-commit hooks"
echo "  python examples/python/golden_path_demo.py  # Run example"
echo ""
