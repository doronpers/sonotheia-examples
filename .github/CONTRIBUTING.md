# Contributing to Sonotheia Examples

Thank you for your interest in contributing to Sonotheia Examples! This document provides guidelines for contributing to this repository.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and professional in all interactions.

## How to Contribute

### Reporting Issues

- Search [existing issues](https://github.com/doronpers/sonotheia-examples/issues) first to avoid duplicates
- Use clear, descriptive titles
- Include relevant details: code snippets, error messages, environment info
- For security vulnerabilities, **do not** open a public issue - email your Sonotheia integration engineer directly

### Submitting Changes

1. **Fork the repository** and create a new branch from `main`
2. **Make your changes** following our coding standards
3. **Test your changes** thoroughly
4. **Document your changes** in code comments and relevant documentation files
5. **Submit a pull request** with a clear description of your changes

## Development Workflow

### Prerequisites

- Python 3.9+ (for Python examples)
- Node.js 18+ (for TypeScript/Node.js examples)
- Git

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/sonotheia-examples.git
cd sonotheia-examples

# Set up environment
cp .env.example .env
# Edit .env with your API credentials

# Install dependencies (choose based on what you're working on)
cd examples/python && pip install -r requirements.txt
# OR
cd examples/typescript && npm install
# OR
cd examples/node && npm install
```

### Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our [Coding Standards](.github/CODING_STANDARDS.md)

3. Test your changes:
   ```bash
   # Python
   cd examples/python && pytest tests/ -v
   
   # TypeScript
   cd examples/typescript && npm run build && npm test
   
   # Node.js
   cd examples/node && npm install && node --check batch-processor.js
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Brief description of changes"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Open a pull request on GitHub

## Coding Standards

Please follow our coding standards and conventions:

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Follow the existing TypeScript conventions
- **JavaScript/Node.js**: Use modern ES6+ syntax
- **Shell scripts**: Follow bash best practices, use shellcheck

See [CODING_STANDARDS.md](CODING_STANDARDS.md) for comprehensive guidelines.

## Testing Requirements

All code changes should include appropriate tests:

- **Python**: Use pytest, follow existing test patterns
- **TypeScript/Node.js**: Use Jest or built-in test runners
- **Documentation**: Test all code examples and links

Run tests before submitting your pull request to ensure everything works.

## Documentation Standards

- Update relevant documentation when making code changes
- Follow [Documentation Principles](../docs/DOCUMENTATION_PRINCIPLES.md)
- Use clear, concise language
- Include code examples where appropriate
- Test all code snippets and links

## AI-Assisted Development

This repository embraces AI-assisted development:

- See [AI Development Workflow](QUICK_REFERENCE.md) for best practices
- Use the [Three-Question Framework](../docs/workflow-guides/start-simple.md)
- Consider [Multi-Agent Workflow](../docs/workflow-guides/multi-agent-workflow.md) for complex changes
- Reference [Agent Quick Reference](AGENT_QUICK_REFERENCE.md) for common patterns

## Pull Request Process

1. **Update documentation** reflecting any changes to behavior or APIs
2. **Update tests** and ensure all tests pass
3. **Update CHANGELOG** (if applicable) with notes on your changes
4. **Request review** from maintainers
5. **Address feedback** promptly and professionally
6. **Wait for approval** before merging

### Pull Request Checklist

Before submitting your PR, ensure:

- [ ] Code follows the style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] No sensitive information (API keys, secrets) is included
- [ ] Changes are focused and minimal
- [ ] All links and references are valid

## Questions?

- Check the [FAQ](../docs/FAQ.md)
- Review [Troubleshooting](../docs/TROUBLESHOOTING.md)
- Search [existing issues](https://github.com/doronpers/sonotheia-examples/issues)
- Join [GitHub Discussions](https://github.com/doronpers/sonotheia-examples/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Sonotheia Examples! 🎉
