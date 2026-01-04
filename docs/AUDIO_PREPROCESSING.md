# Audio Preprocessing Guide

This guide covers audio preprocessing techniques for optimal results with the Sonotheia API.

## Recommended Audio Format

For best results, submit audio in the following format:
- **Sample rate**: 16 kHz
- **Channels**: Mono (single channel)
- **Format**: WAV (uncompressed)
- **Duration**: 3-10 seconds
- **Bit depth**: 16-bit PCM

## FFmpeg Examples

[FFmpeg](https://ffmpeg.org/) is a powerful, cross-platform tool for audio/video processing.

### Installation

```bash
# Ubuntu/Debian
apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Basic Conversion

Convert any audio file to the recommended format:

```bash
# Convert to 16 kHz mono WAV
ffmpeg -i input.mp3 -ar 16000 -ac 1 -sample_fmt s16 output.wav

# Shorter form
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

### Extract Audio from Video

```bash
# Extract audio track from video
ffmpeg -i video.mp4 -vn -ar 16000 -ac 1 output.wav
```

### Trim Audio to Optimal Duration

```bash
# Extract first 10 seconds
ffmpeg -i input.wav -t 10 -ar 16000 -ac 1 output.wav

# Extract from 5s to 15s (10 second duration)
ffmpeg -i input.wav -ss 5 -t 10 -ar 16000 -ac 1 output.wav
```

### Split Long Audio into Chunks

```bash
# Split into 10-second chunks
ffmpeg -i long_audio.wav -f segment -segment_time 10 -ar 16000 -ac 1 chunk_%03d.wav

# This creates: chunk_000.wav, chunk_001.wav, chunk_002.wav, etc.
```

### Normalize Audio Volume

```bash
# Normalize audio to -20dB
ffmpeg -i input.wav -af "loudnorm=I=-20:TP=-1.5:LRA=11" -ar 16000 -ac 1 output.wav

# Simpler volume normalization
ffmpeg -i input.wav -filter:a "volume=1.5" -ar 16000 -ac 1 output.wav
```

### Remove Silence

```bash
# Remove leading/trailing silence
ffmpeg -i input.wav -af "silenceremove=start_periods=1:stop_periods=1:start_threshold=-50dB:stop_threshold=-50dB" -ar 16000 -ac 1 output.wav
```

### Reduce Background Noise

```bash
# Apply high-pass filter to remove low-frequency noise
ffmpeg -i input.wav -af "highpass=f=200" -ar 16000 -ac 1 output.wav

# Combined filtering
ffmpeg -i input.wav -af "highpass=f=200,lowpass=f=3000" -ar 16000 -ac 1 output.wav
```

### Check Audio Properties

```bash
# Display audio file information
ffprobe -i input.wav -show_streams -select_streams a:0

# Get duration only
ffprobe -i input.wav -show_entries format=duration -v quiet -of csv="p=0"

# Get sample rate
ffprobe -i input.wav -show_entries stream=sample_rate -v quiet -of csv="p=0"
```

### Batch Processing

```bash
# Convert all MP3 files in a directory
for file in *.mp3; do
  ffmpeg -i "$file" -ar 16000 -ac 1 "${file%.mp3}.wav"
done

# Process with parallel execution (GNU parallel)
ls *.mp3 | parallel ffmpeg -i {} -ar 16000 -ac 1 {.}.wav
```

## SoX Examples

[SoX](http://sox.sourceforge.net/) (Sound eXchange) is the "Swiss Army knife" of audio processing.

### Installation

```bash
# Ubuntu/Debian
apt-get install sox

# macOS
brew install sox

# Windows
# Download from http://sox.sourceforge.net/
```

### Basic Conversion

```bash
# Convert to 16 kHz mono WAV
sox input.mp3 -r 16000 -c 1 output.wav

# With explicit format specification
sox -t mp3 input.mp3 -r 16000 -c 1 -b 16 output.wav
```

### Trim and Extract

```bash
# Extract first 10 seconds
sox input.wav output.wav trim 0 10

# Extract from 5s to 15s
sox input.wav output.wav trim 5 10
```

### Normalize Volume

```bash
# Normalize to maximum volume without clipping
sox input.wav output.wav norm

# Normalize with specific dB level
sox input.wav output.wav gain -n -3
```

### Remove Silence

```bash
# Remove silence at beginning and end
sox input.wav output.wav silence 1 0.1 1% reverse silence 1 0.1 1% reverse

# More aggressive silence removal
sox input.wav output.wav silence 1 0.1 0.1% reverse silence 1 0.1 0.1% reverse
```

### Apply Filters

```bash
# High-pass filter (remove low frequencies)
sox input.wav output.wav highpass 200

# Band-pass filter (keep speech frequencies)
sox input.wav output.wav bandpass 300 3000

# Reduce noise (requires noise profile)
# Step 1: Create noise profile from silence/noise
sox noise.wav -n noiseprof noise.prof
# Step 2: Apply noise reduction
sox input.wav output.wav noisered noise.prof 0.21
```

### Get Audio Information

```bash
# Display file statistics
soxi input.wav

# Get specific properties
soxi -r input.wav  # Sample rate
soxi -c input.wav  # Channels
soxi -d input.wav  # Duration
soxi -b input.wav  # Bit depth
```

### Batch Processing

```bash
# Convert all files in directory
for file in *.mp3; do
  sox "$file" -r 16000 -c 1 "${file%.mp3}.wav"
done
```

## Python Integration

You can call FFmpeg/SoX from Python for preprocessing:

### Using subprocess

```python
import subprocess
import os

def preprocess_audio_ffmpeg(input_path, output_path):
    """Convert audio to optimal format using FFmpeg."""
    command = [
        'ffmpeg',
        '-i', input_path,
        '-ar', '16000',  # Sample rate
        '-ac', '1',      # Mono
        '-y',            # Overwrite output
        output_path
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
    
    return output_path

def preprocess_audio_sox(input_path, output_path):
    """Convert audio to optimal format using SoX."""
    command = [
        'sox',
        input_path,
        '-r', '16000',  # Sample rate
        '-c', '1',      # Mono
        output_path
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"SoX failed: {result.stderr}")
    
    return output_path

# Usage
preprocessed = preprocess_audio_ffmpeg('input.mp3', 'output.wav')
```

### Using pydub (Python library)

```python
from pydub import AudioSegment

def preprocess_with_pydub(input_path, output_path):
    """Convert audio using pydub (which uses FFmpeg under the hood)."""
    # Load audio file
    audio = AudioSegment.from_file(input_path)
    
    # Convert to mono
    audio = audio.set_channels(1)
    
    # Set sample rate to 16kHz
    audio = audio.set_frame_rate(16000)
    
    # Normalize volume
    audio = audio.normalize()
    
    # Export as WAV
    audio.export(output_path, format='wav')
    
    return output_path

# Install: pip install pydub
```

## Node.js Integration

```javascript
const { exec } = require('child_process');
const { promisify } = require('util');

const execPromise = promisify(exec);

async function preprocessAudio(inputPath, outputPath) {
  const command = `ffmpeg -i "${inputPath}" -ar 16000 -ac 1 -y "${outputPath}"`;
  
  try {
    const { stdout, stderr } = await execPromise(command);
    console.log('Preprocessing complete:', outputPath);
    return outputPath;
  } catch (error) {
    throw new Error(`FFmpeg failed: ${error.message}`);
  }
}

// Usage
preprocessAudio('input.mp3', 'output.wav')
  .then(path => console.log('Processed:', path))
  .catch(err => console.error('Error:', err));
```

## Validation Before Submission

Before sending audio to the Sonotheia API, validate the file meets requirements:

### Using FFprobe (FFmpeg)

```bash
# Check if audio meets requirements
ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate,channels,codec_name -of json input.wav
```

### Using soxi (SoX)

```bash
# Validate format
if [ "$(soxi -r input.wav)" != "16000" ]; then
  echo "Warning: Sample rate is not 16kHz"
fi

if [ "$(soxi -c input.wav)" != "1" ]; then
  echo "Warning: Audio is not mono"
fi
```

### Python Validation

```python
import subprocess
import json

def validate_audio(audio_path):
    """Validate audio file meets Sonotheia requirements."""
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'a:0',
        '-show_entries', 'stream=sample_rate,channels,duration,codec_name',
        '-of', 'json',
        audio_path
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise ValueError(f"Invalid audio file: {result.stderr}")
    
    info = json.loads(result.stdout)
    stream = info['streams'][0]
    
    issues = []
    
    # Check sample rate
    sample_rate = int(stream.get('sample_rate', 0))
    if sample_rate != 16000:
        issues.append(f"Sample rate is {sample_rate}Hz, recommended 16000Hz")
    
    # Check channels
    channels = int(stream.get('channels', 0))
    if channels != 1:
        issues.append(f"Audio has {channels} channels, should be mono (1)")
    
    # Check duration
    duration = float(stream.get('duration', 0))
    if duration < 3:
        issues.append(f"Audio is {duration}s, recommend at least 3s")
    elif duration > 10:
        issues.append(f"Audio is {duration}s, optimal is 3-10s")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'sample_rate': sample_rate,
        'channels': channels,
        'duration': duration,
        'codec': stream.get('codec_name')
    }

# Usage
validation = validate_audio('input.wav')
if not validation['valid']:
    for issue in validation['issues']:
        print(f"⚠️  {issue}")
```

## Best Practices

1. **Always validate audio files** before submitting to the API to avoid unnecessary API calls
2. **Normalize volume** to ensure consistent analysis across different recordings
3. **Remove silence** at the beginning and end to improve processing efficiency
4. **Use lossless compression** (WAV, FLAC) during intermediate processing steps
5. **Preserve original files** - keep unprocessed versions for reference
6. **Batch process** when handling multiple files to save time
7. **Test preprocessing** with a few samples before processing large batches
8. **Monitor file sizes** - ensure processed files don't exceed 10 MB

## Common Issues and Solutions

### "Invalid audio format" error
- **Solution**: Convert to 16 kHz mono WAV using FFmpeg or SoX

### "Audio too short" error
- **Solution**: Ensure audio is at least 3 seconds. Use `ffprobe` to check duration

### "Poor quality results"
- **Solution**: Check for background noise, apply filters, normalize volume

### "Processing timeout"
- **Solution**: Split long audio files into chunks (see streaming examples)

## Further Reading

- [FFmpeg Official Documentation](https://ffmpeg.org/documentation.html)
- [SoX Manual](http://sox.sourceforge.net/sox.html)
- [Audio Signal Processing Basics](https://en.wikipedia.org/wiki/Audio_signal_processing)
- [Speech Processing Techniques](https://en.wikipedia.org/wiki/Speech_processing)

## See Also

- [Python Streaming Example](../examples/python/streaming_example.py) - Automatic audio chunking with FFmpeg
- [Best Practices](BEST_PRACTICES.md) - API integration guidelines
- [FAQ](FAQ.md) - Common questions and answers
