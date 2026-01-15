#!/bin/bash
# One-click launcher for Sonotheia Examples

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Header
show_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║              🎙️  Sonotheia Examples Launcher              ║"
    echo "║     Voice Fraud Mitigation Integration & Evaluation       ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}⚠️  No virtual environment found.${NC}"
        echo -e "Run '${GREEN}./launcher.sh dev${NC}' to set up the development environment."
        return 1
    fi
    return 0
}

# Check environment file
check_env() {
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.example...${NC}"
            cp .env.example .env
            echo -e "${GREEN}✓ .env file created. Please edit it with your API keys.${NC}"
        fi
    fi
}

# DEV SETUP
setup_dev() {
    echo -e "${BLUE}🛠️  Setting up development environment...${NC}"

    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    fi

    # shellcheck disable=SC1091
    source venv/bin/activate
    pip install --upgrade pip
    
    # Install evaluation framework
    if [ -d "evaluation" ]; then
        pip install -e "evaluation[dev]"
        echo -e "${GREEN}✓ Evaluation framework installed${NC}"
    fi
    
    # Install examples dependencies
    if [ -d "examples/python" ]; then
        pip install -r examples/python/requirements.txt
        echo -e "${GREEN}✓ Python examples dependencies installed${NC}"
    fi

    check_env

    echo ""
    echo -e "${GREEN}✅ Development environment ready${NC}"
    echo -e "${YELLOW}Activate with: source venv/bin/activate${NC}"
}

# Run Python Example
run_python_example() {
    check_env
    echo -e "${BLUE}🐍 Running Python integration example...${NC}"
    
    if check_venv; then
        # shellcheck disable=SC1091
        source venv/bin/activate
    fi
    
    if [ ! -f "$1" ]; then
        echo -e "${YELLOW}Usage: ./launcher.sh python <audio_file>${NC}"
        echo "Example: ./launcher.sh python test_audio.wav"
        exit 1
    fi
    
    cd examples/python
    python main.py "$1"
}

# Run Evaluation Harness
run_evaluation() {
    check_env
    echo -e "${BLUE}🔬 Running Audio Trust Harness evaluation...${NC}"
    
    if check_venv; then
        # shellcheck disable=SC1091
        source venv/bin/activate
    fi
    
    if [ ! -f "$1" ]; then
        echo -e "${YELLOW}Usage: ./launcher.sh eval <audio_file> [output_file]${NC}"
        echo "Example: ./launcher.sh eval test.wav audit.jsonl"
        exit 1
    fi
    
    OUTPUT="${2:-audit.jsonl}"
    python -m audio_trust_harness run --audio "$1" --out "$OUTPUT"
    echo -e "${GREEN}✅ Evaluation complete. Results: $OUTPUT${NC}"
}

# Run Tests
run_tests() {
    echo -e "${BLUE}🧪 Running tests...${NC}"
    
    if check_venv; then
        # shellcheck disable=SC1091
        source venv/bin/activate
    fi
    
    if [ -d "evaluation" ]; then
        cd evaluation
        pytest tests/ -v
    else
        echo -e "${YELLOW}No test directory found.${NC}"
    fi
}

# CHECK Readiness
check_readiness() {
    echo -e "${BLUE}🔍 Checking environment readiness...${NC}"

    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        echo -e "  [${GREEN}✓${NC}] ${PYTHON_VERSION}"
    else
        echo -e "  [${RED}✗${NC}] Python not found"
    fi

    # Check virtual environment
    if [ -d "venv" ]; then
        echo -e "  [${GREEN}✓${NC}] Virtual environment exists"
    else
        echo -e "  [${YELLOW}!${NC}] Virtual environment missing (run: ./launcher.sh dev)"
    fi

    # Check .env
    if [ -f .env ]; then
        echo -e "  [${GREEN}✓${NC}] .env file exists"
    else
        echo -e "  [${YELLOW}!${NC}] .env file missing"
    fi

    # Check key directories
    if [ -d "examples" ]; then
        echo -e "  [${GREEN}✓${NC}] examples/ directory found"
    fi
    
    if [ -d "evaluation" ]; then
        echo -e "  [${GREEN}✓${NC}] evaluation/ directory found"
    fi

    echo ""
    echo -e "${GREEN}✓ Readiness check complete.${NC}"
}

# USAGE / Interactive Menu
show_menu() {
    show_header
    echo "Select an option:"
    echo ""
    echo -e "  ${GREEN}1)${NC} dev        - Setup development environment"
    echo -e "  ${CYAN}2)${NC} python     - Run Python integration example"
    echo -e "  ${MAGENTA}3)${NC} eval       - Run Audio Trust Harness evaluation"
    echo -e "  ${BLUE}4)${NC} test       - Run tests"
    echo -e "  5) check      - Check environment readiness"
    echo -e "  ${RED}q)${NC} quit       - Exit"
    echo ""
    read -p "Enter choice [1-5 or q]: " choice
    
    case "$choice" in
        1|dev)     setup_dev ;;
        2|python)  
            read -p "Enter audio file path: " audio_file
            run_python_example "$audio_file" 
            ;;
        3|eval)    
            read -p "Enter audio file path: " audio_file
            run_evaluation "$audio_file"
            ;;
        4|test)    run_tests ;;
        5|check)   check_readiness ;;
        q|quit)    echo "Goodbye!"; exit 0 ;;
        *)         echo -e "${RED}Invalid option${NC}"; show_menu ;;
    esac
}

# USAGE for command-line mode
show_usage() {
    echo "Usage: $0 [command] [args]"
    echo ""
    echo "Commands:"
    echo "  ${GREEN}dev${NC}              - Setup development environment"
    echo "  ${CYAN}python <file>${NC}    - Run Python integration example"
    echo "  ${MAGENTA}eval <file>${NC}      - Run Audio Trust Harness evaluation"
    echo "  ${BLUE}test${NC}             - Run tests"
    echo "  check           - Check environment readiness"
    echo ""
    echo "Run without arguments for interactive menu."
    exit 1
}

# Main Logic
case "${1:-}" in
    dev)     setup_dev ;;
    python)  run_python_example "$2" ;;
    eval)    run_evaluation "$2" "$3" ;;
    test)    run_tests ;;
    check)   check_readiness ;;
    help|-h|--help) show_usage ;;
    "")      show_menu ;;
    *)       echo -e "${RED}Unknown command: $1${NC}"; show_usage ;;
esac
