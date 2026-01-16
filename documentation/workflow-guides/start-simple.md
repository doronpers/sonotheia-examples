# Start Simple: The Three-Question Framework

Before diving into AI-assisted development, start with clarity. These three questions form the foundation of effective AI collaboration.

## The Three Essential Questions

### 1. What problem am I solving?

**Keep it to 1-2 sentences.** If you can't explain it briefly, you don't understand it yet.

**Examples:**
- ✅ "Users need to upload audio files up to 800MB for deepfake detection"
- ✅ "API responses timeout when processing large batches"
- ❌ "Make the system better and faster" (too vague)
- ❌ "Fix all the issues with audio processing, improve performance, add new features, and refactor the codebase" (too broad)

**Why this matters:**
- Clear problem definition helps AI generate relevant solutions
- Prevents scope creep
- Makes it easier to know when you're done

### 2. What does success look like?

**Define concrete, testable outcomes.** Not aspirations—actual tests you can run.

**Examples:**
```python
# ✅ Concrete success criteria
def test_success():
    # Upload 800MB file
    response = upload_file("large_audio.wav", size_mb=800)
    assert response.status_code == 200
    assert response.json()["analysis_time"] < 30
    assert "deepfake_score" in response.json()

# ❌ Vague success criteria
"The system should work better"
"Users should be happy"
"Performance should improve"
```

**Good success criteria are:**
- Measurable (numbers, not feelings)
- Testable (you can write a test for it)
- Specific (defines exact behavior)
- Binary (pass/fail, not subjective)

### 3. What constraints exist?

**List the non-negotiable limits.** These shape your solution space.

**Common constraint categories:**

**Performance:**
- Response time: "Analysis must complete in <30s"
- Throughput: "Handle 100 concurrent uploads"
- Memory: "Run in 2GB RAM containers"

**Size/Scale:**
- File size: "Support files up to 800MB"
- Batch size: "Process 1000 files per batch"
- Rate limits: "External API allows 10 req/sec"

**Security:**
- Authentication: "Require API key validation"
- Data handling: "Never store audio files longer than 24h"
- Compliance: "Must be GDPR compliant"

**Infrastructure:**
- Platform: "Must deploy on Render.com"
- Technology: "Must use existing FastAPI backend"
- Dependencies: "Cannot add dependencies with GPL licenses"

**Example constraint documentation:**
```markdown
## Constraints
- **File size**: 800MB max (nginx default: 1MB)
- **Processing time**: <30s (users won't wait longer)
- **Concurrency**: 50 simultaneous uploads
- **Storage**: No persistent audio storage (privacy)
- **Tech stack**: Python 3.9+, FastAPI, Docker
```

## Putting It Together

**Template to use:**

```markdown
## Problem Definition

**Problem:** [1-2 sentence description]

**Success Criteria:**
- [ ] [Specific, testable outcome 1]
- [ ] [Specific, testable outcome 2]
- [ ] [Specific, testable outcome 3]

**Constraints:**
- **Performance:** [specific limits]
- **Scale:** [specific limits]
- **Security:** [specific requirements]
- **Infrastructure:** [specific requirements]
```

**Real example from audio processing:**

```markdown
## Problem Definition

**Problem:** Users need to upload large audio files (up to 800MB) for deepfake detection without timeout errors.

**Success Criteria:**
- [ ] POST /v1/voice/deepfake accepts WAV files up to 800MB
- [ ] Analysis completes and returns results in <30 seconds
- [ ] Handles 50 concurrent uploads without degradation
- [ ] Returns structured JSON with deepfake_score and confidence

**Constraints:**
- **Performance:** <30s response time, 50 concurrent uploads
- **Scale:** 800MB max file size
- **Security:** API key authentication, no persistent storage
- **Infrastructure:** FastAPI backend, Docker, nginx reverse proxy, Render.com deployment
```

## How This Helps with AI

### Before Using This Framework

**Vague prompt to AI:**
> "Help me make the audio upload work better"

**AI response:** Generic, unfocused suggestions that may not address your actual needs.

### After Using This Framework

**Clear prompt to AI:**
```
I'm building an audio upload endpoint for deepfake detection.

Problem: Users need to upload audio files up to 800MB for analysis
Success: POST /upload accepts file, returns analysis in <30s
Constraints:
- Must handle 50 concurrent uploads
- nginx default blocks files >1MB
- FastAPI backend on Docker
- Deploy to Render.com

Help me design the approach. Consider:
1. nginx configuration for large files
2. Streaming vs. buffering
3. Timeout handling
4. Memory management
```

**AI response:** Specific, actionable solutions addressing your exact needs.

## Common Mistakes

### Mistake 1: Starting with "How?"

❌ **Don't start with:**
- "How do I upload large files?"
- "How do I make it faster?"
- "What's the best way to...?"

✅ **Start with:**
- "Users need to upload files up to 800MB"
- "Analysis takes 45s, must be <30s"
- "Need to support 100 concurrent requests"

**Why:** "How" questions skip the crucial problem definition step.

### Mistake 2: Multiple Problems at Once

❌ **Don't combine:**
- "Fix uploads AND improve performance AND add new features"

✅ **Separate:**
1. First: "Enable 800MB file uploads"
2. Then: "Reduce analysis time from 45s to <30s"
3. Finally: "Add streaming progress updates"

**Why:** AI (and humans) work better with focused problems.

### Mistake 3: Vague Success Criteria

❌ **Too vague:**
- "Make it work well"
- "Good user experience"
- "Better performance"

✅ **Specific and testable:**
- "Accept 800MB files (currently fails at 1MB)"
- "Return results in <30s (currently takes 45s)"
- "Support 50 concurrent uploads (currently 10)"

**Why:** Vague criteria lead to vague solutions.

## Quick Self-Check

Before asking AI for help, ask yourself:

1. **Can I explain the problem in 30 seconds?**
   - If no → clarify the problem first

2. **Can I write a test that validates success?**
   - If no → define success criteria first

3. **Do I know my non-negotiable constraints?**
   - If no → list them first

**If you answered "no" to any question, stop and clarify before proceeding.**

## Next Steps

Once you have clarity on these three questions:

1. **Share your definition with AI** using the template above
2. **Review AI suggestions** against your criteria
3. **Iterate** if the solution doesn't match your constraints
4. **Document** what worked for future reference

## Related Resources

- [AI-Assisted Development Workflow](../../.github/QUICK_REFERENCE.md) - Full workflow guide
- [Multi-Agent Workflow](multi-agent-workflow.md) - Using multiple AI agents for better results
- [Learning Journal Template](../../templates/learning-journal.md) - Track your progress and insights

---

*Part of the AI-Assisted Development Workflow
Last updated: 2026-01-04*
