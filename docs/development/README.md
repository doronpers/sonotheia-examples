# Development Documentation

This directory contains development notes, integration summaries, and historical context for maintainers and contributors.

## Files in This Directory

### Integration Documentation
- **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** - Complete integration summary including all features, metrics, and accomplishments
- **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** - Enhanced examples integration details from sonotheia-enhanced repository
- **[XLAYER_STATUS.md](XLAYER_STATUS.md)** - XLayer voice integrity concepts integration notes

### Agent Resources
- **[SOURCES.md](SOURCES.md)** - Source references and workspace information for coding agents

## Purpose

These files document:
- **Development decisions** made during repository creation
- **Integration approach** for incorporating features from other repositories
- **Implementation details** that provide context for future changes
- **Historical context** for why things are structured as they are

## Who Should Read These?

- **Maintainers** - Understanding past decisions and integration history
- **Contributors** - Learning the context before making significant changes
- **Agents** - Accessing source information and development patterns

## When to Add Files Here

Add files to this directory when they:
- Document development or integration processes
- Provide historical context for future maintainers
- Are not needed by end users of the examples
- Reference internal development decisions or workflows

## When to Use Other Locations

- **User-facing docs** → `/docs/` (FAQ, best practices, guides)
- **Example-specific docs** → `examples/<language>/README.md`
- **Contributing guidelines** → `.github/`
- **Essential notes** → `/NOTES.md` in root

## Archive Policy

When development notes become outdated:
1. Consider if they still provide valuable historical context
2. If yes, keep them here
3. If no, move to `docs/development/archive/` subdirectory
4. Update links in other documentation

---

**Note**: End users integrating the Sonotheia API typically don't need these files. Direct them to the main [README](../../README.md) and user-facing documentation in `/docs/`.
