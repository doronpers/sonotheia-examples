# Multi-Agent Workflow: Using Multiple AI Checks

One of the most powerful patterns in AI-assisted development is having multiple AI agents review each other's work. This creates a system of checks and balances that catches issues a single agent might miss.

## The Core Pattern

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Agent 1        │     │   Agent 2        │     │   Agent 3        │
│   (Generator)    │────►│   (Reviewer)     │────►│   (Security)     │
│   Creates code   │     │   Critiques it   │     │   Audits it      │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Human Decision                                │
│         Accept / Modify / Request Alternative / Iterate              │
└─────────────────────────────────────────────────────────────────────┘
```

## Why Multiple Agents?

**Single Agent Limitations:**
- May have blind spots in specific domains
- Can develop consistency bias (following initial approach even when flawed)
- Might miss edge cases in complex scenarios

**Multi-Agent Benefits:**
- Different perspectives catch different issues
- Specialized agents excel in their domains
- Cross-validation increases confidence
- Reduces human review burden

## Three Common Multi-Agent Patterns

### Pattern 1: Generator → Reviewer

**Best for:** General code development

**Setup:**
1. **Agent 1 (Generator):** Creates initial code
2. **Agent 2 (Reviewer):** Reviews for correctness, style, and issues
3. **Human:** Makes final decision

**Example prompt sequence:**

```markdown
## To Agent 1 (Generator):
Create a FastAPI endpoint that accepts audio file uploads up to 800MB.

Requirements:
- Streaming upload to handle large files
- Validate file type (WAV, Opus)
- Return upload confirmation with file hash
- Handle errors gracefully

Use our existing auth middleware.

---

## To Agent 2 (Reviewer):
Review this FastAPI endpoint code for:

1. **Security issues:**
   - Input validation
   - File type verification
   - Path traversal risks
   - DoS vectors (file size bombs, etc.)

2. **Error handling:**
   - Network interruptions
   - Disk space issues
   - Invalid file formats
   - Timeout scenarios

3. **Performance:**
   - Memory usage with 800MB files
   - Streaming vs. buffering
   - Concurrent upload handling

4. **Best practices:**
   - Alignment with FastAPI patterns
   - Proper use of async/await
   - Resource cleanup (temp files, etc.)

Code:
[paste Agent 1's code]
```

### Pattern 2: Generator → Security Auditor → Reviewer

**Best for:** Security-critical code (authentication, file handling, API endpoints)

**Setup:**
1. **Agent 1 (Generator):** Creates code
2. **Agent 2 (Security):** Focused security audit
3. **Agent 3 (Reviewer):** General code review
4. **Human:** Final decision

**Example:**

```markdown
## To Agent 2 (Security Auditor):
Perform a security audit on this file upload endpoint:

Focus on:
1. **Input validation:** File type, size, content
2. **Path traversal:** Are file paths properly sanitized?
3. **Resource exhaustion:** Can this be abused for DoS?
4. **Injection risks:** Any command or SQL injection vectors?
5. **Authentication/Authorization:** Proper checks in place?
6. **Data exposure:** Any sensitive data in logs or errors?

Code:
[paste code]

Provide specific issues with line numbers and severity (Critical/High/Medium/Low).
```

### Pattern 3: Multiple Specialists → Human Integration

**Best for:** Complex features touching multiple domains

**Setup:**
1. **Agent 1 (Backend):** Backend implementation
2. **Agent 2 (Frontend):** Frontend implementation
3. **Agent 3 (Integration):** Reviews how they work together
4. **Human:** Integrates and tests

**Example:**

```markdown
## To Agent 3 (Integration Reviewer):
Review how this backend and frontend work together:

Backend endpoint: [paste backend code]
Frontend client: [paste frontend code]

Check for:
1. **API contract consistency:** Do types/schemas match?
2. **Error handling:** Are backend errors properly handled in frontend?
3. **Edge cases:** What happens when network fails, server times out, etc.?
4. **Race conditions:** Any async issues between client and server?
5. **User experience:** Clear loading states, error messages?
```

## Real-World Example: Audio Upload Feature

### Session 1: Initial Implementation

**Agent 1 (Generator):**
```python
# Created FastAPI endpoint for audio upload
@app.post("/upload")
async def upload_audio(file: UploadFile):
    contents = await file.read()
    # Process audio
    return {"status": "success"}
```

**Agent 2 (Reviewer) found:**
- ❌ Reads entire file into memory (fails with 800MB files)
- ❌ No file type validation
- ❌ No error handling
- ❌ Missing authentication

### Session 2: Revised Implementation

**Agent 1 (Generator) - revised with streaming:**
```python
@app.post("/upload")
async def upload_audio(
    file: UploadFile,
    api_key: str = Depends(verify_api_key)
):
    if file.content_type not in ["audio/wav", "audio/opus"]:
        raise HTTPException(400, "Invalid file type")

    fd, path = tempfile.mkstemp(suffix=".wav")
    try:
        with os.fdopen(fd, 'wb') as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                f.write(chunk)
        # Process file at path
        return {"status": "success", "file_hash": compute_hash(path)}
    finally:
        os.unlink(path)
```

**Agent 2 (Security Auditor) found:**
- ✅ Streaming approach (good)
- ✅ File type validation (good)
- ✅ Auth check (good)
- ⚠️ Missing file size limit check
- ⚠️ compute_hash might fail on some files

### Session 3: Final Polish

**Human decision:** Accepted with minor fixes for the warnings.

## Prompt Templates for Common Reviews

### Security Review

```markdown
Review this code for security issues:

**Focus areas:**
1. Input validation (file types, sizes, formats)
2. Path traversal or injection risks
3. Authentication and authorization
4. Resource exhaustion (DoS vectors)
5. Sensitive data exposure
6. Cryptographic issues

**Code:**
[paste code]

**Context:**
- Handles files up to 800MB
- Public-facing API endpoint
- Deployed on shared infrastructure

Provide specific issues with line numbers and risk level.
```

### Performance Review

```markdown
Review this code for performance issues:

**Focus areas:**
1. Memory usage with large inputs (up to 800MB)
2. CPU efficiency for processing
3. Concurrency handling (50+ simultaneous requests)
4. Blocking operations that should be async
5. Resource leaks (files, connections, memory)

**Code:**
[paste code]

**Load profile:**
- 50 concurrent uploads
- Files: 10MB to 800MB
- Expected latency: <30s per file

Identify bottlenecks and suggest optimizations.
```

### Integration Review

```markdown
Review how these components integrate:

**Component 1 (Backend):**
[paste backend code]

**Component 2 (Frontend/Client):**
[paste frontend code]

**Check for:**
1. API contract consistency (types, schemas)
2. Error handling alignment
3. Race conditions or timing issues
4. Edge cases (network failures, timeouts)
5. User experience gaps

Identify integration risks and UX issues.
```

## When to Use Multi-Agent vs. Single Agent

### Use Single Agent When:
- Simple, isolated changes
- Well-understood patterns
- Low risk (documentation, tests)
- Time-sensitive fixes

### Use Multi-Agent When:
- Security-critical code
- Complex integrations
- Large files or scale issues
- New patterns or architectures
- Public-facing APIs

## Best Practices

### 1. Give Each Agent Clear Focus

❌ **Don't:**
> "Review this code for everything"

✅ **Do:**
> "Review this code for security issues only. Focus on input validation and auth."

### 2. Provide Context

❌ **Don't:**
> "Review this function"

✅ **Do:**
> "Review this audio upload function. It handles files up to 800MB from untrusted users. Deployed on shared infrastructure with 2GB RAM containers."

### 3. Request Specific Output

❌ **Don't:**
> "What do you think?"

✅ **Do:**
> "List issues with line numbers, severity (Critical/High/Medium/Low), and suggested fixes."

### 4. Iterate Based on Findings

Don't just collect feedback—act on it and re-review:

```
Session 1: Generate → Review (found 5 issues)
Session 2: Fix issues → Review (found 2 remaining)
Session 3: Fix remaining → Review (approved) → Human test
```

## Common Pitfalls

### Pitfall 1: Too Many Agents

**Problem:** Diminishing returns with >3 agents
**Solution:** Stick to 2-3 specialized agents

### Pitfall 2: Vague Prompts

**Problem:** "Review this code" yields generic feedback
**Solution:** Specific focus areas and context

### Pitfall 3: Ignoring Conflicts

**Problem:** Agents give contradicting advice
**Solution:** Human decides based on constraints and priorities

### Pitfall 4: No Human Judgment

**Problem:** Blindly accepting all AI suggestions
**Solution:** Evaluate each suggestion against your requirements

## Measuring Effectiveness

Track these metrics to see if multi-agent review helps:

| Metric | Good Sign | Bad Sign |
|--------|-----------|----------|
| Bugs caught in review | Increasing | No change |
| Bugs in production | Decreasing | No change |
| Time to working feature | Same or better | Much longer |
| Developer confidence | Higher | Lower |

## Advanced Pattern: Adversarial Review

For critical code, use an adversarial approach:

```markdown
## To Agent 1 (Generator):
Create a secure file upload endpoint.

## To Agent 2 (Attacker):
Try to break this endpoint. How would you:
1. Upload malicious files?
2. Cause resource exhaustion?
3. Bypass authentication?
4. Exploit any vulnerabilities?

## To Agent 3 (Defender):
Given these attack vectors, how do we defend?
What additional checks are needed?
```

This simulates red team / blue team security review.

## Quick Reference

**For any code change, ask:**

1. **Is this security-critical?**
   - YES → Use Generator → Security → Reviewer
   - NO → Continue

2. **Is this complex or multi-component?**
   - YES → Use specialized agents per component
   - NO → Continue

3. **Is this low-risk?**
   - YES → Single agent is fine
   - NO → Use Generator → Reviewer minimum

## Related Resources

- [AI-Assisted Development Workflow](../../.github/QUICK_REFERENCE.md) - Full workflow guide
- [Start Simple](start-simple.md) - The three-question framework
- [Learning Journal Template](../../templates/learning-journal.md) - Track your progress

---

*Part of the AI-Assisted Development Workflow
Last updated: 2026-01-04*
