# Voice MFA Enrollment Guide

This guide explains how to enroll users for Voice Multi-Factor Authentication (MFA) using the Sonotheia API.

## Overview

Voice MFA enrollment creates a unique voice profile (voiceprint) for a user that can be used for subsequent authentication. The enrollment process captures voice samples and generates an `enrollment_id` that identifies the user's voice profile.

## Enrollment Process

### Step 1: Collect Voice Samples

For robust voice authentication, collect **3-5 voice samples** from the user:

- **Duration**: 5-10 seconds per sample
- **Format**: 16 kHz mono WAV (recommended)
- **Content**: Different phrases to capture voice variety
- **Environment**: Quiet, minimal background noise
- **Spacing**: Collect samples across different sessions if possible (e.g., morning, afternoon)

**Recommended Enrollment Phrases:**
- "My voice is my password, verify me"
- "Security is my top priority"
- "I authorize this transaction"
- Free-form: User speaks naturally for 5-10 seconds

### Step 2: Create Enrollment

**Endpoint:** `POST /v1/mfa/voice/enroll`

**Request Format:**
```http
POST /v1/mfa/voice/enroll HTTP/1.1
Host: api.sonotheia.com
Authorization: Bearer YOUR_API_KEY
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="audio_samples"; filename="sample1.wav"
Content-Type: audio/wav

[Binary audio data for sample 1]
--boundary
Content-Disposition: form-data; name="audio_samples"; filename="sample2.wav"
Content-Type: audio/wav

[Binary audio data for sample 2]
--boundary
Content-Disposition: form-data; name="audio_samples"; filename="sample3.wav"
Content-Type: audio/wav

[Binary audio data for sample 3]
--boundary
Content-Disposition: form-data; name="user_id"

user_12345
--boundary
Content-Disposition: form-data; name="metadata"

{"enrollment_date": "2026-01-05", "device": "mobile_app"}
--boundary--
```

**Response Format:**
```json
{
  "enrollment_id": "enroll_abc123def456",
  "user_id": "user_12345",
  "status": "active",
  "quality_score": 0.94,
  "samples_processed": 3,
  "created_at": "2026-01-05T12:34:56Z",
  "metadata": {
    "enrollment_date": "2026-01-05",
    "device": "mobile_app"
  }
}
```

### Step 3: Store Enrollment ID

Save the `enrollment_id` in your database associated with the user. This ID is required for all subsequent voice verification requests.

**Security Best Practices:**
- Treat `enrollment_id` as sensitive data
- Store it encrypted at rest
- Use secure lookup mechanisms
- Implement access controls

## Code Examples

### Python

```python
import requests
import os

def enroll_user_voice(user_id, audio_files, metadata=None):
    """Enroll a user for voice MFA"""
    url = f"{os.getenv('SONOTHEIA_API_URL')}/v1/mfa/voice/enroll"
    headers = {
        "Authorization": f"Bearer {os.getenv('SONOTHEIA_API_KEY')}"
    }

    # Prepare multipart form data
    files = []
    for i, audio_path in enumerate(audio_files):
        files.append(
            ('audio_samples', (f'sample{i+1}.wav', open(audio_path, 'rb'), 'audio/wav'))
        )

    data = {
        'user_id': user_id,
        'metadata': metadata or {}
    }

    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()

        result = response.json()
        enrollment_id = result['enrollment_id']
        quality_score = result.get('quality_score', 0)

        # Check quality threshold
        if quality_score < 0.75:
            print(f"Warning: Low enrollment quality score: {quality_score}")
            print("Consider re-enrolling with better quality audio samples")

        return enrollment_id
    except requests.exceptions.RequestException as e:
        print(f"Enrollment failed: {e}")
        return None
    finally:
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()

# Usage
audio_samples = [
    'sample1.wav',
    'sample2.wav',
    'sample3.wav'
]

enrollment_id = enroll_user_voice(
    user_id='user_12345',
    audio_files=audio_samples,
    metadata={'device': 'mobile_app', 'enrollment_date': '2026-01-05'}
)

if enrollment_id:
    print(f"User enrolled successfully: {enrollment_id}")
    # Store enrollment_id in your database
```

### cURL

```bash
#!/bin/bash
# enroll-user.sh - Enroll a user for voice MFA

API_URL="${SONOTHEIA_API_URL:-https://api.sonotheia.com}"
USER_ID="user_12345"
SAMPLE1="sample1.wav"
SAMPLE2="sample2.wav"
SAMPLE3="sample3.wav"

curl -X POST "${API_URL}/v1/mfa/voice/enroll" \
  -H "Authorization: Bearer ${SONOTHEIA_API_KEY}" \
  -F "user_id=${USER_ID}" \
  -F "audio_samples=@${SAMPLE1}" \
  -F "audio_samples=@${SAMPLE2}" \
  -F "audio_samples=@${SAMPLE3}" \
  -F 'metadata={"device":"mobile_app","enrollment_date":"2026-01-05"}'
```

### TypeScript

```typescript
import FormData from 'form-data';
import fs from 'fs';
import axios from 'axios';

interface EnrollmentResponse {
  enrollment_id: string;
  user_id: string;
  status: string;
  quality_score: number;
  samples_processed: number;
  created_at: string;
  metadata?: Record<string, any>;
}

async function enrollUserVoice(
  userId: string,
  audioFiles: string[],
  metadata?: Record<string, any>
): Promise<string | null> {
  const apiUrl = process.env.SONOTHEIA_API_URL || 'https://api.sonotheia.com';
  const apiKey = process.env.SONOTHEIA_API_KEY;

  const form = new FormData();
  form.append('user_id', userId);

  // Add audio samples
  audioFiles.forEach((filePath, index) => {
    form.append('audio_samples', fs.createReadStream(filePath), {
      filename: `sample${index + 1}.wav`,
      contentType: 'audio/wav'
    });
  });

  if (metadata) {
    form.append('metadata', JSON.stringify(metadata));
  }

  try {
    const response = await axios.post<EnrollmentResponse>(
      `${apiUrl}/v1/mfa/voice/enroll`,
      form,
      {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          ...form.getHeaders()
        }
      }
    );

    const { enrollment_id, quality_score } = response.data;

    if (quality_score < 0.75) {
      console.warn(`Low enrollment quality score: ${quality_score}`);
      console.warn('Consider re-enrolling with better quality audio samples');
    }

    return enrollment_id;
  } catch (error) {
    console.error('Enrollment failed:', error);
    return null;
  }
}

// Usage
const audioSamples = ['sample1.wav', 'sample2.wav', 'sample3.wav'];
const enrollmentId = await enrollUserVoice('user_12345', audioSamples, {
  device: 'mobile_app',
  enrollment_date: '2026-01-05'
});

if (enrollmentId) {
  console.log(`User enrolled successfully: ${enrollmentId}`);
  // Store enrollment_id in your database
}
```

## Voice Verification

Once enrolled, verify the user's voice using the `enrollment_id`:

**Endpoint:** `POST /v1/mfa/voice/verify`

```bash
curl -X POST "https://api.sonotheia.com/v1/mfa/voice/verify" \
  -H "Authorization: Bearer ${SONOTHEIA_API_KEY}" \
  -F "audio=@verification_sample.wav" \
  -F "enrollment_id=enroll_abc123def456"
```

See the main [README](../README.md) and [examples](../examples/) for complete verification examples.

## Best Practices

### Audio Quality
- **Clear speech**: Minimal background noise
- **Natural speaking**: Don't read mechanically
- **Consistent distance**: Maintain same distance from microphone
- **Good hardware**: Use quality microphone (phone mic is usually sufficient)

### Enrollment Quality
- **Multiple samples**: 3-5 samples provide better accuracy
- **Variety**: Use different phrases to capture voice characteristics
- **Time spacing**: Collect samples across sessions for better robustness
- **Quality threshold**: Aim for quality_score > 0.85

### Security
- **Re-enrollment**: Periodically re-enroll users (e.g., annually)
- **Backup authentication**: Provide fallback auth methods
- **Fraud detection**: Monitor failed verification attempts
- **Privacy**: Inform users about voice data collection and storage

## Re-enrollment

Users may need to re-enroll if:
- Voice characteristics change significantly (illness, aging)
- Quality score is consistently low during verification
- Security policy requires periodic re-enrollment
- User changes primary device/microphone

**Endpoint:** `POST /v1/mfa/voice/reenroll`

```http
POST /v1/mfa/voice/reenroll HTTP/1.1
Host: api.sonotheia.com
Authorization: Bearer YOUR_API_KEY
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="enrollment_id"

enroll_abc123def456
--boundary
Content-Disposition: form-data; name="audio_samples"; filename="new_sample1.wav"

[Binary audio data]
--boundary--
```

## Managing Enrollments

### List User Enrollments

```bash
GET /v1/mfa/voice/enrollments?user_id=user_12345
```

### Deactivate Enrollment

```bash
DELETE /v1/mfa/voice/enrollments/enroll_abc123def456
```

### Update Enrollment Metadata

```bash
PATCH /v1/mfa/voice/enrollments/enroll_abc123def456
Content-Type: application/json

{
  "metadata": {
    "last_verified": "2026-01-05T12:34:56Z",
    "device": "updated_mobile_app"
  }
}
```

## Troubleshooting

### Low Quality Score
- **Cause**: Background noise, poor microphone, unclear speech
- **Solution**: Re-record in quiet environment, speak clearly, use better microphone

### Enrollment Failed
- **Cause**: Audio too short, unsupported format, API error
- **Solution**: Check audio duration (5-10s), use WAV format, check API response

### Too Few Samples
- **Cause**: Less than 3 samples provided
- **Solution**: Collect at least 3 voice samples per enrollment

### Verification Failures After Enrollment
- **Cause**: Different recording conditions, voice changed, poor verification audio
- **Solution**: Ensure similar recording conditions, consider re-enrollment

## API Reference

For complete API documentation, including error codes and response schemas:
- Contact your Sonotheia integration engineer
- Refer to [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common errors
- See [BEST_PRACTICES.md](BEST_PRACTICES.md) for audio preprocessing

## Related Documentation

- [Voice MFA Examples](../examples/python/README.md#voice-mfa)
- [Best Practices Guide](BEST_PRACTICES.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [FAQ](FAQ.md)
