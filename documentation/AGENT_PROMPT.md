# Agent Prompts for Repository Coding Agents

> **For Complete Instructions**: See [OPTIMAL_AGENT_PROMPT.md](OPTIMAL_AGENT_PROMPT.md) - the comprehensive, unified prompt that includes all standards, workflows, security requirements, and best practices.

This document provides **specialized prompt variants** for specific tasks. For the full baseline instructions, always refer to OPTIMAL_AGENT_PROMPT.md first.

## When to Use This Document

- **General work**: Use [OPTIMAL_AGENT_PROMPT.md](OPTIMAL_AGENT_PROMPT.md)
- **Specialized tasks**: Use the task-specific prompts below in addition to the optimal prompt

## Quick Reference

| Task Type | Prompt to Use | Additional Reading |
|-----------|---------------|-------------------|
| General coding | [OPTIMAL_AGENT_PROMPT.md](OPTIMAL_AGENT_PROMPT.md) | Required baseline |
| Documentation work | [Documentation variant](#for-documentation-work) below | + INDEX.md |
| Code examples | [Code examples variant](#for-code-examples) below | + BEST_PRACTICES.md |
| Structural changes | [Structural variant](#for-structural-changes) below | + REPOSITORY_STRUCTURE.md |
| Maintenance | [Maintenance variant](#for-maintenance-tasks) below | + DOCUMENTATION_PRINCIPLES.md |

## Specialized Prompts

### For Documentation Work

```
You are working on documentation for sonotheia-examples repository.

READ FIRST:
- docs/INDEX.md - Documentation hub
- docs/DOCUMENTATION_PRINCIPLES.md - Dieter Rams principles applied
- docs/REPOSITORY_STRUCTURE.md - Organization guide

APPLY THESE PRINCIPLES:
1. Less but better - Essential content only
2. Task-oriented - Organize by user goals
3. Progressive disclosure - Simple → Advanced → Deep
4. Single source of truth - No duplication
5. Multiple navigation paths - Purpose, topic, type

STRUCTURE:
- User guides → docs/
- Workflow guides → docs/workflow-guides/
- Dev context → docs/development/
- Templates → templates/

DOCUMENT TEMPLATE:
# Title - Clear Purpose

[Brief description and audience]

## Quick Start/Overview
[Orient users immediately]

## Main Content
[Organized by goals]

## Related Resources
[Help users go deeper]

UPDATE CHECKLIST:
- [ ] Clear purpose statement
- [ ] Follows existing template
- [ ] Added to docs/INDEX.md
- [ ] Cross-references updated
- [ ] Links verified
- [ ] Follows Dieter Rams principles
```

### For Code Examples

```
You are adding code examples to sonotheia-examples repository.

READ FIRST:
- docs/INDEX.md - Find similar examples
- examples/<your-language>/README.md - Language patterns
- docs/BEST_PRACTICES.md - API integration patterns

APPLY THREE QUESTIONS:
1. What problem does this example solve?
2. What should users learn from it?
3. What are the constraints (dependencies, versions, etc.)?

STRUCTURE:
examples/<language>/
├── README.md (required)
├── tests/ (if complex)
└── source files

EXAMPLE REQUIREMENTS:
- Error handling included
- Environment variables (no hardcoded secrets)
- Clear comments on non-obvious code
- Follows language conventions
- Works with documented versions

README STRUCTURE:
# <Language> Examples

## Prerequisites
[Required software, versions]

## Quick Start
[1-2-3 steps to run]

## Examples
[Describe each file and when to use]

## Testing
[How to test]

UPDATE CHECKLIST:
- [ ] README.md in example directory
- [ ] Tests pass
- [ ] No secrets in code
- [ ] Main README.md updated
- [ ] Follows existing language patterns
```

### For Structural Changes

```
You are making structural changes to sonotheia-examples repository.

READ FIRST:
- docs/DOCUMENTATION_PRINCIPLES.md - Design philosophy
- .github/CODING_STANDARDS.md - Standards
- docs/REPOSITORY_STRUCTURE.md - Current structure

BEFORE CHANGING STRUCTURE:
Apply Dieter Rams' principles:
1. Does this make docs more useful?
2. Does this simplify or complicate?
3. Does this create or reduce duplication?
4. Will this age well?
5. Is this truly necessary?

IF MOVING FILES:
- Use git mv to preserve history
- Search for all references: grep -r "old/path" --include="*.md" .
- Update docs/INDEX.md
- Update all cross-references
- Verify all links work

IF ADDING DIRECTORIES:
- Justify need (apply "less but better")
- Follow existing naming (no numbers, clear names)
- Update REPOSITORY_STRUCTURE.md
- Update INDEX.md

MAINTAIN:
- Root directory ≤ 5 files
- Clear separation: docs/, examples/, .github/
- No deep nesting
- Consistent naming

VERIFY AFTER CHANGES:
- [ ] All links work
- [ ] All tests pass
- [ ] docs/INDEX.md updated
- [ ] REPOSITORY_STRUCTURE.md updated
- [ ] Root directory still minimal
- [ ] Applied Dieter Rams principles
```

### For Maintenance Tasks

```
You are performing maintenance on sonotheia-examples repository.

READ FIRST:
- docs/INDEX.md - Complete navigation
- docs/DOCUMENTATION_PRINCIPLES.md - Quality standards

MAINTENANCE CHECKLIST:

Links:
- [ ] All internal links work
- [ ] All example references valid
- [ ] Updated paths after moves

Content:
- [ ] Remove duplicates (apply "environmentally friendly")
- [ ] Consolidate similar docs (apply "minimal")
- [ ] Archive obsolete content → docs/development/archive/
- [ ] Update version references

Structure:
- [ ] Root directory ≤ 5 files
- [ ] All examples have README.md
- [ ] Consistent naming throughout
- [ ] Clear hierarchy maintained

Quality:
- [ ] All tests pass
- [ ] No broken examples
- [ ] Documentation accurate
- [ ] Known limitations documented

Apply "thorough down to the last detail" principle.
```

## Usage Examples

### Example 1: Adding a New Python Example

```
I need to add a Python example for batch audio processing with rate limiting.

Using the code examples specialized prompt, please:
1. Apply the three-question framework
2. Create the example in examples/python/
3. Follow existing Python patterns
4. Include tests
5. Update documentation appropriately
```

### Example 2: Reorganizing Documentation

```
I want to improve the organization of API-related documentation.

Using the structural changes specialized prompt, please:
1. Review current structure against Dieter Rams principles
2. Propose improvements that maintain "less but better"
3. Update all references if changes are made
4. Verify nothing breaks
```

### Example 3: Writing a New Guide

```
I need to create a guide for handling webhook events.

Using the documentation work specialized prompt, please:
1. Determine the right location in docs/
2. Follow the document template
3. Add to docs/INDEX.md with proper categorization
4. Cross-reference with related docs
5. Apply progressive disclosure principle
```

## Key Reminders

1. **Always start with the three-question framework** - It prevents wasted effort
2. **Use docs/INDEX.md as your navigation hub** - Everything is organized there
3. **Maintain the minimal root directory** - Only 5 essential files
4. **Apply "less but better"** - Quality over quantity in documentation
5. **Check common AI pitfalls** - numpy types, file descriptors, SSL certs
6. **Test before committing** - All examples must work
7. **Update cross-references** - Keep documentation interconnected
8. **Preserve existing patterns** - Consistency is valuable

## Anti-Patterns to Avoid

❌ Creating new top-level directories without justification  
❌ Duplicating information across multiple documents  
❌ Using numbered or cryptic directory names  
❌ Scattering related documentation  
❌ Adding files to root directory  
❌ Breaking existing documentation links  
❌ Skipping the three-question framework  
❌ Over-documenting simple concepts  

## Success Indicators

✅ Can find any doc in < 2 minutes using docs/INDEX.md  
✅ Root directory has ≤ 5 files  
✅ All tests pass  
✅ All links work  
✅ No duplicate information  
✅ Clear separation: docs/, examples/, .github/  
✅ Applied three-question framework  
✅ Follows Dieter Rams principles  

---

**Version**: 1.0  
**Last Updated**: 2026-01-05  
**For**: AI coding agents, developers, maintainers  
**Philosophy**: Minimal, purposeful, well-organized  

*"Less but better" - Dieter Rams*
