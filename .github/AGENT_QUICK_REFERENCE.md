# Agent Quick Reference: Repository Organization & AI Workflow

This is a quick reference guide for coding agents to maintain the organization of the sonotheia-examples repository and follow effective AI-assisted development practices.

## 📋 Before Making Changes

**ALWAYS** read these files first:
1. `.github/QUICK_REFERENCE.md` - **AI-Assisted Development Workflow** (essential for effective collaboration)
2. `.github/CODING_STANDARDS.md` - Complete standards and guidelines
3. `docs/REPOSITORY_STRUCTURE.md` - Full structure documentation
4. This file - Quick reference for organization decisions

## 🤖 AI-Assisted Development Quick Guide

Before writing code, apply the **Three-Question Framework**:

1. **What problem am I solving?** (1-2 sentences)
2. **What does success look like?** (concrete, testable outcomes)
3. **What constraints exist?** (performance, scale, security, infrastructure)

**See:** [Start Simple Guide](../documentation/workflow-guides/start-simple.md) for detailed framework.

### Common AI Pitfalls to Check

Based on this repository's experience, **ALWAYS verify**:

```python
# ✅ numpy type conversion for JSON serialization
if isinstance(obj, np.integer): return int(obj)
if isinstance(obj, np.floating): return float(obj)
if isinstance(obj, np.ndarray): return obj.tolist()

# ✅ Proper temp file handling (use fd properly)
fd, path = tempfile.mkstemp()
try:
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
finally:
    os.unlink(path)

# ✅ Docker SSL certificates
# Always include in Dockerfile: RUN apk add --no-cache ca-certificates
```

**See:** [AI-Assisted Development Workflow](QUICK_REFERENCE.md) for full checklist.

## 🎯 Quick Decision Tree

### Adding a New File

**Is it a code example?**
→ YES: Place in `examples/<language>/`
→ NO: Continue...

**Is it user-facing documentation?**
→ YES: Place in `/docs/`
→ NO: Continue...

**Is it development notes or integration context?**
→ YES: Place in `/docs/development/`
→ NO: Continue...

**Is it essential configuration or core documentation?**
→ YES: Place in root (but ask yourself if it's REALLY essential)
→ NO: Reconsider if this file is needed

### Modifying Existing Code

1. **Identify the file location** - Don't move files unless necessary
2. **Update related documentation** - Especially README files
3. **Run tests** - Ensure nothing breaks
4. **Update links** - If you changed file locations

### Adding Documentation

**User needs to know this?**
→ `/docs/` with clear filename like `FEATURE_GUIDE.md`

**Internal development context?**
→ `/docs/development/` with descriptive name

**Explains a specific example?**
→ Update that example's `README.md`

## 📁 Standard Locations

| File Type | Location | Example |
|-----------|----------|---------|
| Code examples | `examples/<lang>/` | `examples/python/client.py` |
| Tests | `examples/<lang>/tests/` | `examples/python/tests/test_client.py` |
| User docs | `docs/` | `docs/FAQ.md` |
| Dev notes | `docs/development/` | `docs/development/INTEGRATION_SUMMARY.md` |
| CI/CD | `.github/workflows/` | `.github/workflows/python-ci.yml` |
| Config templates | Root | `.env.example` |
| Essential docs | Root | `README.md`, `NOTES.md`, `LICENSE` |

## ✅ Organization Checklist

When making changes, verify:

- [ ] Root directory remains minimal (6-8 files max)
- [ ] All examples have their own README.md
- [ ] Tests are in `tests/` subdirectories
- [ ] User docs are in `/docs/`
- [ ] Dev notes are in `/docs/development/`
- [ ] No broken links in documentation
- [ ] All tests still pass
- [ ] New files follow naming conventions

## 🚫 Common Mistakes to Avoid

❌ **Don't** add status files to root (SUMMARY.md, STATUS.md, etc.)
✅ **Do** add them to `/docs/development/`

❌ **Don't** create scattered documentation across multiple locations
✅ **Do** centralize in `/docs/` or example-specific READMEs

❌ **Don't** create temporary files in the repository
✅ **Do** use `/tmp/` for temporary work files

❌ **Don't** move files without checking for references
✅ **Do** search for links and update them

❌ **Don't** commit without updating documentation
✅ **Do** update relevant README files

## 🔧 Common Tasks

### Task: Add a new Python example

```bash
# 1. Create the file
vim examples/python/new_example.py

# 2. Add tests if complex
vim examples/python/tests/test_new_example.py

# 3. Update the Python README
vim examples/python/README.md

# 4. Update main README with reference
vim README.md

# 5. Test
cd examples/python && pytest tests/ -v
```

### Task: Add new documentation

```bash
# 1. Determine type (user-facing or dev notes)

# 2. Create in appropriate location
vim docs/NEW_GUIDE.md          # User-facing
# OR
vim docs/development/NOTES.md   # Development

# 3. Update main README with link
vim README.md

# 4. Update REPOSITORY_STRUCTURE.md if it's a new pattern
vim docs/REPOSITORY_STRUCTURE.md
```

### Task: Reorganize existing files

```bash
# 1. Read CODING_STANDARDS.md first!
cat .github/CODING_STANDARDS.md

# 2. Use git mv to preserve history
git mv OLD_LOCATION NEW_LOCATION

# 3. Search for references
grep -r "OLD_LOCATION" --include="*.md" .

# 4. Update all references

# 5. Run all tests
cd examples/python && pytest tests/ -v
cd examples/typescript && npm run build
cd examples/node && node --check *.js
```

## 🧪 Testing Requirements

**Before committing:**

```bash
# Python tests
cd examples/python
pip install -r requirements.txt
pytest tests/ -v

# TypeScript build
cd examples/typescript
npm install
npm run build

# Node.js syntax
cd examples/node
npm install
node --check batch-processor.js
node --check batch-processor-enhanced.js
node --check webhook-server.js
```

**All must pass before committing!**

## 📝 Commit Message Guide

Good commit messages:
- ✅ "Add streaming audio example to Python"
- ✅ "Update README with new deployment instructions"
- ✅ "Move development notes to docs/development/"
- ✅ "Fix broken links in FAQ documentation"

Bad commit messages:
- ❌ "Update files"
- ❌ "Fix"
- ❌ "WIP"
- ❌ "asdf"

## 🔍 Self-Check Questions

Before finalizing changes, ask:

1. **Is the root directory still minimal?**
   - Only README.md, LICENSE, NOTES.md, .env.example, .gitignore should be there

2. **Are all examples in examples/<language>/?**
   - Each with its own README.md
   - Tests in tests/ subdirectory

3. **Is documentation organized?**
   - User docs in /docs/
   - Dev notes in /docs/development/
   - No scattered markdown files in root

4. **Do tests pass?**
   - All Python tests pass
   - TypeScript builds successfully
   - Node.js files have no syntax errors

5. **Are links updated?**
   - No broken links in documentation
   - References to moved files updated

6. **Is naming consistent?**
   - Following established conventions
   - Clear, descriptive names

## 📚 Key Documents

Must read for effective AI-assisted development:
- `.github/QUICK_REFERENCE.md` - **AI-Assisted Development Workflow** (10 min read) - Start here!
- `.github/CODING_STANDARDS.md` - **Full standards** (20 min read)
- `docs/REPOSITORY_STRUCTURE.md` - **Complete structure guide** (15 min read)
- `docs/03-workflow-building/start-simple.md` - **Three-Question Framework** (10 min read)
- This file - **Quick reference** (5 min read)

## 🆘 When in Doubt

1. **Read** `.github/QUICK_REFERENCE.md` for AI workflow guidance
2. **Apply** the three-question framework before coding
3. **Read** `.github/CODING_STANDARDS.md` for structural changes
4. **Look** at similar existing files for patterns
5. **Consider** multi-agent review for complex changes (see [Multi-Agent Workflow](../documentation/workflow-guides/multi-agent-workflow.md))
6. **Ask** via GitHub issue if you're unsure
7. **Keep it simple** - prefer existing patterns
8. **Document** your decision in commit message

## 🎓 Learning More

Want to understand the organization and workflow better?
1. Start with `.github/QUICK_REFERENCE.md` - AI-Assisted Development Workflow
2. Read `docs/workflow-guides/start-simple.md` - Three-question framework
3. Read `README.md` in root - Repository overview
4. Read `docs/REPOSITORY_STRUCTURE.md` - Structure details
5. Read `.github/CODING_STANDARDS.md` - Complete standards
6. Browse `docs/development/` for historical context
7. Look at existing examples for patterns

---

**Remember**: The goal is to keep the repository clean, organized, and easy to navigate while following effective AI-assisted development practices. When in doubt, preserve the existing organizational patterns and apply the three-question framework.

**Last Updated**: 2026-01-24
**For**: Coding agents and contributors
**See Also**:
- [AI-Assisted Development Workflow](QUICK_REFERENCE.md) - Essential reading
- [CODING_STANDARDS.md](CODING_STANDARDS.md) - Complete standards
- [REPOSITORY_STRUCTURE.md](../documentation/REPOSITORY_STRUCTURE.md) - Structure guide
- [Start Simple](../documentation/workflow-guides/start-simple.md) - Three-question framework
