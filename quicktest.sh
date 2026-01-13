#!/usr/bin/env bash
# =============================================================================
# Sonotheia Quick Test
# =============================================================================
# Auto-detects available runtime, validates environment, and runs a smoke test.
# Usage: ./quicktest.sh [audio_file]
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎙️ Sonotheia Quick Test${NC}"
echo "========================"
echo ""

# -----------------------------------------------------------------------------
# Step 1: Check for API key
# -----------------------------------------------------------------------------
echo -e "${YELLOW}Step 1: Checking environment...${NC}"

# Source .env if it exists
if [[ -f .env ]]; then
    set -a
    source .env
    set +a
    echo -e "  ${GREEN}✓${NC} Loaded .env file"
fi

if [[ -z "${SONOTHEIA_API_KEY:-}" ]]; then
    echo -e "  ${RED}✗${NC} No API key found!"
    echo ""
    echo "  To fix, either:"
    echo "    1. Copy and edit the example: cp .env.example .env"
    echo "    2. Export directly: export SONOTHEIA_API_KEY=your_key"
    echo ""
    exit 1
fi

echo -e "  ${GREEN}✓${NC} API key configured"

# Check API URL
API_URL="${SONOTHEIA_API_URL:-https://api.sonotheia.com}"
echo -e "  ${GREEN}✓${NC} API URL: ${API_URL}"
echo ""

# -----------------------------------------------------------------------------
# Step 2: Find or use provided audio file
# -----------------------------------------------------------------------------
echo -e "${YELLOW}Step 2: Locating audio file...${NC}"

AUDIO_FILE="${1:-}"

if [[ -z "$AUDIO_FILE" ]]; then
    # Try to find sample audio in test-audio directory
    if [[ -d "examples/test-audio" ]]; then
        AUDIO_FILE=$(find examples/test-audio -type f \( -name "*.wav" -o -name "*.mp3" -o -name "*.flac" \) | head -1)
    fi
fi

if [[ -z "$AUDIO_FILE" ]] || [[ ! -f "$AUDIO_FILE" ]]; then
    echo -e "  ${RED}✗${NC} No audio file found!"
    echo ""
    echo "  Usage: ./quicktest.sh <path_to_audio_file>"
    echo "  Or place test audio in: examples/test-audio/"
    echo ""
    exit 1
fi

echo -e "  ${GREEN}✓${NC} Using audio file: ${AUDIO_FILE}"
echo ""

# -----------------------------------------------------------------------------
# Step 3: Auto-detect runtime and run test
# -----------------------------------------------------------------------------
echo -e "${YELLOW}Step 3: Detecting runtime and running test...${NC}"

run_python() {
    if [[ -f examples/python/main.py ]]; then
        echo -e "  ${BLUE}→${NC} Using Python client..."
        echo ""
        
        # Check if venv exists, if not suggest setup
        if [[ ! -d ".venv" ]] && [[ ! -d "examples/python/.venv" ]]; then
            echo -e "  ${YELLOW}Note:${NC} No virtual environment found."
            echo "  For a clean setup, run:"
            echo "    python3 -m venv .venv && source .venv/bin/activate"
            echo "    pip install -r examples/python/requirements.txt"
            echo ""
        fi
        
        cd examples/python
        python3 main.py "../../${AUDIO_FILE}"
        return 0
    fi
    return 1
}

run_curl() {
    if [[ -f examples/curl/deepfake-detect.sh ]]; then
        echo -e "  ${BLUE}→${NC} Using cURL client..."
        echo ""
        ./examples/curl/deepfake-detect.sh "$AUDIO_FILE"
        return 0
    fi
    return 1
}

run_node() {
    if [[ -f examples/node/batch-processor.js ]]; then
        echo -e "  ${BLUE}→${NC} Using Node.js client..."
        echo ""
        
        if [[ ! -d "examples/node/node_modules" ]]; then
            echo -e "  ${YELLOW}Note:${NC} Installing dependencies..."
            (cd examples/node && npm install --silent)
        fi
        
        node examples/node/batch-processor.js "$AUDIO_FILE"
        return 0
    fi
    return 1
}

# Try runtimes in order of preference
if command -v python3 &>/dev/null && run_python; then
    :
elif command -v curl &>/dev/null && run_curl; then
    :
elif command -v node &>/dev/null && run_node; then
    :
else
    echo -e "  ${RED}✗${NC} No supported runtime found!"
    echo ""
    echo "  Supported runtimes:"
    echo "    - Python 3.9+ (recommended)"
    echo "    - cURL"
    echo "    - Node.js 18+"
    echo ""
    exit 1
fi

# -----------------------------------------------------------------------------
# Step 4: Next steps
# -----------------------------------------------------------------------------
echo ""
echo -e "${GREEN}✅ Quick test complete!${NC}"
echo ""
echo "Next steps:"
echo "  📖 Full documentation:   documentation/GETTING_STARTED.md"
echo "  🐍 Python examples:      examples/python/README.md"
echo "  📦 Node.js examples:     examples/node/README.md"
echo "  🐳 Docker deployment:    examples/kubernetes/"
echo ""
