# Sonotheia-Examples: Quick Action Plan

**Prepared**: January 27, 2026  
**Total Estimated Effort**: 25-26 hours to 100% production-ready  
**Current Status**: 72% production-ready

---

## 🎯 Priority Actions (Copy-Paste Ready)

### P0-1: Fix Pytest Collection Errors [3 HOURS]

```bash
# Step 1: Diagnose
cd /Volumes/Treehorn/Gits/sonotheia-examples
python -m pytest examples/python/tests/test_main.py -vv 2>&1 | tee diagnosis.txt

# Step 2: Review diagnosis output for import/fixture errors

# Step 3: Create/Fix examples/python/conftest.py
cat > examples/python/conftest.py << 'EOF'
import pytest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from simple_api_client import SonotheiaClient
    CLIENT_AVAILABLE = True
except ImportError as e:
    CLIENT_AVAILABLE = False
    print(f"Warning: Client import failed: {e}")

@pytest.fixture
def test_api_key():
    return "test_key_12345"

@pytest.fixture
def test_audio_file():
    return b"mock_audio_data"
EOF

# Step 4: Verify
pytest --co -q examples/python/tests/ | tail -5
```

**Expected Output**:

```
193 tests collected, 0 errors
```

---

### P0-2: Fix Tool Configuration [30 MINUTES]

```bash
# Edit pyproject.toml and replace [tool.ruff] section

# ADD (if missing):
cat >> pyproject.toml << 'EOF'

[tool.ruff]
line-length = 100
target-version = "py39"
select = ["E", "F", "W", "I"]
EOF

# Verify all three tools configured to line-length = 100:
grep -A 2 "tool.black\|tool.ruff\|tool.isort" pyproject.toml
```

---

### P0-3: Fix Line Length Violations [30 MINUTES]

```bash
# Find all violations
ruff check examples/ evaluation/ --select E501 2>&1 | head -20

# Fix violations interactively:
# 1. examples/terraform/aws/lambda/audio_processor.py:40
# 2. examples/terraform/aws/lambda/audio_processor.py:73

# Manual edits (break long strings):
sed -i 's/raise ValueError(f"Missing required environment variables: {\x27, \x27\.join(missing)}")/error_msg = f"Missing required environment variables: {'"'"', '"'"'\.join(missing)}")\n        raise ValueError(error_msg)/' examples/terraform/aws/lambda/audio_processor.py

# Verify
ruff check examples/terraform/ --select E501
```

**After P0-1, P0-2, P0-3**: ✅ **~82% Completion**

---

### P1-1: Add Optional Dependency Fallbacks [4 HOURS]

```bash
# Step 1: Scan for unconditional optional imports
grep -r "^import torch\|^import transformers\|^import plotly" evaluation/src examples/python | grep -v "\.md"

# Step 2: Apply pattern to each file
# CREATE: evaluation/src/optional_deps.py

cat > evaluation/src/optional_deps.py << 'EOF'
"""Optional dependency management."""

TORCH_AVAILABLE = False
TRANSFORMERS_AVAILABLE = False
PLOTLY_AVAILABLE = False
PANDAS_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None

try:
    import transformers
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    transformers = None

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    px = None

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
EOF

# Step 3: Update imports across codebase
# Example (evaluation/src/audio_trust_harness/indicators/ml_detector.py):

# BEFORE:
import torch
from transformers import AutoModel

# AFTER:
from optional_deps import TORCH_AVAILABLE, torch, TRANSFORMERS_AVAILABLE
import numpy as np

# Step 4: Test with missing deps
pip uninstall -y torch transformers
pytest evaluation/tests/ -v
# Should pass with graceful fallback
```

---

### P1-2: Set Up Pre-Commit Hooks [1.5 HOURS]

```bash
# Step 1: Install pre-commit
pip install pre-commit

# Step 2: Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        args: [--line-length=100, --fix]

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--line-length=100]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-ll, -r]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=1000]
EOF

# Step 3: Install hooks
pre-commit install

# Step 4: Run against all files
pre-commit run --all-files
```

---

### P1-3: Standardize Imports [3 HOURS]

```bash
# Step 1: Auto-fix import sorting
ruff check --fix examples/ evaluation/ --select I

# Step 2: Convert absolute to relative imports
# SCRIPT: convert_to_relative.py
cat > convert_to_relative.py << 'EOF'
import re
import sys
from pathlib import Path

def convert_imports(file_path):
    content = Path(file_path).read_text()
    
    # Pattern: from audio_validator import ...
    # Replace with: from .audio_validator import ...
    
    content = re.sub(
        r'^from (audio_validator|config_validator|mock_api_server)',
        r'from .\1',
        content,
        flags=re.MULTILINE
    )
    
    Path(file_path).write_text(content)
    print(f"✓ {file_path}")

# Apply to all Python files
for py_file in Path('.').rglob('*.py'):
    if '.venv' not in str(py_file) and '__pycache__' not in str(py_file):
        convert_imports(py_file)
EOF

python convert_to_relative.py

# Step 3: Verify
ruff check examples/ evaluation/ --select I
isort --check examples/ evaluation/
```

---

### P1-4: Test Coverage Analysis [4 HOURS]

```bash
# After fixing P0-1-3:
cd /Volumes/Treehorn/Gits/sonotheia-examples

# Run coverage
pytest --cov=evaluation/src --cov=examples/python \
       --cov-report=html --cov-report=term-missing

# Expected targets:
# - evaluation/src: >= 85%
# - examples/python: >= 70%

# View HTML report
open htmlcov/index.html

# Identify gaps (modules < 70%):
grep -E "^[a-z_].*\s+[0-9]+ *$" htmlcov/index.html | grep -v "100%\|9[0-9]%\|8[0-9]%"
```

---

## 📊 Progress Tracking

| Phase | Items | Est. Hours | Status | Result |
|-------|-------|-----------|--------|--------|
| **P0** | 1-3 | 4 | 🔴 NOT STARTED | → 82% |
| **P1** | 1-4 | 12 | 🔴 NOT STARTED | → 92% |
| **P2** | 1-3 | 9-10 | 🔴 OPTIONAL | → 100% |

**Total**: 25-26 hours to complete hardening

---

## ✅ Completion Criteria

### Phase 1 (P0) Complete When

```bash
✅ pytest --co -q 2>/dev/null | grep "errors" | wc -l
   Expected: 0 errors

✅ black --check . 2>&1 | grep -c "would reformat"
   Expected: 0 files

✅ ruff check . 2>&1 | grep -c "error\|warning"
   Expected: 0 (or minimal non-blocking)
```

### Phase 2 (P1) Complete When

```bash
✅ pytest --cov=evaluation/src --cov=examples/python 2>&1 | grep "TOTAL"
   Expected: >= 80% coverage

✅ pre-commit run --all-files 2>&1 | grep "failed"
   Expected: 0 failed

✅ git log --oneline | head -5
   Expected: Shows commits fixing each item
```

### Phase 3 (P2) Complete When

```bash
✅ GitHub Actions workflow passing
✅ Docker Compose building without errors
✅ Deployment checklist reviewed and approved
```

---

## 🚨 Critical Blockers

| Blocker | Impact | Fix Time | Priority |
|---------|--------|----------|----------|
| Pytest collection errors | Tests won't run | 1-2 hrs | **P0** |
| Tool config conflicts | Inconsistent linting | 0.5 hrs | **P0** |
| Line length violations | CI/CD fails | 0.5 hrs | **P0** |
| Optional deps unconditional | Breaks without deps | 4 hrs | **P1** |
| No pre-commit | Local quality slips | 1.5 hrs | **P1** |

---

## 📞 For Questions

**Detailed Reference**: See `COMPREHENSIVE_HARDENING_PLAN.md` for full context

**Key Sections**:

- Section 1: Audit findings
- Section 2: Hardening recommendations (detailed)
- Section 3: Completion status
- Section 4: Implementation roadmap
- Appendix: Useful commands, patterns, references

---

**Created**: January 27, 2026  
**Status**: Ready for implementation
