# Launch Quick Reference

**One-page cheat sheet for launching repositories**

---

## 🚀 Launch Commands

### Sonotheia Examples

```bash
# Windows
cd sonotheia-examples
launcher.sh dev

# macOS
cd sonotheia-examples
./launcher.sh dev
```

### Feedback Loop

```bash
# Windows
cd feedback-loop
launch-feedback-loop.bat

# macOS
cd feedback-loop
./launch-feedback-loop.command

# Or one-liner
curl -fsSL https://raw.githubusercontent.com/doronpers/feedback-loop/main/install.sh | bash
```

### Sono-Eval

```bash
# Windows
cd sono-eval
launcher.sh start

# macOS
cd sono-eval
./launcher.sh start

# Or double-click
start-sono-eval-server.command  # API only
start-sono-eval-full.command     # Full stack
```

### Council AI

```bash
# Windows
cd council-ai
bin\launch-council.bat

# macOS
cd council-ai
./bin/launch-council-web.command

# First time setup
council init
```

---

## 📋 Prerequisites Check

```bash
# Check Python
python --version    # Windows
python3 --version   # macOS

# Check Git
git --version

# Check Docker (for sono-eval)
docker --version
docker-compose --version
```

---

## 🔧 Common Fixes

### Windows

```cmd
# Python not found
# → Reinstall Python, check "Add to PATH"

# Permission denied
# → Run PowerShell as Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### macOS

```bash
# Permission denied
chmod +x script-name.command

# Security warning
# → Right-click → Open → Open
```

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Port in use | Launcher auto-finds next port |
| Module not found | Activate venv, reinstall deps |
| Docker not running | Start Docker Desktop |
| Python version wrong | Use pyenv (macOS) or reinstall |

---

## 📚 Full Guide

See [LAUNCH_AND_ONBOARDING.md](LAUNCH_AND_ONBOARDING.md) for complete instructions.

---

**Last Updated:** 2026-01-24
