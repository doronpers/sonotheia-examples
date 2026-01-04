# Notes, Assumptions, and TODOs

## Assumptions

### API Endpoints and Authentication
- The API uses bearer token authentication via the `Authorization: Bearer <token>` header
- Base URL defaults to `https://api.sonotheia.com`
- Three primary endpoints are assumed based on existing code:
  - `/v1/voice/deepfake` - Deepfake detection
  - `/v1/mfa/voice/verify` - Voice MFA verification
  - `/v1/reports/sar` - SAR (Suspicious Activity Report) submission

### Request/Response Formats
- **Deepfake Detection**:
  - Request: multipart/form-data with `audio` file and optional `metadata` JSON
  - Response: `{ score: number, label: string, latency_ms: number, session_id?: string }`
  
- **MFA Verification**:
  - Request: multipart/form-data with `audio` file, `enrollment_id` string, and optional `context` JSON
  - Response: `{ verified: boolean, enrollment_id: string, confidence: number, session_id?: string }`
  
- **SAR Submission**:
  - Request: JSON body with `session_id`, `decision` (allow/deny/review), `reason`, and optional `metadata`
  - Response: `{ status: string, case_id: string, session_id: string }`

### Audio Requirements
- Recommended format: 16 kHz mono WAV files
- Also supports: Opus, MP3, FLAC
- Optimal duration: 3-10 seconds
- Maximum file size: ~10 MB

### ID Lifecycles and Relationships
- **session_id**: Links related API calls together (e.g., deepfake detection + SAR submission)
- **enrollment_id**: References a user's voice profile for MFA verification
- **case_id**: Unique identifier for submitted SARs, returned after SAR submission

### Webhook Events
- The webhook server example assumes these event types:
  - `deepfake.completed` - Async deepfake detection result
  - `mfa.completed` - Async MFA verification result
  - `sar.submitted` - SAR submission confirmation
- Webhook signature uses HMAC-SHA256 with secret
- Signature header: `X-Sonotheia-Signature`

## TODOs

### Documentation
- [ ] Add more audio preprocessing examples (FFmpeg, SoX commands)
- [ ] Document enrollment process for MFA
- [ ] Add troubleshooting guide for common API errors
- [ ] Create migration guide for API version updates
- [ ] Document webhook payload schemas in detail

### Code Examples
- [ ] Add retry logic examples with exponential backoff
- [ ] Add streaming audio examples (for long recordings)
- [ ] Add example of rate limit handling
- [ ] Create integration test suite with real API (requires API key)
- [ ] Add example of audio validation before API submission

### Infrastructure
- [ ] Add Docker/Podman containerized examples
- [ ] Add example Kubernetes deployment for webhook server
- [ ] Create example CloudFormation/Terraform for AWS deployment
- [ ] Add monitoring/observability examples (Prometheus, Grafana)

### Testing
- [ ] Expand unit test coverage beyond basic request construction
- [ ] Add integration tests with mocked API server
- [ ] Add performance/load testing examples
- [ ] Create test audio files for different scenarios

## Questions for Doron

### API Endpoints and Fields

1. **Enrollment Process**: What is the endpoint and payload structure for initial voice enrollment? The examples reference `enrollment_id` but don't show how to create one.

2. **Webhook Registration**: How do users register webhook URLs with the API? Is there a management endpoint?

3. **SAR Fields**: Are there additional required or optional fields for SAR submission beyond what's shown in the examples (session_id, decision, reason, metadata)?

4. **Error Responses**: What is the standard error response schema? Do errors include error codes, request IDs, or structured error details?

5. **Rate Limits**: What are the actual rate limits per tier? Should examples include specific numbers?

6. **Pagination**: Do any endpoints support pagination (e.g., listing SARs)? What's the pagination format?

### Response Fields

7. **Session ID Generation**: Is `session_id` client-generated or server-generated? Can it be omitted from requests?

8. **Additional Response Fields**: Are there other response fields not documented in the examples (e.g., confidence intervals, model versions, request IDs)?

9. **Deepfake Labels**: What are all possible values for the `label` field in deepfake responses? Examples show "likely_real" and "likely_synthetic" - are there others?

10. **MFA Thresholds**: What confidence threshold does `verified: true` use? Is this configurable?

### Webhook Details

11. **Webhook Event Payloads**: Can you provide complete webhook event payload schemas for all event types?

12. **Webhook Delivery**: Does the API retry failed webhook deliveries? What's the retry policy?

13. **Webhook Security**: Besides signature verification, are there other recommended security measures (IP whitelisting, etc.)?

### Use Cases and Best Practices

14. **Enrollment Best Practices**: How many voice samples are recommended for enrollment? What's the optimal duration?

15. **Audio Preprocessing**: Are there specific preprocessing steps recommended or required before submission?

16. **Session Lifecycle**: How long are sessions retained? Is there a maximum age for linking operations via session_id?

17. **SAR Retrieval**: Is there an endpoint to retrieve submitted SARs by case_id or session_id?

18. **Batch Operations**: Are there batch endpoints for processing multiple audio files in a single request?

### Compliance and Security

19. **Data Retention**: How long does the API retain audio files and analysis results? Is this configurable?

20. **GDPR/Privacy**: Are there specific endpoints or procedures for data deletion requests (right to be forgotten)?

21. **Audit Logs**: Does the API provide audit logs for API access? How can users retrieve them?

### Deployment and Operations

22. **API Versions**: How are API versions managed? Is `/v1/` the current version? How will breaking changes be communicated?

23. **Status Page**: Is there an operational status page for the API? What's the SLA?

24. **Sandbox Environment**: Is there a separate sandbox/test environment with non-production API keys?

25. **Geographic Regions**: Are there region-specific API endpoints for latency optimization or data residency requirements?

## Known Limitations

- Examples do not include actual API credentials (by design - must be provided by user)
- No enrollment endpoint examples (enrollment process not yet documented)
- Webhook examples are demonstration only (require additional hardening for deployment)
- No streaming audio support in examples (future enhancement)
- TypeScript/Node examples require Node.js 18+ (older versions not tested)
- Python examples require Python 3.9+ (older versions not tested)

## Testing Notes

- All examples have been tested for syntax and basic validation
- End-to-end API testing requires valid API credentials
- Mock/unit tests use synthetic data and don't call real API
- Integration tests are manual (no automated test suite with real API)

## Version Compatibility

- **Python**: Tested with 3.9, 3.10, 3.11, 3.12
- **Node.js**: Tested with 18.x, 20.x, 22.x
- **TypeScript**: 5.3+
- **cURL**: Works with standard system curl (7.x+)

## Contributing

When contributing new examples:
1. Do not hard-code API keys or secrets
2. Include error handling and validation
3. Follow existing code style and patterns
4. Update this NOTES.md with any new assumptions or questions
5. Add tests where applicable
6. Update documentation (README, FAQ, BEST_PRACTICES)
