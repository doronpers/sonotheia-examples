# Frequently Asked Questions

## General

### What is Sonotheia?

Sonotheia.ai is a voice fraud detection service that provides:
- **Deepfake Detection**: Identify synthetic or manipulated voice recordings
- **Voice MFA**: Multi-factor authentication using voice biometrics
- **SAR Generation**: Suspicious Activity Report submission for compliance

### How do I get an API key?

Contact Sonotheia support or visit the developer portal at https://api.sonotheia.com (API host for Sonotheia.ai) to request API access.

### What audio formats are supported?

The API works best with:
- **Recommended**: 16 kHz mono WAV files
- **Also supported**: Opus, MP3, FLAC
- **Duration**: Optimal results with 3-10 seconds of audio
- **Max size**: Typically 10 MB per file

### Is there a rate limit?

Rate limits depend on your subscription tier. Check the API response headers:
- `X-RateLimit-Limit`: Requests per time window
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

If you hit rate limits, implement exponential backoff and retry logic.

## Authentication

### Where do I store my API key?

**Never** hard-code API keys in source code. Use:
- Environment variables (recommended)
- Secret management services (AWS Secrets Manager, Azure Key Vault)
- Configuration files outside of version control

```bash
# Good - environment variable
export SONOTHEIA_API_KEY=sk_live_...

# Bad - hard-coded
const API_KEY = "sk_live_..."; // DON'T DO THIS
```

### Can I use the same API key for multiple environments?

No. Use separate API keys for:
- Development/testing
- Staging
- Production

This allows you to revoke keys without affecting other environments.

### How do I rotate API keys?

1. Generate a new API key in the developer portal
2. Update your environment configuration
3. Test with the new key
4. Revoke the old key once migration is complete

## Deepfake Detection

### What does the deepfake score mean?

The score ranges from 0.0 to 1.0:
- **0.0 - 0.3**: Likely authentic voice
- **0.4 - 0.7**: Uncertain, may require human review
- **0.8 - 1.0**: Likely synthetic or manipulated

The `label` field provides a human-readable interpretation.

### How accurate is deepfake detection?

Accuracy depends on:
- Audio quality (clear recordings work best)
- Recording duration (3-10s is optimal)
- Type of synthesis technique
- Language and accent

For critical decisions, combine the score with other signals and human review.

### Can I adjust the sensitivity threshold?

The API returns a continuous score. You can adjust your application's threshold based on your use case:
- **High security** (banking): threshold 0.5 or lower
- **Moderate** (customer service): threshold 0.7
- **Permissive** (content moderation): threshold 0.8

### What if I get inconsistent scores for the same audio?

Deepfake detection is a statistical model and may have minor variations. If you see significant inconsistencies:
1. Check audio quality and format
2. Ensure audio isn't corrupted or truncated
3. Contact support with session IDs for investigation

## Voice MFA

### How do I enroll a user's voice?

Voice enrollment is typically a separate API endpoint (not shown in basic examples). Contact your integration engineer for enrollment documentation.

### What is an enrollment ID?

The enrollment ID is a unique identifier for a user's voice profile. It's returned after successful enrollment and used for subsequent verifications.

### How much audio is needed for MFA?

- **Enrollment**: Usually requires 3-5 samples of 5-10 seconds each
- **Verification**: 3-5 seconds of clear speech

### Can MFA work with background noise?

The API handles moderate background noise, but accuracy decreases with:
- Loud background music
- Multiple speakers
- Poor quality phone lines

For best results:
- Use quiet environments for enrollment
- Apply noise reduction preprocessing if available
- Set appropriate confidence thresholds

### What does the confidence score mean?

Confidence ranges from 0.0 to 1.0:
- **0.9+**: Very high confidence match
- **0.7 - 0.9**: Good match
- **0.5 - 0.7**: Uncertain, consider retry
- **< 0.5**: Likely not a match

The `verified` boolean uses an appropriate threshold, but you can also use the raw `confidence` score for custom logic.

## SAR (Suspicious Activity Reports)

### When should I submit a SAR?

Submit SARs for:
- High deepfake detection scores
- Failed MFA attempts
- Unusual access patterns
- Regulatory compliance requirements

### What decisions are available?

- **allow**: Transaction/action was approved despite suspicion
- **deny**: Transaction/action was blocked
- **review**: Flagged for human review (most common)

### How long are SARs retained?

Retention depends on your contract and regulatory requirements (typically 5-7 years for financial institutions).

### Can I retrieve submitted SARs?

Yes, use the SAR retrieval API (contact support for documentation) with the returned `case_id`.

## Troubleshooting

### I'm getting 401 Unauthorized errors

- Verify your API key is correct and active
- Check that you're sending the key in the Authorization header: `Bearer YOUR_KEY`
- Ensure the key hasn't expired or been revoked
- Verify you're using the correct environment (production vs. sandbox)

### I'm getting 400 Bad Request errors

Common causes:
- Missing required fields (audio file, enrollment_id)
- Invalid audio format or corrupted file
- Audio file too large (> 10 MB)
- Invalid JSON in metadata/context fields

Check the error response body for specific details.

### I'm getting timeout errors

- Check your network connectivity
- Verify the API endpoint URL
- Increase timeout values (30s recommended)
- For large files, consider streaming if available

### The API is slow

Typical response times:
- Deepfake detection: 500-1500ms
- MFA verification: 300-800ms

If experiencing slower responses:
- Check your network latency
- Verify audio file size (smaller is faster)
- Contact support if consistently slow

### How do I debug API responses?

Enable detailed logging:

```bash
# cURL - show headers
curl -v ...

# Python
import logging
logging.basicConfig(level=logging.DEBUG)

# Node.js
LOG_LEVEL=debug node script.js
```

Save session IDs from responses for support inquiries.

## Best Practices

### Audio Preprocessing

- **Normalize volume**: Target -16 LUFS
- **Remove silence**: Trim leading/trailing silence
- **Resample**: Convert to 16 kHz for consistency
- **Mono conversion**: Convert stereo to mono

### Error Handling

Always implement retry logic with exponential backoff:

```python
import time

def call_api_with_retry(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except requests.exceptions.Timeout:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)  # 1s, 2s, 4s
```

### Caching

Cache results when appropriate:
- Don't re-analyze the same audio repeatedly
- Use session IDs to link related operations
- Cache negative results (likely authentic) longer than suspicious ones

### Monitoring

Track key metrics:
- API response times
- Error rates by type
- Deepfake score distributions
- MFA verification success rates

Set up alerts for:
- High error rates
- Unusual spike in high-risk scores
- API downtime

### Security

- Use HTTPS for all API calls
- Store API keys securely (never in code)
- Implement webhook signature verification
- Log security events (high-risk detections, failed verifications)
- Rotate API keys regularly (every 90 days)

### Compliance

- Obtain user consent before voice processing
- Implement data retention policies
- Maintain audit logs for SARs
- Follow GDPR, CCPA, and other applicable regulations
- Document voice data processing in privacy policy

## Performance Optimization

### Batch Processing

For multiple files:
- Use concurrent requests (5-10 parallel)
- Implement a queue for large batches
- Process overnight for non-urgent analysis

### Latency Reduction

- Use the geographically nearest API endpoint
- Keep audio files small (< 10s)
- Send compressed audio formats (Opus)
- Use HTTP/2 if available

### Cost Optimization

- Cache results to avoid duplicate analysis
- Use appropriate thresholds to reduce false positives
- Implement client-side validation before API calls
- Consider batch pricing for high-volume use

## Getting Help

### Documentation

- API Reference: https://docs.sonotheia.com/api
- Developer Portal: https://api.sonotheia.com (API host for Sonotheia.ai)
- Status Page: https://status.sonotheia.com

### Support

- Email: support@sonotheia.com
- Include: session IDs, error messages, code snippets
- Response time: 24-48 hours (check SLA for your tier)

### Community

- GitHub Issues: https://github.com/doronpers/sonotheia-examples/issues
- Example code: This repository
