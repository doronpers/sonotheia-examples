#!/bin/bash

# Standardization Setup Script
# Use this to quickly apply global standards to any new repository.

# Strict error handling
set -euo pipefail

# Configuration
SOURCE_DIR="${STANDARDS_SOURCE_DIR:-/Volumes/Treehorn/Gits/sonotheia-enhanced/Documentation/Governance}"

# Track operations for summary
OPERATIONS_SUCCESS=()
OPERATIONS_FAILED=()

echo "🚀 Starting Repository Standardization..."
echo "📁 Source directory: $SOURCE_DIR"
echo ""

# Helper: Backup file
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        local backup="${file}.bak.$(date +%s)"
        cp "$file" "$backup"
        echo "📦 Backed up $file to $backup"
    fi
}

# 1. Create Governance Directory
if mkdir -p Documentation/Governance 2>/dev/null; then
    OPERATIONS_SUCCESS+=("Created Documentation/Governance directory")
else
    OPERATIONS_FAILED+=("Failed to create Documentation/Governance directory")
fi

# 2. Deploy Standards Files
if [ -f "$SOURCE_DIR/AGENT_REFORMATTING_GUIDELINES.md" ]; then
    if cat "$SOURCE_DIR/AGENT_REFORMATTING_GUIDELINES.md" > Documentation/Governance/AGENT_REFORMATTING_GUIDELINES.md; then
        OPERATIONS_SUCCESS+=("Deployed AGENT_REFORMATTING_GUIDELINES.md")
    else
        OPERATIONS_FAILED+=("Failed to deploy AGENT_REFORMATTING_GUIDELINES.md")
    fi
else
    echo "⚠️  AGENT_REFORMATTING_GUIDELINES.md not found in $SOURCE_DIR"
    OPERATIONS_FAILED+=("AGENT_REFORMATTING_GUIDELINES.md not found")
fi

if [ -f "$SOURCE_DIR/AGENT_BEHAVIORAL_STANDARDS.md" ]; then
    if cat "$SOURCE_DIR/AGENT_BEHAVIORAL_STANDARDS.md" > Documentation/Governance/AGENT_BEHAVIORAL_STANDARDS.md; then
        OPERATIONS_SUCCESS+=("Deployed AGENT_BEHAVIORAL_STANDARDS.md")
    else
        OPERATIONS_FAILED+=("Failed to deploy AGENT_BEHAVIORAL_STANDARDS.md")
    fi
else
    echo "⚠️  AGENT_BEHAVIORAL_STANDARDS.md not found in $SOURCE_DIR"
    OPERATIONS_FAILED+=("AGENT_BEHAVIORAL_STANDARDS.md not found")
fi

# 3. Create/Update .flake8
backup_file ".flake8"
if cat <<EOF > .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,venv,.venv
EOF
then
    OPERATIONS_SUCCESS+=("Created/updated .flake8")
else
    OPERATIONS_FAILED+=("Failed to create/update .flake8")
fi

# 4. Update root pyproject.toml if it exists
if [ -f "pyproject.toml" ]; then
    backup_file "pyproject.toml"
    echo "Checking pyproject.toml for tool configurations..."
    if ! grep -q "\[tool.black\]" pyproject.toml; then
        if echo -e "\n[tool.black]\nline-length = 88" >> pyproject.toml; then
            OPERATIONS_SUCCESS+=("Added [tool.black] to pyproject.toml")
        else
            OPERATIONS_FAILED+=("Failed to add [tool.black] to pyproject.toml")
        fi
    else
        OPERATIONS_SUCCESS+=("Skipped [tool.black] (already exists)")
    fi
    
    if ! grep -q "\[tool.isort\]" pyproject.toml; then
        if echo -e "\n[tool.isort]\nprofile = \"black\"\nline_length = 88" >> pyproject.toml; then
            OPERATIONS_SUCCESS+=("Added [tool.isort] to pyproject.toml")
        else
            OPERATIONS_FAILED+=("Failed to add [tool.isort] to pyproject.toml")
        fi
    else
        OPERATIONS_SUCCESS+=("Skipped [tool.isort] (already exists)")
    fi
fi

# 5. Add "Priming" instructions to README.md
if [ -f "README.md" ]; then
    if ! grep -q "AGENT_BEHAVIORAL_STANDARDS" README.md; then
        backup_file "README.md"
        if echo -e "\n## Agent Instructions\nThis repository follows [Agent Behavioral Standards](Documentation/Governance/AGENT_BEHAVIORAL_STANDARDS.md). All AI agents MUST read these before performing any tasks." >> README.md; then
            OPERATIONS_SUCCESS+=("Added Agent Instructions to README.md")
        else
            OPERATIONS_FAILED+=("Failed to add Agent Instructions to README.md")
        fi
    else
        OPERATIONS_SUCCESS+=("Skipped README.md update (already contains Agent Instructions)")
    fi
else
    echo "⚠️  README.md not found - skipping agent instructions"
    OPERATIONS_FAILED+=("README.md not found")
fi

# 6. Update .gitignore
if [ ! -f ".gitignore" ]; then
    touch .gitignore
    OPERATIONS_SUCCESS+=("Created .gitignore")
fi
backup_file ".gitignore"

IGNORES=("__pycache__" "*.pyc" ".DS_Store" "venv/" ".venv/" ".env" ".mypy_cache/")
for ignore in "${IGNORES[@]}"; do
    if ! grep -qF "$ignore" .gitignore; then
        echo "$ignore" >> .gitignore
        OPERATIONS_SUCCESS+=("Added $ignore to .gitignore")
    fi
done

# 7. Create/Update .pre-commit-config.yaml
if [ ! -f ".pre-commit-config.yaml" ]; then
    cat <<EOF > .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
EOF
    OPERATIONS_SUCCESS+=("Created .pre-commit-config.yaml")
else
    OPERATIONS_SUCCESS+=("Skipped .pre-commit-config.yaml (already exists)")
fi

# Print summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Standardization Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ${#OPERATIONS_SUCCESS[@]} -gt 0 ]; then
    echo "✅ Successful operations (${#OPERATIONS_SUCCESS[@]}):"
    for op in "${OPERATIONS_SUCCESS[@]}"; do
        echo "   • $op"
    done
fi

if [ ${#OPERATIONS_FAILED[@]} -gt 0 ]; then
    echo ""
    echo "❌ Failed operations (${#OPERATIONS_FAILED[@]}):"
    for op in "${OPERATIONS_FAILED[@]}"; do
        echo "   • $op"
    done
fi

echo ""
if [ ${#OPERATIONS_FAILED[@]} -eq 0 ]; then
    echo "✅ Standardization Complete! Run 'black .' to finalize."
    exit 0
else
    echo "⚠️  Standardization completed with errors. Please review above."
    exit 1
fi
