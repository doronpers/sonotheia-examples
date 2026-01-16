# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when working with the Sonotheia API.

## Table of Contents

- [Authentication Issues](#authentication-issues)
- [Audio Format Errors](#audio-format-errors)
- [Rate Limiting](#rate-limiting)
- [Timeout Errors](#timeout-errors)
- [Connectivity Issues](#connectivity-issues)
- [Response Errors](#response-errors)
- [MFA Verification Issues](#mfa-verification-issues)
- [Webhook Problems](#webhook-problems)
- [Performance Issues](#performance-issues)

---

## Authentication Issues

### Error: 401 Unauthorized

**Symptom:**
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

**Possible Causes:**
1. API key is missing or not set
2. API key is incorrect or has been revoked
3. API key is not being sent in the correct header

**Solutions:**

```bash
# Verify API key is set
echo $SONOTHEIA_API_KEY

# If empty, set it:
export SONOTHEIA_API_KEY=your_api_key_here

# Test with curl
curl -H "Authorization: Bearer $SONOTHEIA_API_KEY" \
  https://api.sonotheia.com/v1/voice/deepfake \
  -X POST \
  -F "audio=@test.wav"
```

**Check your code:**

```python
# Python - Ensure header is set correctly
headers = {
    "Authorization": f"Bearer {api_key}",  # Note the "Bearer " prefix
    "Accept": "application/json"
}
```

```javascript
// Node.js - Ensure header is set correctly
const headers = {
  'Authorization': `Bearer ${API_KEY}`,  // Note the "Bearer " prefix
  'Accept': 'application/json'
};
```

### Error: 403 Forbidden

**Symptom:**
```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions for this endpoint"
}
```

**Possible Causes:**
1. API key doesn't have access to the requested endpoint
2. Account has been suspended or tier downgraded

**Solutions:**
- Contact Sonotheia support to verify your API key permissions
- Check your account status in the developer portal

---

## Audio Format Errors

### Error: 400 Bad Request - Invalid audio format

**Symptom:**
```json
{
  "error": "Invalid audio format",
  "message": "Audio must be WAV, MP3, Opus, or FLAC"
}
```

**Solutions:**

```bash
# Check file format
file audio.wav

# Convert to recommended format
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

### Error: 400 Bad Request - Audio file too large

**Symptom:**
```json
{
  "error": "Payload too large",
  "message": "Audio file exceeds maximum size of 10 MB"
}
```

**Solutions:**

```bash
# Check file size
ls -lh audio.wav

# Compress audio or reduce duration
ffmpeg -i long_audio.wav -t 10 -ar 16000 -ac 1 output.wav

# Split into chunks (see streaming examples)
python examples/python/streaming_example.py long_audio.wav
```

### Error: Audio too short

**Symptom:**
```json
{
  "error": "Invalid audio",
  "message": "Audio duration must be at least 3 seconds"
}
```

**Solutions:**

```bash
# Check duration
ffprobe -i audio.wav -show_entries format=duration -v quiet -of csv="p=0"

# If too short, consider:
# 1. Using a longer audio sample
# 2. Padding with silence (not recommended for production)
```

### Error: Invalid sample rate

**Symptom:**
Poor results or warnings in response

**Solutions:**

```bash
# Check sample rate
ffprobe -i audio.wav -show_entries stream=sample_rate -v quiet -of csv="p=0"

# Convert to recommended 16 kHz
ffmpeg -i audio.wav -ar 16000 output.wav
```

---

## Rate Limiting

### Error: 429 Too Many Requests

**Symptom:**
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please retry after 60 seconds"
}
```

**Response Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640000000
```

**Solutions:**

1. **Implement exponential backoff:**

```python
import time
import requests

def call_api_with_retry(url, data, max_retries=5):
    for attempt in range(max_retries):
        response = requests.post(url, data=data)

        if response.status_code == 429:
            # Get retry-after header or use exponential backoff
            retry_after = int(response.headers.get('Retry-After', 2 ** attempt))
            print(f"Rate limited. Retrying after {retry_after}s...")
            time.sleep(retry_after)
            continue

        return response

    raise Exception("Max retries exceeded")
```

2. **Use the enhanced client with rate limiting:**

```python
from client_enhanced import SonotheiaClientEnhanced

# Initialize with rate limit
client = SonotheiaClientEnhanced(
    api_key="your_key",
    rate_limit_per_second=2.0  # Max 2 requests per second
)

result = client.detect_deepfake("audio.wav")
```

3. **Check rate limit headers before making requests:**

```python
def check_rate_limit(response):
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))

    if remaining < 5:
        print(f"⚠️  Only {remaining} requests remaining")
        # Consider throttling your requests
```

---

## Timeout Errors

### Error: Request timeout

**Symptom:**
```
requests.exceptions.Timeout: HTTPSConnectionPool(host='api.sonotheia.com', port=443): Read timed out.
```

**Possible Causes:**
1. Network connectivity issues
2. Large audio file taking too long to process
3. API server experiencing high load

**Solutions:**

1. **Increase timeout:**

```python
import requests

response = requests.post(
    url,
    files=files,
    timeout=30  # Increase from default 10s
)
```

2. **Split large files:**

```python
# For files > 10 seconds, use streaming approach
from streaming_example import process_long_audio

results = process_long_audio(
    "long_audio.wav",
    chunk_duration=10
)
```

3. **Check network connectivity:**

```bash
# Test connection to API
curl -I https://api.sonotheia.com

# Check DNS resolution
nslookup api.sonotheia.com

# Test with verbose output
curl -v https://api.sonotheia.com/v1/voice/deepfake
```

---

## Connectivity Issues

### Error: Connection refused / DNS resolution failed

**Symptom:**
```
requests.exceptions.ConnectionError: Failed to establish a new connection
```

**Solutions:**

1. **Check API URL:**

```python
# Ensure URL is correct
api_url = "https://api.sonotheia.com"  # Note: HTTPS, no trailing slash

# Wrong:
# api_url = "http://api.sonotheia.com"  # Wrong protocol
# api_url = "https://api.sonotheia.com/"  # Trailing slash (will be stripped by client)
```

2. **Check proxy settings:**

```bash
# If behind corporate proxy
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# In Python
proxies = {
    'http': 'http://proxy.company.com:8080',
    'https': 'http://proxy.company.com:8080'
}
response = requests.post(url, proxies=proxies)
```

3. **Check firewall rules:**

```bash
# Test port 443 connectivity
telnet api.sonotheia.com 443

# Or using nc (netcat)
nc -zv api.sonotheia.com 443
```

### Error: SSL/TLS certificate verification failed

**Symptom:**
```
requests.exceptions.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Solutions:**

```bash
# Update CA certificates (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install ca-certificates

# Update certifi package (Python)
pip install --upgrade certifi
```

**Temporary workaround (NOT recommended for production):**

```python
import requests

# Only for debugging - DO NOT use in production
response = requests.post(url, verify=False)
```

---

## Response Errors

### Error: 500 Internal Server Error

**Symptom:**
```json
{
  "error": "Internal server error",
  "request_id": "req_abc123"
}
```

**Solutions:**

1. **Retry the request** - Transient errors may resolve automatically
2. **Check audio file integrity** - Corrupt files may cause server errors
3. **Contact support** with the `request_id` from the error response

### Error: 503 Service Unavailable

**Symptom:**
```json
{
  "error": "Service temporarily unavailable",
  "message": "Please try again later"
}
```

**Solutions:**

1. **Implement circuit breaker pattern:**

```python
from client_enhanced import SonotheiaClientEnhanced

# Enhanced client includes circuit breaker
client = SonotheiaClientEnhanced(api_key="your_key")

try:
    result = client.detect_deepfake("audio.wav")
except Exception as e:
    if "circuit breaker" in str(e).lower():
        print("Service is down, circuit breaker activated")
        # Fall back to alternative logic or queue for later
```

2. **Check API status:**

```bash
# If a status page exists
curl https://status.sonotheia.com
```

### Error: Invalid JSON response

**Symptom:**
```python
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Solutions:**

```python
import requests

response = requests.post(url, data=data)

# Check response before parsing
if response.headers.get('content-type') != 'application/json':
    print(f"Unexpected content type: {response.headers.get('content-type')}")
    print(f"Response body: {response.text}")
    # Handle non-JSON response

try:
    result = response.json()
except ValueError:
    print(f"Failed to parse JSON: {response.text}")
    # Handle parsing error
```

---

## MFA Verification Issues

### Error: Enrollment ID not found

**Symptom:**
```json
{
  "error": "Enrollment not found",
  "message": "No enrollment exists with ID: enroll-123"
}
```

**Solutions:**

1. **Verify enrollment ID exists:**
   - Check that enrollment was completed successfully
   - Ensure enrollment ID is correct (no typos)
   - Verify enrollment hasn't been deleted or expired

2. **Check enrollment process:**
   - Contact your integration engineer for enrollment API documentation
   - Ensure enrollment completed successfully before verification attempts

### Error: Low confidence score

**Symptom:**
```json
{
  "verified": false,
  "enrollment_id": "enroll-123",
  "confidence": 0.45,
  "recommended_action": "defer_to_review"
}
```

**Possible Causes:**
1. Poor audio quality (background noise, low volume)
2. Different recording conditions from enrollment
3. Voice changes (illness, stress)
4. Wrong person attempting verification

**Solutions:**

1. **Improve audio quality:**
   - Use quiet environment
   - Ensure adequate volume
   - Use good quality microphone

2. **Re-enrollment may be needed if:**
   - Original enrollment was in different conditions
   - Significant time has passed
   - Voice has changed

3. **Implement confidence thresholds:**

```python
def handle_mfa_result(result):
    confidence = result['confidence']
    verified = result['verified']

    if verified and confidence > 0.85:
        return "allow"
    elif confidence > 0.50:
        return "defer_to_review"
    else:
        return "deny"
```

---

## Webhook Problems

### Webhooks not being received

**Possible Causes:**
1. Webhook URL is not publicly accessible
2. Firewall blocking incoming requests
3. Incorrect webhook configuration
4. Webhook secret mismatch

**Solutions:**

1. **Test webhook endpoint:**

```bash
# Test from external source
curl -X POST https://your-domain.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

2. **Verify webhook registration:**
   - Contact your integration engineer to verify webhook URL is registered
   - Ensure URL is HTTPS (required for production)

3. **Check webhook signature:**

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature."""
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)

# In webhook handler
signature = request.headers.get('X-Sonotheia-Signature')
if not verify_webhook_signature(request.body, signature, WEBHOOK_SECRET):
    return 401, "Invalid signature"
```

4. **Enable webhook logging:**

```python
import logging

logging.basicConfig(level=logging.DEBUG)

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    logging.debug(f"Received webhook: {request.headers}")
    logging.debug(f"Payload: {request.get_data()}")
    # Process webhook
```

### Webhook timeout

**Symptom:**
Webhook is called but no response within 30 seconds

**Solutions:**

1. **Process asynchronously:**

```python
from queue import Queue
from threading import Thread

webhook_queue = Queue()

def process_webhooks():
    """Background worker to process webhooks."""
    while True:
        payload = webhook_queue.get()
        # Process payload (may take time)
        process_webhook(payload)
        webhook_queue.task_done()

# Start background worker
Thread(target=process_webhooks, daemon=True).start()

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    # Quickly queue and return
    webhook_queue.put(request.json)
    return {'status': 'accepted'}, 202
```

---

## Performance Issues

### Slow response times

**Symptoms:**
- API calls taking > 5 seconds
- High latency values in responses

**Solutions:**

1. **Check audio file size:**

```bash
# Large files take longer to upload and process
ls -lh audio.wav

# Optimize file size
ffmpeg -i large.wav -ar 16000 -ac 1 optimized.wav
```

2. **Use connection pooling:**

```python
from client_enhanced import SonotheiaClientEnhanced

# Enhanced client uses connection pooling
client = SonotheiaClientEnhanced(api_key="your_key")

# Reuse client for multiple requests
for audio_file in audio_files:
    result = client.detect_deepfake(audio_file)
```

3. **Enable concurrent processing:**

```python
from concurrent.futures import ThreadPoolExecutor

def process_file(audio_path):
    return client.detect_deepfake(audio_path)

# Process multiple files concurrently
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(process_file, audio_files))
```

4. **Monitor latency:**

```python
import time

start = time.time()
result = client.detect_deepfake("audio.wav")
latency = time.time() - start

print(f"Total latency: {latency:.2f}s")
print(f"API processing time: {result.get('latency_ms', 0)}ms")

if latency > 5.0:
    print("⚠️  High latency detected")
```

### Memory issues with large batches

**Symptom:**
```
MemoryError: Unable to allocate memory
```

**Solutions:**

1. **Process in smaller batches:**

```python
def process_in_batches(audio_files, batch_size=10):
    for i in range(0, len(audio_files), batch_size):
        batch = audio_files[i:i + batch_size]
        for audio_file in batch:
            yield client.detect_deepfake(audio_file)

# Process all files in batches
for result in process_in_batches(large_file_list):
    # Handle result
    pass
```

2. **Use streaming for long files:**

```python
from streaming_example import process_long_audio

# Automatically splits and streams results
results = process_long_audio("large_file.wav", chunk_duration=10)
```

---

## Debugging Tips

### Enable verbose logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Will show detailed request/response info
```

### Capture request/response details

```python
import requests
import logging

# Enable HTTP request debugging
from http.client import HTTPConnection
HTTPConnection.debuglevel = 1

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```

### Test with minimal example

```bash
# Test with curl to isolate issues
curl -X POST https://api.sonotheia.com/v1/voice/deepfake \
  -H "Authorization: Bearer $SONOTHEIA_API_KEY" \
  -F "audio=@test.wav" \
  -v
```

---

## Getting Help

If you've tried the solutions above and still have issues:

1. **Collect diagnostic information:**
   - Request ID from error responses
   - Session IDs from API calls
   - Full error messages and stack traces
   - Audio file format and size
   - Code snippets showing the issue

2. **Check documentation:**
   - [FAQ](FAQ.md)
   - [Best Practices](BEST_PRACTICES.md)
   - [Audio Preprocessing Guide](AUDIO_PREPROCESSING.md)

3. **Contact support:**
   - Email: support@sonotheia.com
   - Include request IDs and diagnostic information
   - Describe steps to reproduce the issue

4. **Check for known issues:**
   - Review GitHub issues in this repository
   - Check API status page (if available)

---

## Additional Resources

- [API Best Practices](BEST_PRACTICES.md)
- [Enhanced Examples](ENHANCED_EXAMPLES.md)
- [Audio Preprocessing Guide](AUDIO_PREPROCESSING.md)
- [Python Examples](../examples/python/)
- [Node.js Examples](../examples/node/)
