# Integration Examples Contract

This document defines the standard behavior that all integration examples (Python, TypeScript, Node.js) must follow to ensure consistent user experience.

## Environment Variables

### Required
- `SONOTHEIA_API_KEY` - API key for authentication (must be set or examples will exit with clear error)

### Optional
- `SONOTHEIA_API_URL` - Base API URL (defaults to `https://api.sonotheia.com`)
- `SONOTHEIA_DEEPFAKE_PATH` - Deepfake endpoint path (defaults to `/v1/voice/deepfake`)
- `SONOTHEIA_MFA_PATH` - MFA endpoint path (defaults to `/v1/mfa/voice/verify`)
- `SONOTHEIA_SAR_PATH` - SAR endpoint path (defaults to `/v1/reports/sar`)

**Note**: Examples read from process environment variables. They do NOT automatically load `.env` files. Users must export variables or use a tool like `dotenv` if they want `.env` file support.

## Audio File Support

All examples accept the following audio formats:
- `.wav` (recommended: 16 kHz mono)
- `.opus`
- `.mp3`
- `.flac`

Examples must validate file existence and extension before processing.

## CLI Behavior

### Common Arguments

All CLI examples should support:
- Audio file path (positional argument or `--audio` flag)
- `--enrollment-id <id>` - For MFA verification (optional)
- `--session-id <id>` - For SAR submission and session tracking (optional)
- `--output <path>` or `--out <path>` - Write JSON results to file (optional)
- `--pretty` - Pretty-print JSON output (optional)

### SAR Submission Policy

**CRITICAL**: SAR submission must be **explicitly requested** by the user, not triggered by implicit conditions.

- ✅ **Correct**: SAR submitted only when `--session-id` is provided AND user explicitly requests SAR (e.g., via `--submit-sar` flag or similar explicit mechanism)
- ❌ **Incorrect**: SAR automatically submitted based on score thresholds or other implicit conditions

**Rationale**: SAR submission is a compliance action that should never happen automatically. Users must explicitly opt-in.

### Session ID Semantics

- `session_id` is used for:
  1. Linking related API calls (deepfake detection + SAR submission)
  2. Metadata tracking in API requests
- Default behavior:
  - If not provided, examples may generate a default session ID for metadata (e.g., `"demo-session"`)
  - Default session IDs should NOT trigger SAR submission
- When provided via `--session-id`:
  - Used in all API calls for that run
  - Enables SAR submission workflow (if explicitly requested)

## Output Format

### JSON Structure

All examples output JSON with this structure:

```json
{
  "deepfake": {
    "score": 0.23,
    "label": "likely_real",
    "latency_ms": 450,
    "session_id": "session-123"
  },
  "mfa": {
    "verified": true,
    "enrollment_id": "enroll-123",
    "confidence": 0.85,
    "session_id": "session-123"
  },
  "sar": {
    "status": "submitted",
    "case_id": "case-456",
    "session_id": "session-123"
  }
}
```

- All three operations (deepfake, mfa, sar) are optional based on flags provided
- Only operations that were executed appear in the output
- Output is always valid JSON, even on errors (error details in stderr, exit code non-zero)

### Exit Codes

- `0` - Success
- `1` - Error (missing API key, file not found, API error, etc.)
- Examples must print clear error messages to stderr before exiting

## Error Handling

All examples must:
1. Validate API key presence before making any API calls
2. Validate audio file existence and format
3. Handle API errors gracefully with clear messages
4. Exit with non-zero code on any error
5. Never log secrets, PII, or raw audio bytes

## Implementation Checklist

When creating or updating an example, verify:

- [ ] API key validation with clear error message
- [ ] Audio file validation (existence, extension)
- [ ] SAR submission only when explicitly requested (not score-based)
- [ ] Consistent JSON output structure
- [ ] Proper exit codes (0 for success, 1 for errors)
- [ ] Error messages go to stderr, results to stdout
- [ ] No hardcoded secrets
- [ ] README.md documents the example with prerequisites and usage

## Version History

- **2026-01-18**: Initial contract established
  - Standardized SAR submission policy (explicit only)
  - Defined output format and exit codes
  - Clarified environment variable handling
