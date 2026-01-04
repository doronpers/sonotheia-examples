# Sonotheia TypeScript Examples

Type-safe TypeScript client for the Sonotheia voice fraud detection API.

## Features

- **Type Safety**: Full TypeScript types for requests and responses
- **Error Handling**: Proper error handling with detailed messages
- **Flexible Configuration**: Environment variables or programmatic config
- **Modern API**: Promise-based async/await interface

## Installation

```bash
npm install
npm run build
```

## Usage

### Command Line

```bash
export SONOTHEIA_API_KEY=your_api_key

# Basic deepfake detection
node dist/index.js path/to/audio.wav

# With MFA verification
node dist/index.js path/to/audio.wav --enrollment-id enroll-123

# With session tracking
node dist/index.js path/to/audio.wav --enrollment-id enroll-123 --session-id session-456
```

### As a Library

```typescript
import { SonotheiaClient } from './index';

const client = new SonotheiaClient({
  apiKey: process.env.SONOTHEIA_API_KEY!,
});

// Deepfake detection
const deepfakeResult = await client.detectDeepfake({
  audioPath: 'audio.wav',
  metadata: { session_id: 'my-session', channel: 'web' },
});
console.log('Deepfake score:', deepfakeResult.score);

// Voice MFA
const mfaResult = await client.verifyMfa({
  audioPath: 'audio.wav',
  enrollmentId: 'enroll-123',
  context: { session_id: 'my-session' },
});
console.log('MFA verified:', mfaResult.verified);

// Submit SAR
const sarResult = await client.submitSar({
  sessionId: 'my-session',
  decision: 'review',
  reason: 'Suspicious activity detected',
});
console.log('SAR case ID:', sarResult.case_id);
```

## Configuration

The client can be configured via environment variables or constructor options:

| Variable | Default | Description |
|----------|---------|-------------|
| `SONOTHEIA_API_KEY` | (required) | Your API key |
| `SONOTHEIA_API_URL` | `https://api.sonotheia.com` | Base API URL |
| `SONOTHEIA_DEEPFAKE_PATH` | `/v1/voice/deepfake` | Deepfake endpoint |
| `SONOTHEIA_MFA_PATH` | `/v1/mfa/voice/verify` | MFA endpoint |
| `SONOTHEIA_SAR_PATH` | `/v1/reports/sar` | SAR endpoint |

## Types

All request and response types are exported:

- `DeepfakeRequest` / `DeepfakeResponse`
- `MfaRequest` / `MfaResponse`
- `SarRequest` / `SarResponse`
- `SonotheiaConfig`

## Error Handling

The client throws errors for:
- Missing API key
- Invalid file paths
- HTTP errors (with response details)
- Network errors

```typescript
try {
  const result = await client.detectDeepfake({ audioPath: 'audio.wav' });
} catch (error) {
  if (axios.isAxiosError(error)) {
    console.error('API error:', error.response?.data);
  } else {
    console.error('Error:', error.message);
  }
}
```
