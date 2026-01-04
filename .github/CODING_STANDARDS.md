# Coding Standards and Repository Organization

This document provides guidelines for maintaining the organization and structure of the sonotheia-examples repository. All coding agents and contributors should follow these standards.

## Repository Structure

```
sonotheia-examples/
├── .github/                    # GitHub configurations and workflows
│   ├── workflows/              # CI/CD pipelines
│   └── CODING_STANDARDS.md     # This file
├── docs/                       # All documentation
│   ├── development/            # Development notes and summaries
│   ├── BEST_PRACTICES.md       # Integration best practices
│   ├── ENHANCED_EXAMPLES.md    # Enhanced features guide
│   ├── FAQ.md                  # Frequently asked questions
│   └── REPOSITORY_STRUCTURE.md # Repository organization guide
├── examples/                   # All code examples
│   ├── curl/                   # Bash/curl examples
│   ├── kubernetes/             # K8s deployment manifests
│   ├── node/                   # Node.js examples
│   ├── python/                 # Python examples and tests
│   └── typescript/             # TypeScript examples
├── .env.example                # Example environment configuration
├── .gitignore                  # Git ignore patterns
├── LICENSE                     # Repository license
├── NOTES.md                    # Implementation notes and TODOs
└── README.md                   # Main repository documentation
```

## File Organization Principles

### Root Directory
- **KEEP MINIMAL**: Only essential files in the root
- **Essential files**: README.md, LICENSE, NOTES.md, .env.example, .gitignore
- **Move everything else** to appropriate subdirectories

### Documentation (`/docs/`)
- All documentation goes in `/docs/` except README.md and NOTES.md
- Use subdirectories for different doc types:
  - `/docs/development/` - Development artifacts, summaries, integration notes
  - `/docs/guides/` - User-facing guides (if needed in future)
  - `/docs/api/` - API documentation (if added in future)

### Examples (`/examples/`)
- Each language/tool gets its own subdirectory
- Each example directory should contain:
  - `README.md` - Setup and usage instructions
  - Source code files
  - `tests/` subdirectory (if applicable)
  - Configuration files (package.json, requirements.txt, etc.)

## Naming Conventions

### Files
- Use lowercase with hyphens for shell scripts: `deepfake-detect.sh`
- Use snake_case for Python files: `client_enhanced.py`
- Use kebab-case for Node.js files: `batch-processor.js`
- Use PascalCase for TypeScript when appropriate
- Documentation uses UPPERCASE for major docs: `README.md`, `FAQ.md`

### Directories
- Use lowercase for directories: `examples/`, `docs/`
- Use descriptive names: `kubernetes/` not `k8s/`
- Avoid abbreviations unless widely recognized

## Code Organization

### Python Examples
```
examples/python/
├── README.md              # Python-specific documentation
├── requirements.txt       # Dependencies
├── pyproject.toml         # Project metadata
├── Dockerfile             # Container image
├── docker-compose.yml     # Multi-service orchestration
├── client.py              # Basic client
├── client_enhanced.py     # Enhanced client with resilience
├── main.py                # Basic CLI example
├── enhanced_example.py    # Enhanced CLI example
├── streaming_example.py   # Streaming processor
├── health_check.py        # Health monitoring
├── audio_analysis_example.py    # DSP analysis
├── voice_routing_example.py     # Voice routing workflow
└── tests/                 # All test files
    ├── test_client.py
    └── test_client_enhanced.py
```

### Node.js Examples
```
examples/node/
├── README.md                      # Node-specific documentation
├── package.json                   # Dependencies
├── batch-processor.js             # Basic batch processor
├── batch-processor-enhanced.js    # Enhanced with metrics
└── webhook-server.js              # Webhook receiver
```

### Kubernetes Examples
```
examples/kubernetes/
├── README.md           # K8s deployment guide
└── deployment.yaml     # All manifests in one file
```

## Development Workflow

### Adding New Examples
1. Create files in the appropriate `/examples/<language>/` directory
2. Add comprehensive README.md in that directory
3. Include tests if the example is complex
4. Update the main README.md with a reference
5. Add to the appropriate section in docs if needed

### Adding Documentation
1. Determine if it's user-facing or development notes
2. User-facing → `/docs/`
3. Development notes → `/docs/development/`
4. Update README.md with a link if it's important
5. Use clear, descriptive filenames

### Updating Existing Code
1. Maintain consistency with existing patterns
2. Update tests if changing functionality
3. Update documentation if changing behavior
4. Run tests before committing
5. Keep changes minimal and focused

## Documentation Standards

### README Files
- Start with a clear title and brief description
- Include a "Quick Start" or "Quickstart" section
- Provide examples with actual commands
- Document all configuration options
- Include troubleshooting section if relevant

### Code Comments
- Use comments sparingly - code should be self-documenting
- Add comments for complex algorithms or non-obvious logic
- Include docstrings for all public functions/classes
- Reference issue numbers or docs where relevant

### Markdown Style
- Use ATX-style headers (`#` not underlines)
- Use fenced code blocks with language hints
- Keep lines under 120 characters where practical
- Use tables for comparison data
- Include links to related documentation

## Testing Standards

### Python Tests
- All tests go in `examples/python/tests/`
- Use pytest as the test framework
- Filename pattern: `test_*.py`
- Mock external API calls
- Aim for high coverage of new code

### Running Tests
```bash
# Python tests
cd examples/python
pip install -r requirements.txt
pytest tests/ -v

# TypeScript build
cd examples/typescript
npm install
npm run build

# Node.js syntax check
cd examples/node
npm install
node --check batch-processor.js
```

## Security Practices

### Secrets Management
- **NEVER** commit API keys, tokens, or secrets
- Use environment variables for all credentials
- Provide `.env.example` with placeholder values
- Document required environment variables
- Use secret management services in production

### Dependencies
- Keep dependencies up to date
- Review security advisories regularly
- Use lock files (requirements.txt, package-lock.json)
- Document why each dependency is needed

## Git Practices

### Commits
- Write clear, descriptive commit messages
- Use present tense: "Add feature" not "Added feature"
- Reference issues when applicable
- Keep commits focused on one change

### Branches
- Use descriptive branch names: `copilot/feature-description`
- Keep branches short-lived
- Rebase on main before merging
- Delete branches after merging

### Pull Requests
- Fill out the PR description template
- Link to related issues
- Request review from appropriate team members
- Ensure CI passes before merging

## Maintenance Tasks

### Regular Reviews
- Monthly review of dependencies for updates
- Quarterly review of documentation accuracy
- Remove deprecated examples and update docs
- Check for broken links in documentation

### When Examples Become Outdated
1. Add deprecation notice to the example's README
2. Point to the replacement or updated example
3. Keep the old example for 2 release cycles
4. Then move to `/docs/development/archive/` or delete

### File Cleanup
- Remove temporary files not in .gitignore
- Archive old development notes to `/docs/development/archive/`
- Keep root directory minimal
- Consolidate duplicate documentation

## Agent-Specific Guidelines

### For Coding Agents
1. **Always check** this file before making structural changes
2. **Preserve** the organization patterns described here
3. **Ask before** creating new top-level directories
4. **Update** this file if you establish new patterns
5. **Document** your decisions in commit messages

### For Review Agents
1. **Verify** changes follow these standards
2. **Check** that documentation is updated
3. **Ensure** tests are included where appropriate
4. **Validate** that the structure remains clean
5. **Request changes** if standards are violated

## Questions or Changes

If you need to deviate from these standards:
1. Document why in your commit message
2. Update this file with the new pattern
3. Ensure consistency across the repository
4. Consider if it improves maintainability

For questions about these standards, open an issue or contact the repository maintainers.

---

**Last Updated**: 2026-01-04  
**Version**: 1.0.0
