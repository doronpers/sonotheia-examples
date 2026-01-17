# How to Interpret Results

This guide explains how to properly interpret and use results from Sonotheia's voice fraud mitigation system. Understanding what results are—and what they are not—is critical for effective integration and risk management.

---

## What Results Are

### Suggestive Signals, Not Proofs

Results from Sonotheia are **suggestive signals** that indicate the likelihood of synthetic or manipulated audio. They are:

- **Acoustic indicators** - Measurements of physical and system-consistent properties
- **Risk signals** - Information to inform decision-making within broader security workflows
- **Evidence components** - Part of a comprehensive audit trail for review and analysis

Results help you:
- Identify potentially suspicious audio for further review
- Make more informed decisions in authentication workflows
- Build comprehensive audit trails for compliance and analysis
- Reduce false positives through proper interpretation

### Confidence Bounded

All results include confidence bounds that reflect:

- **Measurement uncertainty** - Acoustic analysis has inherent variability
- **Context dependencies** - Results depend on audio quality, environment, and conditions
- **Indicator limitations** - No single indicator is perfect; results reflect the current state of analysis

**Key Principle**: Higher confidence does not mean "certainty." It means the signal is more reliable within the context of the measurement, not that it represents absolute truth.

---

## What Results Are Not

### Not Identity Proofs

Results are **not**:
- Proof of identity or authenticity
- Absolute determinations of "real" vs "fake"
- Guarantees of detection or security
- Standalone authentication mechanisms

### Not Perfect Detection

The system does **not** provide:
- 100% accuracy or perfect detection rates
- Immunity to adversarial attacks
- Complete elimination of false positives or false negatives
- Absolute certainty in any classification

**Why?** Attackers optimize for what sounds convincing, not what is physically or system-consistent. Sounding real is not the same as being physically or system-consistent. The goal is measurably safer decisions—fewer exceptions, fewer bypasses, fewer successful fraud events—not perfect detection.

---

## Understanding Reason Codes

Results include **reason codes** that explain why a particular signal was generated. These codes:

- Provide transparency into the decision-making process
- Enable debugging and analysis
- Support audit and compliance requirements
- Help tune workflows based on specific indicator patterns

Reason codes are standardized and documented in the [Reason Codes Registry](../governance/REASON_CODES_REGISTRY_PUBLIC.md). Common patterns include:

- **Acoustic anomalies** - Unusual spectral or temporal properties
- **Consistency violations** - Mismatches between expected and observed properties
- **Boundary conditions** - Results near decision thresholds
- **Quality indicators** - Audio quality issues that affect reliability

---

## Deferral as Control

### When to Defer

**Deferral** is a critical control mechanism. Results should be deferred for human review when:

- Confidence bounds are wide or uncertain
- Multiple conflicting signals are present
- Audio quality is poor or degraded
- Reason codes indicate boundary conditions
- Your risk tolerance requires additional verification

### Deferral Workflows

Proper deferral workflows:

1. **Capture all evidence** - Log complete audit trails per the [Evidence Logging Standard](../governance/EVIDENCE_LOGGING_STANDARD_PUBLIC.md)
2. **Route appropriately** - Send to qualified reviewers with proper context
3. **Document decisions** - Record review outcomes and rationale
4. **Learn and improve** - Use deferral patterns to tune thresholds and workflows

**Key Principle**: Deferral is not a failure—it's a designed control mechanism that improves overall security outcomes.

---

## Prohibited Uses

### Do Not Use For:

1. **Standalone Authentication**
   - Results should not be the sole factor in authentication decisions
   - Always combine with other factors (e.g., knowledge-based, possession-based)

2. **Identity Verification**
   - Results do not prove identity
   - Do not use as proof of "who" someone is

3. **Legal Evidence Without Context**
   - Results alone are not sufficient legal evidence
   - Always provide full context, audit trails, and expert interpretation

4. **Automated Blocking Without Review**
   - Do not automatically block users based solely on results
   - Implement review workflows for high-risk signals

5. **Perfect Detection Claims**
   - Do not claim or imply 100% accuracy
   - Do not market as "perfect" or "infallible" detection

### Appropriate Uses:

✅ Risk scoring within multi-factor authentication workflows  
✅ Signal generation for human review queues  
✅ Evidence collection for audit and compliance  
✅ Fraud pattern analysis and investigation  
✅ Workflow optimization based on signal patterns  

---

## Best Practices

### 1. Integrate into Broader Workflows

Results should be one component of a comprehensive security workflow that includes:
- Multiple authentication factors
- Risk-based decision making
- Human review processes
- Continuous monitoring and adjustment

### 2. Use Confidence Bounds Appropriately

- **High confidence + high risk signal** → Strong candidate for review or additional verification
- **Low confidence** → Always defer or require additional factors
- **Conflicting signals** → Defer for expert review

### 3. Maintain Audit Trails

Follow the [Evidence Logging Standard](governance/EVIDENCE_LOGGING_STANDARD_PUBLIC.md) to:
- Capture complete context for each result
- Enable post-incident analysis
- Support compliance requirements
- Improve system understanding over time

### 4. Tune Based on Your Context

- Adjust thresholds based on your risk tolerance
- Monitor false positive/negative rates
- Update workflows based on observed patterns
- Review and refine regularly

### 5. Understand Limitations

- No system is perfect
- Attackers continuously adapt
- Results reflect current state of analysis
- Regular updates and monitoring are essential

---

## Summary

**Results are:**
- Suggestive signals within confidence bounds
- Components of broader security workflows
- Evidence for audit and analysis
- Tools for measurably safer decisions

**Results are not:**
- Identity proofs or absolute determinations
- Perfect detection mechanisms
- Standalone authentication solutions
- Guarantees of security

**Proper use requires:**
- Integration into comprehensive workflows
- Understanding of confidence bounds
- Appropriate deferral mechanisms
- Complete audit trails
- Continuous monitoring and improvement

---

## Related Documentation

- [Promotion Checklist](../governance/PROMOTION_CHECKLIST_PUBLIC.md) - Standards for production deployment
- [Reason Codes Registry](../governance/REASON_CODES_REGISTRY_PUBLIC.md) - Standardized reason codes
- [Evidence Logging Standard](../governance/EVIDENCE_LOGGING_STANDARD_PUBLIC.md) - Audit trail requirements

---

**Remember**: The goal is **measurably safer decisions—fewer exceptions, fewer bypasses, fewer successful fraud events**. This is achieved through proper interpretation, appropriate integration, and continuous improvement, not through claims of perfect detection.
