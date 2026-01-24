# Repository Structure Guide

This document explains the organization of the sonotheia-examples repository and helps contributors understand where to find and place files.

## Overview

The sonotheia-examples repository is organized to be:

- **Easy to navigate**: Clear directory structure with logical grouping
- **Easy to maintain**: Consistent patterns across all sections
- **Easy to extend**: Well-defined places for new content
- **Reference-ready**: Examples suitable for learning and adaptation

## Directory Structure

```
sonotheia-examples/
├── .github/                    # GitHub-specific configurations
│   ├── workflows/              # CI/CD automation
│   │   └── python-ci.yml       # Python testing pipeline
│   ├── AGENT_QUICK_REFERENCE.md # Quick reference for coding agents
│   ├── CODING_STANDARDS.md     # Development guidelines
│   └── QUICK_REFERENCE.md      # AI-Assisted Development Workflow
│
├── documentation/               # All documentation
│   ├── workflow-guides/       # AI-assisted workflow guides
│   │   ├── README.md           # Workflow building overview
│   │   ├── start-simple.md     # Three-question framework
│   │   └── multi-agent-workflow.md  # Multi-agent patterns
│   ├── development/            # Active development notes
│   │   ├── README.md           # Development context
│   │   ├── SOURCES.md          # Source references for agents
│   │   └── TEST_COVERAGE.md    # Test coverage guide
│   ├── Archive/                # Historical documents
│   │   ├── Development-Historical/  # Past summaries and notes
│   │   └── Reports-Historical/     # Historical review reports
│   ├── BEST_PRACTICES.md       # Integration best practices
│   ├── ENHANCED_EXAMPLES.md    # Production features guide
│   ├── FAQ.md                  # Frequently asked questions
│   └── REPOSITORY_STRUCTURE.md # This file
│
├── examples/                   # All code examples
│   ├── curl/                   # Bash/curl examples
│   │   ├── deepfake-detect.sh  # Deepfake detection
│   │   ├── mfa-verify.sh       # Voice MFA verification
│   │   └── sar-report.sh       # SAR submission
│   │
│   ├── kubernetes/             # Kubernetes deployment
│   │   ├── README.md           # K8s deployment guide
│   │   └── deployment.yaml     # Production manifests
│   │
│   ├── node/                   # Node.js examples
│   │   ├── README.md           # Node.js documentation
│   │   ├── package.json        # Dependencies
│   │   ├── batch-processor.js  # Basic batch processing
│   │   ├── batch-processor-enhanced.js  # With metrics
│   │   └── webhook-server.js   # Webhook receiver
│   │
│   ├── python/                 # Python examples
│   │   ├── tests/              # Test suite (178 tests, 87% coverage threshold)
│   │   │   ├── conftest.py     # Shared fixtures
│   │   │   ├── test_client.py  # Basic client tests
│   │   │   ├── test_client_enhanced.py  # Enhanced tests
│   │   │   ├── test_constants.py  # Constants tests
│   │   │   ├── test_utils.py   # Utils tests
│   │   │   ├── test_response_validator.py  # Response validation tests
│   │   │   ├── test_config_validator.py  # Config validation tests
│   │   │   ├── test_audio_validator.py  # Audio validation tests
│   │   │   ├── test_health_check.py  # Health check tests
│   │   │   ├── test_main.py    # CLI tests
│   │   │   ├── test_mock_api_server.py  # Mock server tests
│   │   │   ├── test_integration.py  # Integration tests
│   │   │   └── test_example_validation.py  # Example validation tests
│   │   ├── README.md           # Python documentation
│   │   ├── requirements.txt    # Python dependencies
│   │   ├── pyproject.toml      # Project metadata
│   │   ├── Dockerfile          # Container image
│   │   ├── docker-compose.yml  # Multi-service setup
│   │   ├── client.py           # Basic API client
│   │   ├── client_enhanced.py  # Hardened client
│   │   ├── main.py             # Basic CLI example
│   │   ├── enhanced_example.py # Enhanced CLI
│   │   ├── streaming_example.py # Stream processing
│   │   ├── health_check.py     # Health monitoring
│   │   ├── audio_analysis_example.py  # DSP analysis
│   │   └── voice_routing_example.py   # Voice routing
│   │
│   └── typescript/             # TypeScript examples
│       ├── src/                # TypeScript source
│       ├── README.md           # TypeScript documentation
│       ├── package.json        # Dependencies
│       └── tsconfig.json       # TypeScript config
│
├── templates/                  # Reusable templates
│   ├── README.md               # Templates overview
│   └── learning-journal.md     # Learning journal template
│
├── .env.example                # Example environment vars
├── .gitignore                  # Git ignore patterns
├── LICENSE                     # MIT license
├── NOTES.md                    # Implementation notes
└── README.md                   # Main documentation
```

## File Types by Location

### Root Directory (/)

**Purpose**: Entry points and essential configuration

Contains only:

- `README.md` - Primary documentation and navigation
- `LICENSE` - Legal license for the repository
- `NOTES.md` - Assumptions, TODOs, and implementation notes
- `.env.example` - Template for environment configuration
- `.gitignore` - Version control exclusions

**Why minimal?**: A clean root makes the repository approachable and professional.

### Documentation (/documentation/)

**Purpose**: All user-facing and development documentation

#### Main Documentation

- `BEST_PRACTICES.md` - Guidelines for production integration
- `ENHANCED_EXAMPLES.md` - Advanced features and patterns
- `FAQ.md` - Common questions and answers
- `REPOSITORY_STRUCTURE.md` - This file

#### Development Documentation (/documentation/development/)

**Purpose**: Active development notes and sources

- `README.md` - Development context overview
- `SOURCES.md` - Source references for coding agents

#### Historical Archive (/documentation/Archive/)

**Purpose**: Historical documents preserved for reference

- `Development-Historical/` - Integration summaries, refactoring notes, and status reports (2026-01-05/06)
- `Reports-Historical/` - Comprehensive review summaries, audits, and test coverage reports (2026-01-10, 2026-01-23)

**Note**: Archived files document past development processes and decisions but are no longer actively maintained.

#### AI-Assisted Workflow Documentation (/documentation/workflow-guides/)

**Purpose**: Guides for effective AI-assisted development

- `README.md` - Workflow building overview
- `start-simple.md` - Three-question framework for problem definition
- `multi-agent-workflow.md` - Patterns for using multiple AI agents

These guides document real-world AI collaboration practices used in this repository.

### Examples (/examples/)

**Purpose**: Working code samples in multiple languages

Each language/tool subdirectory follows this pattern:

```
examples/<language>/
├── README.md           # Language-specific setup and usage
├── tests/              # Test files (when applicable)
├── <config-files>      # package.json, requirements.txt, etc.
└── <source-files>      # Actual example code
```

#### cURL Examples (/examples/curl/)

Shell scripts demonstrating API calls with minimal dependencies. Great for:

- Quick testing and validation
- CI/CD pipeline integration
- Learning the API structure

#### Python Examples (/examples/python/)

Comprehensive Python implementation with:

- Basic and enhanced clients
- Streaming and batch processing
- Health monitoring
- DSP analysis
- Docker/Kubernetes deployment
- Comprehensive test suite (178 tests, 87% coverage threshold)

**Best for**: Production deployment, complex workflows, data analysis

#### Node.js Examples (/examples/node/)

JavaScript/Node.js patterns including:

- Batch processing with concurrency
- Webhook server
- Metrics and monitoring

**Best for**: JavaScript ecosystems, web applications, serverless

#### TypeScript Examples (/examples/typescript/)

Type-safe client with full type definitions.

**Best for**: TypeScript projects needing compile-time safety

#### Kubernetes Examples (/examples/kubernetes/)

Example Kubernetes manifests with:

- Deployments with health probes
- ConfigMaps and Secrets
- Services for metrics
- Persistent volume claims
- CronJobs for monitoring

**Best for**: Container orchestration, cloud deployment

### GitHub Configuration (/.github/)

**Purpose**: GitHub-specific automation and guidelines

- `/workflows/` - CI/CD pipelines using GitHub Actions
- `AGENT_QUICK_REFERENCE.md` - Quick reference for coding agents
- `CODING_STANDARDS.md` - Standards for agents and contributors
- `QUICK_REFERENCE.md` - AI-Assisted Development Workflow

### Templates (/templates/)

**Purpose**: Reusable templates for tracking and documentation

- `README.md` - Templates overview
- `learning-journal.md` - Template for tracking AI-assisted development sessions

## Navigation Guide

### I want to

**Learn about AI-assisted development**
→ Start with `.github/QUICK_REFERENCE.md`
→ Apply the three-question framework from `documentation/workflow-guides/start-simple.md`
→ Track your progress with `templates/learning-journal.md`

**Learn about the API basics**
→ Start with `README.md` then `documentation/FAQ.md`

**Integrate the API quickly**
→ Try `examples/curl/` for testing, then move to your language

**Build a production application**
→ Read `documentation/BEST_PRACTICES.md` and `documentation/ENHANCED_EXAMPLES.md`
→ Use hardened examples like `examples/python/client_enhanced.py`

**Deploy to Kubernetes**
→ Check `examples/kubernetes/README.md` and `deployment.yaml`

**Understand the repository history**
→ Read `documentation/Archive/Development-Historical/` for historical summaries

**Add a new example**
→ Read `.github/QUICK_REFERENCE.md` for AI workflow guidance
→ Read `.github/CODING_STANDARDS.md` for organizational standards
→ Place it in the appropriate `examples/<language>/` directory
→ Update that directory's README.md
→ Add a reference in the main README.md

**Add documentation**
→ User-facing docs go in `documentation/`
→ Development notes go in `/documentation/development/`
→ Update links in README.md if important

**Run tests**
→ See the testing section in each example's README
→ Python: `cd examples/python && pytest tests/ -v`
→ TypeScript: `cd examples/typescript && npm run build`
→ Node: `cd examples/node && node --check <file>`

## Design Principles

### 1. Separation of Concerns

- **Examples** = Code to run
- **Documentation** = Information to read
- **Development notes** = Context for maintainers
- **CI/CD** = Automation configuration

### 2. Progressive Complexity

Examples progress from simple to complex:

1. cURL - Simplest, minimal dependencies
2. Basic clients - Core functionality
3. Enhanced clients - Production patterns
4. Specialized examples - Advanced use cases

### 3. Self-Contained Examples

Each example directory should be:

- Runnable on its own
- Well-documented
- Include necessary configuration files
- Not depend on other examples

### 4. Documentation Proximity

Documentation lives close to what it documents:

- Main README - Overview of everything
- `/documentation/` - Cross-cutting concerns
- `examples/<lang>/README.md` - Language-specific details
- Code comments - Implementation details

### 5. Future-Proof Organization

The structure accommodates growth:

- New languages → `examples/<new-language>/`
- New doc types → `docs/<category>/`
- New deployment targets → `examples/<platform>/`
- Archive old content → `documentation/Archive/Reports-Historical/`

## Common Patterns

### Example README Structure

```markdown
# <Language> Examples

Brief description of what this directory contains.

## Prerequisites
- Required software/versions
- Environment setup

## Quick Start
1. Install dependencies
2. Set environment variables
3. Run the example

## Examples
Brief description of each file and when to use it

## Testing
How to run tests (if applicable)

## Troubleshooting
Common issues and solutions
```

### Adding New Content

**New language example:**

1. Create `examples/<language>/`
2. Add README.md in that directory
3. Add code files
4. Update main README.md
5. Add CI if needed

**New documentation:**

1. Determine category (user-facing or development)
2. Create file in appropriate `/documentation/` subdirectory
3. Use clear, descriptive filename
4. Update README.md if it's important
5. Add links from related docs

**New feature to existing example:**

1. Add code in the appropriate `examples/<language>/` directory
2. Update that directory's README.md
3. Add tests if complex
4. Update main README.md if it's a major feature
5. Consider adding to `documentation/ENHANCED_EXAMPLES.md` if it demonstrates hardened patterns

## Maintenance

### Regular Tasks

- **Monthly**: Review dependencies for updates
- **Quarterly**: Audit documentation accuracy
- **Per release**: Update version references
- **As needed**: Archive outdated examples

### Keeping It Clean

- Remove temporary files not in `.gitignore`
- Move old development notes to `documentation/Archive/Development-Historical/`
- Consolidate duplicate documentation
- Keep the root directory minimal

### When to Archive

Content should be archived when:

- Examples are superseded by better implementations
- Documentation becomes obsolete
- Development notes are no longer relevant
- But may be needed for historical context

Archive location: `documentation/Archive/`

## Questions?

- **General questions**: Check `documentation/FAQ.md`
- **Integration help**: See `documentation/BEST_PRACTICES.md`
- **Contributing**: Read `.github/CODING_STANDARDS.md`
- **Issues**: Open a GitHub issue

---

**Maintained by**: Repository maintainers
**Last Updated**: 2026-01-24
**Related Docs**:

- [AI-Assisted Development Workflow](../.github/QUICK_REFERENCE.md)
- [Coding Standards](../.github/CODING_STANDARDS.md)
- [Agent Quick Reference](../.github/AGENT_QUICK_REFERENCE.md)
- [Best Practices](BEST_PRACTICES.md)
- [FAQ](FAQ.md)
