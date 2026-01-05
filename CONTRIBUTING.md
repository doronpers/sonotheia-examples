# Contributing to Sonotheia Examples

Thank you for your interest in contributing! 🎉

## TL;DR - Quick Contributions

**Found a typo or small bug?**

1. Fork the repo, make your change, submit a PR
2. That's it! No issue required for obvious fixes

**Want to add an example or feature?**

1. Open an issue first to discuss the approach
2. Get feedback from maintainers
3. Fork, code, test, submit PR

**Need help?** Check [Troubleshooting](docs/TROUBLESHOOTING.md) or [FAQ](docs/FAQ.md) first.

---

## Quick Start for Contributors

### Prerequisites
- Python 3.9+ (for Python examples)
- Node.js 18+ (for TypeScript/Node.js examples)
- Git

### Setup in 3 Steps

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/sonotheia-examples.git
cd sonotheia-examples

# 2. Set up credentials
cp .env.example .env
# Edit .env with your API key

# 3. Install dependencies (choose your language)
cd examples/python && pip install -r requirements.txt
# OR
cd examples/typescript && npm install
# OR
cd examples/node && npm install
```

### Make Your Change

```bash
# 1. Create a branch
git checkout -b feature/your-feature-name

# 2. Make changes (follow existing code style)

# 3. Test your changes
cd examples/python && pytest tests/ -v
# OR
cd examples/typescript && npm test
# OR
cd examples/node && npm test

# 4. Commit and push
git add .
git commit -m "Brief description of changes"
git push origin feature/your-feature-name

# 5. Open a Pull Request on GitHub
```

---

## Code Style Quick Reference

### Python
- Follow PEP 8
- Use type hints
- Run: `ruff check .` before committing

### TypeScript/JavaScript
- Use modern ES6+ syntax
- Follow existing conventions
- Ensure `npm run build` succeeds

### Shell Scripts
- Use `#!/usr/bin/env bash`
- Follow bash best practices
- Run `shellcheck` if available

### Documentation
- Clear, concise language
- Test all code examples
- Check all links work

---

## Pull Request Checklist

Before submitting your PR:

- [ ] Code follows the style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated (if needed)
- [ ] Commit messages are clear
- [ ] No secrets or API keys committed
- [ ] Changes are focused and minimal

---

## Types of Contributions We Welcome

### 🐛 Bug Fixes
- Fix broken examples or code
- Correct typos in documentation
- Fix broken links

### 📚 Documentation
- Improve clarity or accuracy
- Add missing examples
- Fix formatting issues

### ✨ New Examples
- New language implementations
- New use case demonstrations
- Integration patterns

### 🧪 Tests
- Add missing test coverage
- Improve test quality
- Add integration tests

### 🛠️ Tooling
- Improve development workflow
- Add helpful scripts
- Enhance CI/CD

---

## What We're Looking For

### High Priority
- Real-world use case examples
- Production deployment patterns
- Error handling improvements
- Performance optimizations
- Security enhancements

### Medium Priority
- Additional language examples (Go, Rust, Ruby, etc.)
- Cloud platform integrations (GCP, Azure)
- Container orchestration examples
- Monitoring and observability

### Low Priority
- Cosmetic changes to existing code
- Alternative implementations of existing examples
- Experimental features

**Tip:** Open an issue first for medium/large changes to ensure alignment with project goals.

---

## Testing Requirements

All code changes should include appropriate tests:

### Python
```bash
cd examples/python
pytest tests/ -v --cov=.
```

### TypeScript
```bash
cd examples/typescript
npm run build && npm test
```

### Node.js
```bash
cd examples/node
npm install
node --check batch-processor.js
npm test  # if tests exist
```

### Documentation
- Test all code snippets manually
- Verify all links work
- Check formatting renders correctly

---

## Review Process

1. **Automated checks** run on all PRs (linting, tests)
2. **Maintainer review** (usually within 1-3 business days)
3. **Address feedback** if requested
4. **Approval and merge** once checks pass

**Tips for faster review:**
- Keep PRs small and focused
- Write clear commit messages
- Respond promptly to feedback
- Be patient and professional

---

## Code of Conduct

We're committed to providing a welcoming environment:

- Be respectful and professional
- Assume good intentions
- Give constructive feedback
- Accept constructive feedback gracefully
- Focus on what's best for the community

**Report issues:** If you experience unacceptable behavior, contact the maintainers.

---

## AI-Assisted Development

This repository embraces AI-assisted development! We provide comprehensive guides:

- **[AI Development Workflow](.github/QUICK_REFERENCE.md)** - Complete guide for AI-assisted contributions
- **[Three-Question Framework](docs/workflow-guides/start-simple.md)** - Problem-solving approach
- **[Multi-Agent Workflow](docs/workflow-guides/multi-agent-workflow.md)** - For complex changes
- **[Agent Quick Reference](.github/AGENT_QUICK_REFERENCE.md)** - Quick decision tree

**Using AI tools?** These guides help you work more effectively with AI coding assistants.

---

## Need Help?

### Before Opening an Issue
1. Check the [FAQ](docs/FAQ.md)
2. Search [existing issues](https://github.com/doronpers/sonotheia-examples/issues)
3. Review [Troubleshooting](docs/TROUBLESHOOTING.md)

### When Opening an Issue
- Use a clear, descriptive title
- Include reproduction steps (for bugs)
- Provide context and motivation (for features)
- Include environment details (OS, Python/Node version, etc.)

### Security Issues
**DO NOT** open public issues for security vulnerabilities. Email your Sonotheia integration engineer directly.

---

## Recognition

Contributors are recognized in:
- Git commit history
- Release notes (for significant contributions)
- Thank you in relevant documentation

We appreciate all contributions, large and small! 🙏

---

## Detailed Guidelines

For comprehensive contribution guidelines, see:

- **[Full Contributing Guide](.github/CONTRIBUTING.md)** - Detailed process and requirements
- **[Coding Standards](.github/CODING_STANDARDS.md)** - Complete style guide
- **[Documentation Principles](docs/DOCUMENTATION_PRINCIPLES.md)** - Writing guidelines
- **[Repository Structure](docs/REPOSITORY_STRUCTURE.md)** - How code is organized

---

## Questions?

- **General**: [GitHub Discussions](https://github.com/doronpers/sonotheia-examples/discussions)
- **Specific issues**: [Open an issue](https://github.com/doronpers/sonotheia-examples/issues)
- **API support**: Contact your Sonotheia integration engineer

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

**Ready to contribute?** 🚀

1. Find or create an issue
2. Fork the repository
3. Make your changes
4. Submit a pull request

Thank you for making Sonotheia Examples better! 🎉
