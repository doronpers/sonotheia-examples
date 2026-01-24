# Launch & Onboarding Guide

**Cross-Platform Setup for Windows & macOS**

This guide provides simplified, unified instructions for launching and onboarding across all repositories in the Sono ecosystem.

---

## 🎯 Quick Start (Choose Your Repository)

### Sonotheia Examples

**Purpose:** Integration examples and evaluation framework for voice fraud mitigation

**Windows:**

```cmd
cd sonotheia-examples
launcher.sh dev
```

**macOS:**

```bash
cd sonotheia-examples
./launcher.sh dev
```

**First Launch:**

- Creates virtual environment automatically
- Installs dependencies
- Sets up `.env` from `.env.example`
- Ready to run examples in minutes

---

### Feedback Loop

**Purpose:** AI-assisted development framework with pattern learning

**Windows:**

```cmd
cd feedback-loop
launch-feedback-loop.bat
```

**macOS:**

```bash
cd feedback-loop
./launch-feedback-loop.command
```

**Or One-Liner Install:**

```bash
curl -fsSL https://raw.githubusercontent.com/doronpers/feedback-loop/main/install.sh | bash
```

**First Launch:**

- Auto-detects environment
- Installs dependencies if needed
- Launches interactive demo
- Opens analytics dashboard

---

### Sono-Eval

**Purpose:** Growth-oriented assessment platform for candidates

**Windows:**

```cmd
cd sono-eval
launcher.sh start
```

**macOS:**

```bash
cd sono-eval
./launcher.sh start
```

**Or Double-Click:**

- **macOS:** `start-sono-eval-server.command` (API only)
- **macOS:** `start-sono-eval-full.command` (Full stack with Celery)

**First Launch:**

- Checks Docker installation
- Creates `.env` from `.env.example`
- Starts all services (API, PostgreSQL, Redis, Superset)
- Auto-finds available ports
- Displays service URLs

---

### Council AI

**Purpose:** Intelligent advisory council system with AI personas

**Windows:**

```cmd
cd council-ai
bin\launch-council.bat
```

**macOS:**

```bash
cd council-ai
./bin/launch-council-web.command
```

**Or Setup Wizard (First Time):**

```bash
cd council-ai
council init
```

**First Launch:**

- Detects LM Studio (local, free option)
- Guides API key setup (Anthropic, OpenAI, Gemini)
- Sets default domain
- Opens web interface automatically

---

## 📋 Prerequisites

### All Repositories

**Required:**

- **Python 3.11+** (3.13+ recommended for feedback-loop and sono-eval)
- **Git** for cloning repositories

**Check Installation:**

```bash
# Windows (Command Prompt or PowerShell)
python --version
git --version

# macOS
python3 --version
git --version
```

### Repository-Specific Requirements

| Repository | Additional Requirements |
|------------|------------------------|
| **sonotheia-examples** | None (optional: Node.js for TypeScript examples) |
| **feedback-loop** | None (optional: PostgreSQL for production) |
| **sono-eval** | **Docker & Docker Compose** (required for full stack) |
| **council-ai** | None (optional: Node.js for web UI, LM Studio for local LLM) |

---

## 🚀 Installation Methods

### Method 1: Automated Setup (Recommended)

Most repositories provide automated setup scripts that handle everything:

**Windows:**

- Double-click `.bat` files in repository root
- Or run `setup-venv.bat` / `launcher.sh dev` from command line

**macOS:**

- Double-click `.command` files in repository root
- Or run `./launcher.sh dev` from terminal

### Method 2: Manual Setup

**Step 1: Clone Repository**

```bash
git clone <repository-url>
cd <repository-name>
```

**Step 2: Create Virtual Environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS
python3 -m venv venv
source venv/bin/activate
```

**Step 3: Install Dependencies**

```bash
# Most repositories
pip install -r requirements.txt
pip install -e ".[dev]"

# Or repository-specific
pip install -e .
```

**Step 4: Configure Environment**

```bash
# Copy example config
cp .env.example .env

# Edit if needed (optional for quick start)
# Windows: notepad .env
# macOS: nano .env
```

---

## 🖥️ Platform-Specific Instructions

### Windows (PC)

#### PowerShell vs Command Prompt

- **PowerShell** (recommended): Better Unicode support, modern features
- **Command Prompt**: Traditional, works everywhere

#### Common Issues & Solutions

**Issue: "python is not recognized"**

```cmd
# Add Python to PATH during installation
# Or use full path:
C:\Python311\python.exe --version
```

**Issue: "Permission denied" for scripts**

```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Issue: Virtual environment activation fails**

```cmd
# Use the correct activation script
venv\Scripts\activate.bat  # Command Prompt
venv\Scripts\Activate.ps1  # PowerShell
```

#### Windows Launcher Files

- `.bat` files: Double-click to run
- `.ps1` files: Right-click → "Run with PowerShell"
- `.command` files: Not used on Windows (macOS only)

---

### macOS

#### Terminal vs Finder

- **Terminal**: Use for command-line operations
- **Finder**: Double-click `.command` files to launch

#### Common Issues & Solutions

**Issue: "Permission denied" for scripts**

```bash
chmod +x script-name.command
chmod +x launcher.sh
```

**Issue: "Cannot open" security warning**

- Right-click file → "Open" → "Open" in dialog
- Or: System Preferences → Security & Privacy → "Open Anyway"

**Issue: Python version mismatch**

```bash
# Check which Python
which python3
python3 --version

# Use pyenv for version management
brew install pyenv
pyenv install 3.13.0
pyenv local 3.13.0
```

#### macOS Launcher Files

- `.command` files: Double-click to run (opens Terminal)
- `.sh` files: Run from terminal: `./launcher.sh`

---

## 🔧 First-Time Setup Checklist

### Before You Start

- [ ] **Python installed** (3.11+ for most, 3.13+ for feedback-loop/sono-eval)
- [ ] **Git installed** (for cloning repositories)
- [ ] **Repository cloned** (or downloaded)
- [ ] **Terminal/Command Prompt ready**

### During Setup

- [ ] **Virtual environment created** (automatic in most launchers)
- [ ] **Dependencies installed** (automatic in most launchers)
- [ ] **`.env` file created** (from `.env.example`)
- [ ] **API keys configured** (if required for the repository)

### After Setup

- [ ] **Launcher script works** (can start services)
- [ ] **Health check passes** (if repository has health endpoint)
- [ ] **Documentation accessible** (README or docs folder)

---

## 🎓 Onboarding Paths

### Path 1: Quick Demo (5 minutes)

**Goal:** See it working immediately

1. Run the launcher script
2. Follow on-screen prompts
3. Try the demo/example
4. Explore the interface

**Best for:** Getting a feel for the tool

---

### Path 2: Guided Setup (15 minutes)

**Goal:** Proper configuration and understanding

1. Read the repository README
2. Run setup wizard (if available)
3. Configure API keys (if needed)
4. Run first example/demo
5. Review documentation

**Best for:** Understanding how it works

---

### Path 3: Full Development Setup (30 minutes)

**Goal:** Ready for development and contribution

1. Complete guided setup
2. Review architecture documentation
3. Set up development tools (linter, formatter)
4. Run test suite
5. Review contributing guidelines
6. Set up IDE/editor integration

**Best for:** Contributing or customizing

---

## 🔍 Troubleshooting

### Common Problems

#### "Command not found"

**Solution:**

- Check Python is in PATH: `python --version` (Windows) or `python3 --version` (macOS)
- Use full path to Python if needed
- Verify virtual environment is activated

#### "Port already in use"

**Solution:**

- Most launchers auto-detect and use next available port
- Or manually stop the process using the port
- Check with: `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (macOS)

#### "Docker not running" (sono-eval)

**Solution:**

- Start Docker Desktop
- Verify: `docker ps`
- Check Docker Compose: `docker-compose --version`

#### "Permission denied" (macOS)

**Solution:**

```bash
chmod +x script-name.command
chmod +x launcher.sh
```

#### "Module not found"

**Solution:**

- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check you're in the correct directory

---

## 📚 Repository-Specific Guides

### Sonotheia Examples

- **Quick Start:** [README.md](../README.md#-golden-path-demo-start-here)
- **Detailed Guide:** [documentation/SHOWCASE_QUICKSTART.md](SHOWCASE_QUICKSTART.md)
- **Integration Guide:** [examples/README.md](../examples/README.md)

### Feedback Loop

- **Quick Start:** [README.md](../../feedback-loop/README.md#-quick-start-30-seconds)
- **Complete Guide:** [documentation/QUICKSTART.md](../../feedback-loop/documentation/QUICKSTART.md)
- **Cursor Integration:** [CURSOR_INTEGRATION.md](../../feedback-loop/CURSOR_INTEGRATION.md)

### Sono-Eval

- **Quick Start:** [README.md](../../sono-eval/README.md#-start-here)
- **Detailed Guide:** [documentation/Guides/QUICK_START.md](../../sono-eval/documentation/Guides/QUICK_START.md)
- **Launchers:** [README_LAUNCHERS.md](../../sono-eval/README_LAUNCHERS.md)

### Council AI

- **Quick Start:** [README.md](../../council-ai/README.md#-quickstart-zero-cost-no-api-key-required)
- **Setup Guide:** [QUICK_START.md](../../council-ai/QUICK_START.md)
- **Web App Guide:** [documentation/WEB_APP.md](../../council-ai/documentation/WEB_APP.md)

---

## 🎯 Next Steps

After successful launch:

1. **Explore the Interface**
   - Try the demo/example
   - Review available features
   - Check documentation links

2. **Configure for Your Use Case**
   - Set up API keys (if needed)
   - Adjust settings
   - Customize preferences

3. **Read the Documentation**
   - Start with README
   - Review key guides
   - Explore examples

4. **Join the Community**
   - Check GitHub Discussions
   - Review Issues
   - Contribute feedback

---

## 💡 Tips for Success

### Windows Users

- Use **PowerShell** for better Unicode support
- Keep terminal windows open while services run
- Use **full paths** if PATH issues occur
- Check **Windows Defender** isn't blocking scripts

### macOS Users

- Grant **Terminal** full disk access if needed (System Preferences)
- Use **Homebrew** for easy package management
- Keep **Docker Desktop** running for containerized services
- Use **pyenv** for Python version management

### Both Platforms

- **Keep launcher terminal open** while services run
- **Check logs** if something doesn't work
- **Read error messages** carefully - they often contain solutions
- **Start simple** - try the demo before customizing

---

## 🆘 Getting Help

### Self-Service

1. Check repository README
2. Review troubleshooting section
3. Search GitHub Issues
4. Check documentation index

### Community Support

- **GitHub Discussions:** Ask questions
- **GitHub Issues:** Report bugs
- **Documentation:** Find detailed guides

### Emergency

- Check service logs: `./launcher.sh logs` (if available)
- Verify prerequisites are installed
- Try clean reinstall: remove `venv/` and start over

---

## 📝 Summary

**Simplified Launch Process:**

1. **Clone** repository
2. **Navigate** to repository directory
3. **Run** launcher script (`.bat` on Windows, `.command` or `./launcher.sh` on macOS)
4. **Follow** on-screen prompts
5. **Access** the interface (usually opens automatically)

**Most repositories handle:**

- ✅ Virtual environment creation
- ✅ Dependency installation
- ✅ Configuration file setup
- ✅ Service startup
- ✅ Browser opening

**You just need to:**

- Have Python installed
- Run the launcher
- Configure API keys (if required)

---

**Last Updated:** 2026-01-24  
**Maintained by:** Sono Platform Team
