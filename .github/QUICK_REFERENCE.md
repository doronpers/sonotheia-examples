# AI-Assisted Development Workflow

A real-world showcase of how I use AI/LLM agents throughout my development process. This isn't prescriptive—it's documentation of what works for me, evolving over time.

## 🎯 Workflow Philosophy

**Core principle:** AI as a collaborative partner, not just a code generator.

```
┌─────────────────────────────────────────────────────────────────┐
│                    MY DEVELOPMENT LOOP                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. PLAN ──► 2. BUILD ──► 3. REVIEW ──► 4. ITERATE            │
│      ▲           │            │              │                  │
│      │           ▼            ▼              │                  │
│      │       [AI Agent]  [AI Review]         │                  │
│      │           │            │              │                  │
│      └───────────┴────────────┴──────────────┘                  │
│                                                                 │
│   Key: Humans guide, AI assists, both verify                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Tech Stack Context

- **Backend**: Python 3.x, FastAPI, numpy, audio processing
- **Frontend**: Vite, React/TypeScript
- **Infrastructure**: Docker, nginx, SSL/TLS
- **Deployment**: Render.com / cloud platforms

## 📋 The Multi-Stage Workflow

### Stage 1: Problem Definition (Human-Led)

Before touching code or asking AI:
1. **What problem am I solving?** (1-2 sentences)
2. **What does success look like?** (concrete test cases)
3. **What constraints exist?** (file sizes, latency, security)

**Example from my audio processing work:**
```
Problem: Users need to upload audio files up to 800MB for analysis
Success: POST /upload accepts file, returns analysis in <30s
Constraints: Must handle concurrent uploads, nginx defaults block large files
```

### Stage 2: Design & Planning (AI-Assisted)

**Prompt pattern I use:**
```
I'm building [specific feature].

Context:
- Tech: FastAPI, Docker, nginx
- Constraint: [specific constraint]
- Existing pattern: [reference to codebase]

Help me design the approach. Consider:
1. Edge cases
2. Error handling
3. Testing strategy
```

**AI output review checklist:**
- [ ] Does it align with my existing patterns?
- [ ] Are the dependencies appropriate?
- [ ] Did it miss any constraints I mentioned?

### Stage 3: Implementation (Collaborative)

#### My AI Coding Standards

Based on lessons learned, I always verify:

```python
# ✅ Convert numpy types before JSON serialization
def convert_numpy_types(obj):
    """AI often forgets this - always check!"""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

# ✅ Proper temp file handling (AI often uses None for fd)
import tempfile
fd, path = tempfile.mkstemp()
try:
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
finally:
    os.unlink(path)  # Always cleanup

# ✅ SSL in Docker (AI forgets ca-certificates)
# Dockerfile must include:
# RUN apk add --no-cache ca-certificates
```

### Stage 4: AI-Assisted Code Review

**Multi-agent review pattern:**

```
┌──────────────────┐     ┌──────────────────┐
│   Agent 1        │     │   Agent 2        │
│   (Generator)    │────►│   (Reviewer)     │
│   Creates code   │     │   Critiques it   │
└──────────────────┘     └──────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────────────────────────────────┐
│              Human Decision                  │
│   Accept / Modify / Request Alternative     │
└─────────────────────────────────────────────┘
```

**Review prompt I use:**
```
Review this code for:
1. Security issues (especially input validation)
2. Error handling gaps
3. Performance concerns for large files (up to 800MB)
4. Testing blind spots

Code:
[paste code]
```

### Stage 5: Testing (AI-Generated, Human-Verified)

**My pytest patterns:**
```python
# Always use real file descriptors in tests
def test_temp_file_handling(tmp_path):
    """AI-generated tests often mock file ops incorrectly."""
    test_file = tmp_path / "test.wav"
    test_file.write_bytes(b"test data")

    result = process_file(str(test_file))

    assert result is not None
    assert not test_file.exists()  # Verify cleanup

# Use monkeypatch, not fragile mocks
def test_with_monkeypatch(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    # Test with controlled environment
```

## 🔄 Iteration Patterns

### When AI Gets It Wrong

**Pattern: Clarify and Constrain**
```
That solution doesn't handle [specific case].

Additional context:
- We're using [specific library/pattern]
- The constraint is [specific constraint]
- Here's an example that does work: [code snippet]

Please revise.
```

### When AI Gets It Right

**Document for future sessions:**
```
This pattern works well for [use case]:
[code snippet with comments]

Key insight: [what made this work]
```

## 📊 Workflow Metrics I Track

| Metric | What It Tells Me |
|--------|------------------|
| AI suggestions accepted as-is | Am I prompting effectively? |
| Bugs from AI code | What patterns to verify? |
| Time to working feature | Is the workflow efficient? |
| Rework after review | Where are the gaps? |

## 🧠 Lessons Learned

### Things AI Consistently Gets Wrong (for me)

1. **numpy → JSON serialization** - Always check
2. **Docker SSL certificates** - Always add ca-certificates
3. **File descriptor handling** - Always use proper fd patterns
4. **nginx defaults** - Always set client_max_body_size

### Things AI Does Well

1. **Boilerplate generation** - FastAPI endpoints, Pydantic models
2. **Test case generation** - Given good examples
3. **Documentation** - Docstrings, README sections
4. **Refactoring** - When given clear patterns to follow

## 🔗 Related Resources in This Repo

- [Start Simple](../documentation/workflow-guides/start-simple.md) - Begin with three questions
- [Multi-Agent Workflow](../documentation/workflow-guides/multi-agent-workflow.md) - Multiple AI checks
- [Learning Journal Template](../templates/learning-journal.md) - Track your progress

## 🔗 Additional Resources

- [Repository Organization](AGENT_QUICK_REFERENCE.md) - Quick reference for maintaining repo structure
- [Coding Standards](CODING_STANDARDS.md) - Complete standards and guidelines
- [Best Practices](../documentation/BEST_PRACTICES.md) - Integration best practices

---

*This workflow evolves. Last updated: 2026-01-04*
