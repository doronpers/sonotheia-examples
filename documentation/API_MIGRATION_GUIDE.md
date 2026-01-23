# API Migration Guide

This guide helps you migrate between different versions of the Sonotheia API.

## Version History

| Version | Release Date | Status | End of Life |
|---------|-------------|--------|-------------|
| v1 | 2024-06-01 | Current | Active |
| v0 (beta) | 2023-11-01 | Deprecated | 2025-06-01 |

## Current Version: v1

The current API version is `v1`. All new integrations should use this version.

**Base URL:** `https://api.sonotheia.com/v1`

## Versioning Strategy

### URL-Based Versioning

The API version is specified in the URL path:

```
https://api.sonotheia.com/v1/voice/deepfake
https://api.sonotheia.com/v1/mfa/voice/verify
https://api.sonotheia.com/v1/reports/sar
```

### Version Selection

- **Recommended**: Specify version explicitly in all API calls
- **Default**: If no version specified, uses latest stable version (currently v1)
- **Headers**: Version can also be specified via `X-API-Version: v1` header

### Breaking vs Non-Breaking Changes

**Non-Breaking Changes** (no migration required):
- Adding new optional fields to requests
- Adding new fields to responses
- Adding new endpoints
- Adding new error codes
- Adding new enum values (with graceful handling)

**Breaking Changes** (requires migration):
- Removing or renaming fields
- Changing field types
- Changing authentication methods
- Changing request/response formats
- Removing endpoints
- Changing default behaviors

Breaking changes will only occur in new major versions (v2, v3, etc.).

## Migration: v0 (beta) → v1

If you're still using the beta API (v0), follow this guide to migrate to v1.

### Timeline

- **v0 Deprecated**: January 1, 2025
- **v0 End of Life**: June 1, 2025
- **Action Required**: Migrate to v1 before June 1, 2025

### Key Changes

#### 1. Base URL Change

**Before (v0):**
```
https://beta-api.sonotheia.com/voice/deepfake
```

**After (v1):**
```
https://api.sonotheia.com/v1/voice/deepfake
```

#### 2. Authentication

**Before (v0):** API key in query parameter
```bash
curl "https://beta-api.sonotheia.com/voice/deepfake?api_key=YOUR_KEY" \
  -F "audio=@file.wav"
```

**After (v1):** Bearer token in Authorization header
```bash
curl "https://api.sonotheia.com/v1/voice/deepfake" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "audio=@file.wav"
```

#### 3. Response Format Changes

**Deepfake Detection:**

**Before (v0):**
```json
{
  "is_deepfake": true,
  "confidence": 0.82,
  "processing_time": 640
}
```

**After (v1):**
```json
{
  "score": 0.82,
  "label": "likely_synthetic",
  "recommended_action": "defer_to_review",
  "latency_ms": 640,
  "session_id": "sess_abc123"
}
```

**Key Changes:**
- `is_deepfake` → `label` (string values: "likely_real", "likely_synthetic", "uncertain")
- `confidence` → `score` (0.0-1.0, where 1.0 = high probability of deepfake)
- `processing_time` → `latency_ms`
- Added `recommended_action` field
- Added `session_id` for tracking

**Voice MFA:**

**Before (v0):**
```json
{
  "match": true,
  "score": 0.93
}
```

**After (v1):**
```json
{
  "verified": true,
  "enrollment_id": "enroll_abc123",
  "confidence": 0.93,
  "session_id": "sess_def456"
}
```

**Key Changes:**
- `match` → `verified`
- `score` → `confidence`
- Added `enrollment_id` echo
- Added `session_id` for tracking

#### 4. Error Response Format

**Before (v0):**
```json
{
  "error": "Invalid audio format"
}
```

**After (v1):**
```json
{
  "error": {
    "code": "INVALID_AUDIO_FORMAT",
    "message": "Invalid audio format",
    "details": {
      "supported_formats": ["wav", "opus", "mp3", "flac"]
    }
  },
  "request_id": "req_xyz789"
}
```

**Key Changes:**
- Structured error objects with codes
- Added error details
- Added request_id for support

#### 5. Rate Limiting

**Before (v0):** No rate limit headers

**After (v1):** Standard rate limit headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1704470400
```

#### 6. New Features in v1

- **Session Tracking**: All operations return `session_id`
- **SAR Integration**: New `/v1/reports/sar` endpoint
- **Webhooks**: Async event notifications
- **Batch Operations**: Process multiple files
- **Enhanced Metadata**: Detailed audio analysis

### Migration Code Examples

#### Python

**Before (v0):**
```python
import requests

response = requests.post(
    'https://beta-api.sonotheia.com/voice/deepfake',
    params={'api_key': 'YOUR_KEY'},
    files={'audio': open('file.wav', 'rb')}
)

data = response.json()
is_deepfake = data['is_deepfake']
confidence = data['confidence']
```

**After (v1):**
```python
import requests
import os

response = requests.post(
    'https://api.sonotheia.com/v1/voice/deepfake',
    headers={'Authorization': f"Bearer {os.getenv('SONOTHEIA_API_KEY')}"},
    files={'audio': open('file.wav', 'rb')}
)

data = response.json()
score = data['score']
label = data['label']  # 'likely_real', 'likely_synthetic', or 'uncertain'
action = data['recommended_action']  # 'accept', 'deny', or 'defer_to_review'
session_id = data['session_id']
```

#### cURL

**Before (v0):**
```bash
curl "https://beta-api.sonotheia.com/voice/deepfake?api_key=YOUR_KEY" \
  -F "audio=@file.wav"
```

**After (v1):**
```bash
curl "https://api.sonotheia.com/v1/voice/deepfake" \
  -H "Authorization: Bearer $SONOTHEIA_API_KEY" \
  -F "audio=@file.wav"
```

#### Node.js

**Before (v0):**
```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const form = new FormData();
form.append('audio', fs.createReadStream('file.wav'));

const response = await axios.post(
  'https://beta-api.sonotheia.com/voice/deepfake',
  form,
  {
    params: { api_key: process.env.API_KEY },
    headers: form.getHeaders()
  }
);

const { is_deepfake, confidence } = response.data;
```

**After (v1):**
```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const form = new FormData();
form.append('audio', fs.createReadStream('file.wav'));

const response = await axios.post(
  'https://api.sonotheia.com/v1/voice/deepfake',
  form,
  {
    headers: {
      'Authorization': `Bearer ${process.env.SONOTHEIA_API_KEY}`,
      ...form.getHeaders()
    }
  }
);

const { score, label, recommended_action, session_id } = response.data;
```

### Migration Checklist

- [ ] Update base URL to `https://api.sonotheia.com/v1`
- [ ] Move API key from query parameter to Authorization header
- [ ] Update response parsing:
  - [ ] `is_deepfake` → `label`
  - [ ] `confidence` → `score`
  - [ ] `match` → `verified`
- [ ] Add session_id tracking
- [ ] Update error handling for structured error responses
- [ ] Implement rate limit header monitoring
- [ ] Test all endpoints with v1
- [ ] Update documentation and API references
- [ ] Remove v0 code after successful migration

### Testing Migration

1. **Set up parallel testing**: Run both v0 and v1 in parallel
2. **Compare responses**: Validate v1 responses match v0 expectations
3. **Load test**: Ensure performance is acceptable
4. **Monitor errors**: Check for any new error patterns
5. **Gradual rollout**: Migrate non-critical flows first

### Rollback Plan

If issues arise during migration:

1. **Keep v0 code**: Don't delete until v1 is stable
2. **Feature flags**: Use flags to toggle between v0 and v1
3. **Monitor metrics**: Track success rates, latency, errors
4. **Support timeline**: v0 supported until June 1, 2025

## Future Migrations

### v1 → v2 (Planned)

**Estimated Release**: Q3 2026

**Potential Changes** (subject to change):
- Enhanced biometric analysis
- Real-time streaming support
- GraphQL API option
- Improved batch processing
- Regional endpoints

**Migration Notice**: 6 months advance notice before v1 deprecation

## Best Practices

### Version Pinning

**Recommended**: Always specify exact version
```python
API_BASE = "https://api.sonotheia.com/v1"  # Pin to v1
```

**Not Recommended**: Using versionless endpoint
```python
API_BASE = "https://api.sonotheia.com"  # Could change unexpectedly
```

### Handling Deprecation

1. **Subscribe to announcements**: Join the developer mailing list
2. **Monitor deprecation headers**: Check `Deprecation` and `Sunset` headers
3. **Set up alerts**: Monitor for deprecation warnings in logs
4. **Plan ahead**: Start migration well before end-of-life date

### Version Detection

```python
def check_api_version():
    """Check current API version and deprecation status"""
    response = requests.get(
        'https://api.sonotheia.com/v1/status',
        headers={'Authorization': f'Bearer {API_KEY}'}
    )

    # Check deprecation headers
    if 'Deprecation' in response.headers:
        print(f"Warning: API version deprecated")
        print(f"Sunset: {response.headers.get('Sunset', 'Not specified')}")

    return response.json()
```

### Graceful Degradation

Handle unknown response fields gracefully:

```python
def parse_response(data):
    """Parse response with forward compatibility"""
    result = {
        'score': data.get('score'),
        'label': data.get('label', 'unknown'),
        'session_id': data.get('session_id')
    }

    # Handle new fields gracefully
    if 'recommended_action' in data:
        result['action'] = data['recommended_action']

    return result
```

## Support

### Getting Help

- **Documentation**: [https://api.sonotheia.com/docs](https://api.sonotheia.com/docs)
- **Email**: support@sonotheia.com
- **Status Page**: [https://status.sonotheia.com](https://status.sonotheia.com)

### Reporting Issues

When reporting migration issues, include:
- Source version (e.g., v0)
- Target version (e.g., v1)
- Example request/response
- Error messages
- Request IDs from headers

## Related Documentation

- [Best Practices Guide](BEST_PRACTICES.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Webhook Schemas](WEBHOOK_SCHEMAS.md)
- [FAQ](FAQ.md)

## Appendix: Complete API Changelog

### v1.0.0 (2024-06-01)

**New Features:**
- Session tracking with session_id
- SAR submission endpoint
- Webhook support
- Batch processing
- Enhanced error responses with codes
- Rate limiting headers

**Breaking Changes:**
- Authentication moved to Authorization header
- Response field renames (see Migration section)
- Structured error responses

**Improvements:**
- Better audio format support
- Lower latency
- More detailed analysis
- Improved accuracy

**Deprecations:**
- v0 API endpoints (end of life: 2025-06-01)

### v0.9.0 (beta) (2024-03-01)

**Changes:**
- Initial beta release
- Basic deepfake detection
- Voice MFA verification
- Query parameter authentication

---

**Last Updated**: January 5, 2026
**Current Version**: v1.0.0
