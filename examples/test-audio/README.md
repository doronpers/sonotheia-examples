# Test Audio Files

This directory contains test audio files for testing the Sonotheia API examples.

## Overview

These test audio files are generated programmatically and represent various scenarios for testing deepfake detection, voice MFA, and other API features.

**Note:** These are synthetic test files, not real voice samples. They are designed for functional testing, not for accuracy evaluation.

## Test Files

### Basic Test Files

| File | Duration | Sample Rate | Description | Use Case |
|------|----------|-------------|-------------|----------|
| `silent_5s.wav` | 5s | 16 kHz | Silent audio | Basic API connectivity |
| `silent_10s.wav` | 10s | 16 kHz | Silent audio | Standard duration tests |
| `silent_3s.wav` | 3s | 16 kHz | Minimum duration | Boundary testing |
| `tone_440hz_5s.wav` | 5s | 16 kHz | 440 Hz sine wave | Audio validation |
| `tone_440hz_10s.wav` | 10s | 16 kHz | 440 Hz sine wave | Extended audio tests |

### Edge Case Files

| File | Duration | Sample Rate | Description | Use Case |
|------|----------|-------------|-------------|----------|
| `short_1s.wav` | 1s | 16 kHz | Too short | Error handling |
| `long_30s.wav` | 30s | 16 kHz | Longer audio | Performance testing |
| `stereo_5s.wav` | 5s | 16 kHz | Stereo (2 channels) | Channel handling |
| `8khz_5s.wav` | 5s | 8 kHz | Low sample rate | Format conversion |
| `48khz_5s.wav` | 5s | 48 kHz | High sample rate | Format conversion |

### Noise Files

| File | Duration | Sample Rate | Description | Use Case |
|------|----------|-------------|-------------|----------|
| `white_noise_5s.wav` | 5s | 16 kHz | White noise | Noise handling |
| `pink_noise_5s.wav` | 5s | 16 kHz | Pink noise | Natural noise simulation |

## Generating Test Files

### Prerequisites

Install ffmpeg for audio generation:

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg
```

### Generate All Test Files

```bash
# From the examples/test-audio directory
python generate_test_audio.py
```

This will create all test audio files defined in the table above.

### Generate Individual Files

#### Silent Audio

```bash
# 5 second silent audio at 16 kHz mono
ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 5 -y silent_5s.wav

# 10 second silent audio
ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 10 -y silent_10s.wav
```

#### Tone Audio

```bash
# 5 second 440 Hz sine wave at 16 kHz mono
ffmpeg -f lavfi -i "sine=frequency=440:sample_rate=16000:duration=5" -ac 1 -y tone_440hz_5s.wav

# 10 second tone
ffmpeg -f lavfi -i "sine=frequency=440:sample_rate=16000:duration=10" -ac 1 -y tone_440hz_10s.wav
```

#### Different Sample Rates

```bash
# 8 kHz audio
ffmpeg -f lavfi -i anullsrc=r=8000:cl=mono -t 5 -y 8khz_5s.wav

# 48 kHz audio
ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t 5 -y 48khz_5s.wav
```

#### Stereo Audio

```bash
# Stereo audio
ffmpeg -f lavfi -i anullsrc=r=16000:cl=stereo -t 5 -y stereo_5s.wav
```

#### Noise Audio

```bash
# White noise
ffmpeg -f lavfi -i "anoisesrc=d=5:c=white:r=16000:a=0.5" -ac 1 -y white_noise_5s.wav

# Pink noise
ffmpeg -f lavfi -i "anoisesrc=d=5:c=pink:r=16000:a=0.5" -ac 1 -y pink_noise_5s.wav
```

## Using Test Files

### Python

```python
from client import SonotheiaClient

client = SonotheiaClient()

# Test with basic file
result = client.detect_deepfake("examples/test-audio/silent_5s.wav")
print(f"Score: {result['score']}")

# Test with tone file
result = client.detect_deepfake("examples/test-audio/tone_440hz_5s.wav")
print(f"Label: {result['label']}")
```

### cURL

```bash
# Test deepfake detection
curl "https://api.sonotheia.com/v1/voice/deepfake" \
  -H "Authorization: Bearer $SONOTHEIA_API_KEY" \
  -F "audio=@examples/test-audio/silent_5s.wav"

# Test MFA verification
curl "https://api.sonotheia.com/v1/mfa/voice/verify" \
  -H "Authorization: Bearer $SONOTHEIA_API_KEY" \
  -F "audio=@examples/test-audio/tone_440hz_5s.wav" \
  -F "enrollment_id=test-enrollment-123"
```

### Batch Testing

```bash
# Test all files
for file in examples/test-audio/*.wav; do
  echo "Testing: $file"
  curl -s "https://api.sonotheia.com/v1/voice/deepfake" \
    -H "Authorization: Bearer $SONOTHEIA_API_KEY" \
    -F "audio=@$file" | jq '.score'
done
```

## Test Scenarios

### Scenario 1: Basic Connectivity

**Files:** `silent_5s.wav`, `tone_440hz_5s.wav`

**Purpose:** Verify basic API connectivity and response format

```python
# Test basic connectivity
client.detect_deepfake("examples/test-audio/silent_5s.wav")
```

### Scenario 2: Duration Boundaries

**Files:** `short_1s.wav`, `silent_3s.wav`, `silent_10s.wav`, `long_30s.wav`

**Purpose:** Test API behavior at duration boundaries

```python
# Test minimum duration (should succeed)
client.detect_deepfake("examples/test-audio/silent_3s.wav")

# Test too short (may fail with error)
try:
    client.detect_deepfake("examples/test-audio/short_1s.wav")
except Exception as e:
    print(f"Expected error: {e}")

# Test long audio
client.detect_deepfake("examples/test-audio/long_30s.wav")
```

### Scenario 3: Format Handling

**Files:** `8khz_5s.wav`, `48khz_5s.wav`, `stereo_5s.wav`

**Purpose:** Test API handling of different audio formats

```python
# Test different sample rates
client.detect_deepfake("examples/test-audio/8khz_5s.wav")
client.detect_deepfake("examples/test-audio/48khz_5s.wav")

# Test stereo (should be downmixed to mono)
client.detect_deepfake("examples/test-audio/stereo_5s.wav")
```

### Scenario 4: Noise Handling

**Files:** `white_noise_5s.wav`, `pink_noise_5s.wav`

**Purpose:** Test API behavior with noisy audio

```python
# Test with noise
result = client.detect_deepfake("examples/test-audio/white_noise_5s.wav")
print(f"Noise handling - Score: {result['score']}, Label: {result['label']}")
```

## Automated Testing

### pytest Integration

```python
import pytest
import glob

@pytest.mark.parametrize("audio_file", glob.glob("examples/test-audio/*.wav"))
def test_all_audio_files(audio_file):
    """Test all audio files in test-audio directory."""
    client = SonotheiaClient()
    
    # Skip files expected to fail
    if "short_1s" in audio_file:
        pytest.skip("File intentionally too short")
    
    result = client.detect_deepfake(audio_file)
    
    assert "score" in result
    assert "label" in result
    assert 0.0 <= result["score"] <= 1.0
```

### Integration Tests

```bash
# Run integration tests with test audio
cd examples/python
pytest tests/test_integration.py -v
```

## File Specifications

All test files follow these specifications (unless specifically testing edge cases):

- **Format:** WAV (uncompressed PCM)
- **Sample Rate:** 16 kHz (unless testing other rates)
- **Bit Depth:** 16-bit
- **Channels:** 1 (mono, unless testing stereo)
- **Encoding:** PCM signed 16-bit little-endian

## Cleanup

To remove all generated test files:

```bash
cd examples/test-audio
rm -f *.wav
```

## Notes

- These test files are **not** suitable for evaluating detection accuracy
- Use real voice samples for accuracy testing
- Test files are generated, not recorded
- Some files intentionally trigger errors for testing error handling
- File sizes are minimal to reduce repository size

## Related Documentation

- [Audio Preprocessing Guide](../../docs/AUDIO_PREPROCESSING.md)
- [Best Practices](../../docs/BEST_PRACTICES.md)
- [Integration Tests](../python/tests/test_integration.py)
- [Troubleshooting](../../docs/TROUBLESHOOTING.md)
