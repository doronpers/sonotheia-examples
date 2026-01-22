# Best Practices Guide

## Audio Quality

### Recommended Specifications

- **Sample Rate**: 16 kHz (8 kHz minimum, 48 kHz maximum)
- **Bit Depth**: 16-bit PCM
- **Channels**: Mono (stereo will be downmixed)
- **Duration**: 3-10 seconds optimal
- **Format**: WAV (uncompressed) or Opus (compressed)
- **Silence**: Trim excessive leading/trailing silence

### Audio Preprocessing

```python
import librosa
import soundfile as sf

def preprocess_audio(input_path, output_path):
    """Preprocess audio for optimal API performance"""
    # Load audio
    audio, sr = librosa.load(input_path, sr=16000, mono=True)

    # Normalize volume
    audio = librosa.util.normalize(audio)

    # Trim silence (threshold: -40 dB)
    audio, _ = librosa.effects.trim(audio, top_db=40)

    # Ensure minimum duration (3 seconds)
    if len(audio) < sr * 3:
        print("Warning: Audio shorter than 3 seconds")

    # Save as 16kHz mono WAV
    sf.write(output_path, audio, sr, subtype='PCM_16')
```

### Common Issues

- **Too noisy**: Apply noise reduction or use cleaner recording environment
- **Too quiet**: Normalize volume before sending
- **Clipping**: Reduce input gain, avoid over-amplification
- **Compressed artifacts**: Use lossless formats when possible

## API Integration

### Authentication

```python
import os

# Good: Environment variable
API_KEY = os.environ.get('SONOTHEIA_API_KEY')
if not API_KEY:
    raise ValueError("SONOTHEIA_API_KEY must be set")

# Bad: Hard-coded
API_KEY = "sk_live_..."  # DON'T DO THIS
```

### Error Handling

Implement comprehensive error handling:

```python
import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError

def call_api_with_retry(url, **kwargs):
    """Call API with retry logic and proper error handling"""
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            response = requests.post(url, **kwargs, timeout=30)
            response.raise_for_status()
            return response.json()

        except Timeout:
            print(f"Timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
            else:
                raise

        except HTTPError as e:
            # Don't retry client errors (4xx)
            if 400 <= e.response.status_code < 500:
                print(f"Client error: {e.response.text}")
                raise
            # Retry server errors (5xx)
            elif attempt < max_retries - 1:
                print(f"Server error (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay * (2 ** attempt))
            else:
                raise

        except ConnectionError:
            print(f"Connection error (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
            else:
                raise

#### Error Response Contract

The Sonotheia API returns a **standardized error response**. Handle these fields
explicitly so client behavior stays consistent across versions:

```json
{
    "error_code": "VALIDATION_ERROR",
    "message": "Invalid request payload",
    "timestamp": 1705330000.123,
    "contract_version": "1.0",
    "request_id": "req-123"
}
```

Guidance:
- **Always log** `request_id` for support/debugging.
- **Branch on** `error_code` instead of parsing message strings.
- **Treat `contract_version`** as a compatibility hint for future changes.
```

### Rate Limiting

Respect API rate limits:

```python
import time
from collections import deque

class RateLimiter:
    """Simple rate limiter using sliding window"""

    def __init__(self, max_requests=100, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()

    def acquire(self):
        """Wait until a request slot is available"""
        now = time.time()

        # Remove requests outside time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()

        # Wait if at limit
        if len(self.requests) >= self.max_requests:
            sleep_time = self.requests[0] + self.time_window - now
            if sleep_time > 0:
                time.sleep(sleep_time)
                return self.acquire()

        self.requests.append(now)

# Usage
limiter = RateLimiter(max_requests=100, time_window=60)

for audio_file in audio_files:
    limiter.acquire()
    result = detect_deepfake(audio_file)
```

### Response Handling

Always validate responses:

```python
def validate_deepfake_response(response):
    """Validate API response structure"""
    required_fields = ['score', 'label']

    for field in required_fields:
        if field not in response:
            raise ValueError(f"Missing required field: {field}")

    if not 0 <= response['score'] <= 1:
        raise ValueError(f"Invalid score: {response['score']}")

    return response

# Usage
result = detect_deepfake('audio.wav')
validated = validate_deepfake_response(result)
```

## Security

### API Key Management

1. **Storage**
   - Use environment variables or secret management services
   - Never commit keys to version control
   - Rotate keys every 90 days

2. **Access Control**
   - Limit key permissions to minimum required
   - Use separate keys per environment
   - Revoke compromised keys immediately

3. **Transmission**
   - Always use HTTPS
   - Verify SSL certificates
   - Don't log API keys

### Webhook Security

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook came from Sonotheia"""
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)

# Usage in Flask/Django
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-Sonotheia-Signature')
    payload = request.get_data(as_text=True)

    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        return 'Invalid signature', 401

    # Process webhook
    event = request.json
    # ...
```

### Data Privacy

- **Minimize data collection**: Only send required audio
- **Encrypt at rest**: If storing audio locally
- **Delete after processing**: Don't retain audio unnecessarily
- **User consent**: Obtain before voice processing
- **Access logs**: Track who accesses voice data

## Performance

### Caching Strategy

```python
import hashlib
import json
from functools import lru_cache

class APICache:
    """Cache API responses to reduce costs and latency"""

    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl

    def get_audio_hash(self, audio_path):
        """Generate hash of audio file"""
        with open(audio_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def get(self, audio_path):
        """Get cached result if available and fresh"""
        key = self.get_audio_hash(audio_path)

        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result

        return None

    def set(self, audio_path, result):
        """Cache result"""
        key = self.get_audio_hash(audio_path)
        self.cache[key] = (result, time.time())

# Usage
cache = APICache(ttl=3600)  # 1 hour

def detect_deepfake_cached(audio_path):
    # Check cache first
    cached = cache.get(audio_path)
    if cached:
        print("Cache hit")
        return cached

    # Call API
    result = detect_deepfake(audio_path)

    # Cache result
    cache.set(audio_path, result)

    return result
```

### Batch Processing

```python
import asyncio
import aiohttp

async def process_file_async(session, audio_path):
    """Process single file asynchronously"""
    form = aiohttp.FormData()
    form.add_field('audio', open(audio_path, 'rb'))

    async with session.post(API_URL, data=form) as response:
        return await response.json()

async def process_batch(audio_paths, concurrency=5):
    """Process multiple files with controlled concurrency"""
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_process(session, path):
        async with semaphore:
            return await process_file_async(session, path)

    async with aiohttp.ClientSession(headers={'Authorization': f'Bearer {API_KEY}'}) as session:
        tasks = [bounded_process(session, path) for path in audio_paths]
        return await asyncio.gather(*tasks)

# Usage
results = asyncio.run(process_batch(audio_files, concurrency=10))
```

### Latency Optimization

1. **Use appropriate timeouts**
   ```python
   response = requests.post(url, timeout=(5, 30))  # 5s connect, 30s read
   ```

2. **Compress audio when possible**
   ```python
   # Use Opus instead of WAV for 10x size reduction
   # (slightly longer processing time but faster upload)
   ```

3. **Reuse connections**
   ```python
   session = requests.Session()
   session.headers.update({'Authorization': f'Bearer {API_KEY}'})
   # Reuse session for multiple requests
   ```

4. **Parallelize independent operations**
   ```python
   from concurrent.futures import ThreadPoolExecutor

   with ThreadPoolExecutor(max_workers=5) as executor:
       futures = [executor.submit(process_file, f) for f in files]
       results = [f.result() for f in futures]
   ```

## Monitoring and Observability

### Structured Logging

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing"""

    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
        }

        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id

        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms

        return json.dumps(log_data)

# Usage
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Log with extra context
logger.info('API call completed', extra={
    'session_id': 'session-123',
    'duration_ms': 542,
    'score': 0.75
})
```

### Metrics Collection

```python
from prometheus_client import Counter, Histogram

# Define metrics
api_requests = Counter('sonotheia_api_requests_total', 'Total API requests', ['endpoint', 'status'])
api_duration = Histogram('sonotheia_api_duration_seconds', 'API call duration', ['endpoint'])
deepfake_scores = Histogram('sonotheia_deepfake_scores', 'Distribution of deepfake scores')

# Record metrics
def detect_deepfake_with_metrics(audio_path):
    start = time.time()

    try:
        result = detect_deepfake(audio_path)
        api_requests.labels(endpoint='deepfake', status='success').inc()
        deepfake_scores.observe(result['score'])
        return result
    except Exception as e:
        api_requests.labels(endpoint='deepfake', status='error').inc()
        raise
    finally:
        api_duration.labels(endpoint='deepfake').observe(time.time() - start)
```

### Health Checks

```python
def check_api_health():
    """Verify API is reachable and responding"""
    try:
        response = requests.get(
            f"{API_URL}/health",
            headers={'Authorization': f'Bearer {API_KEY}'},
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False

# Run periodically
import schedule

schedule.every(5).minutes.do(check_api_health)
```

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch

def test_deepfake_detection_success():
    """Test successful deepfake detection"""
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {
            'score': 0.85,
            'label': 'likely_synthetic'
        }

        result = detect_deepfake('audio.wav')

        assert result['score'] == 0.85
        assert result['label'] == 'likely_synthetic'

def test_deepfake_detection_error():
    """Test error handling"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout()

        with pytest.raises(requests.exceptions.Timeout):
            detect_deepfake('audio.wav')
```

### Integration Tests

```python
@pytest.mark.integration
def test_api_integration():
    """Test actual API call (requires API key)"""
    if not os.environ.get('SONOTHEIA_API_KEY'):
        pytest.skip("API key not available")

    # Use a known test audio file
    result = detect_deepfake('test_audio.wav')

    assert 'score' in result
    assert 0 <= result['score'] <= 1
    assert 'label' in result
```

## Compliance and Legal

### Data Retention

```python
import datetime

class AudioRetentionPolicy:
    """Enforce data retention policies"""

    def __init__(self, retention_days=90):
        self.retention_days = retention_days

    def should_delete(self, file_timestamp):
        """Check if file should be deleted"""
        age = datetime.datetime.now() - file_timestamp
        return age.days > self.retention_days

    def cleanup_old_files(self, directory):
        """Delete files exceeding retention period"""
        for file in os.listdir(directory):
            path = os.path.join(directory, file)
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(path))

            if self.should_delete(timestamp):
                os.remove(path)
                print(f"Deleted: {file} (age: {(datetime.datetime.now() - timestamp).days} days)")
```

### Audit Logging

```python
def log_voice_processing(user_id, audio_path, result, consent=False):
    """Log voice processing for audit trail"""
    audit_entry = {
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'user_id': user_id,
        'audio_file': os.path.basename(audio_path),
        'result': result,
        'consent_obtained': consent,
        'processing_purpose': 'fraud_detection',
    }

    # Write to secure audit log
    with open('audit.log', 'a') as f:
        f.write(json.dumps(audit_entry) + '\n')
```

### User Consent

```python
def verify_user_consent(user_id):
    """Verify user has consented to voice processing"""
    # Check consent database
    consent = get_user_consent(user_id)

    if not consent or consent['status'] != 'granted':
        raise ValueError(f"No valid consent for user {user_id}")

    if consent['expires_at'] < datetime.datetime.utcnow():
        raise ValueError(f"Consent expired for user {user_id}")

    return True

# Usage
def process_user_audio(user_id, audio_path):
    verify_user_consent(user_id)
    result = detect_deepfake(audio_path)
    log_voice_processing(user_id, audio_path, result, consent=True)
    return result
```

## Migration and Versioning

### API Version Management

```python
class SonotheiaClient:
    """Client with API version support"""

    def __init__(self, api_key, api_version='v1'):
        self.api_key = api_key
        self.api_version = api_version
        # Base URL for Sonotheia.ai API
        self.base_url = f"https://api.sonotheia.com/{api_version}"

    def detect_deepfake(self, audio_path):
        """Call deepfake endpoint with version"""
        url = f"{self.base_url}/voice/deepfake"
        # ...
```

### Graceful Degradation

```python
def detect_deepfake_with_fallback(audio_path):
    """Try primary API, fallback to secondary if unavailable"""
    try:
        return detect_deepfake(audio_path)
    except Exception as e:
        logger.warning(f"Primary API failed: {e}, trying fallback")
        try:
            return detect_deepfake_fallback(audio_path)
        except Exception as e2:
            logger.error(f"Fallback also failed: {e2}")
            # Return conservative default
            return {'score': 0.5, 'label': 'unknown', 'fallback': True}
```

## nginx Configuration for Large File Uploads

When using nginx as a reverse proxy, configure file size limits for audio uploads:

### Basic Configuration

```nginx
# /etc/nginx/nginx.conf or site configuration
http {
    # Set client body size limit (default is 1MB)
    client_max_body_size 100M;
    
    # Increase buffer sizes for large uploads
    client_body_buffer_size 128k;
    
    # Increase timeout for large file uploads
    client_body_timeout 300s;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
}
```

### For Very Large Files (up to 800MB)

For files larger than 100MB, consider:

1. **Direct upload to object storage** (recommended):
   - Upload directly to S3/Cloud Storage
   - Generate pre-signed URLs
   - Process from object storage

2. **Increase nginx limit** (if direct upload not possible):
   ```nginx
   client_max_body_size 800M;
   client_body_buffer_size 1M;
   ```

3. **Streaming upload** (for >800MB):
   - Use chunked uploads
   - Process in streaming mode
   - See `streaming_example.py` for patterns

### Production Recommendations

- **Standard files (<100MB)**: `client_max_body_size 100M`
- **Large files (100-800MB)**: Use object storage direct upload
- **Very large files (>800MB)**: Implement chunked/streaming uploads

## Summary

Key takeaways:
- **Preprocess audio** for optimal quality (16kHz mono WAV)
- **Handle errors gracefully** with retries and timeouts
- **Respect rate limits** with proper throttling
- **Secure API keys** using environment variables
- **Cache results** to reduce costs and latency
- **Monitor performance** with structured logging and metrics
- **Comply with regulations** through consent and retention policies
- **Test thoroughly** with both unit and integration tests
- **Configure nginx** for large file uploads (client_max_body_size 100M+)
