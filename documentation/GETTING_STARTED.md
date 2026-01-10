# Getting Started with Sonotheia

> **Goal**: Make your first successful API call in under 5 minutes

This guide walks you through the quickest path from zero to your first deepfake detection result. For comprehensive documentation, see the [main README](../README.md).

## Prerequisites

- A Sonotheia API key (contact your integration engineer if you don't have one)
- An audio file (WAV format recommended, 3-10 seconds)

Don't have an audio file? Use one from our [test audio collection](../examples/test-audio/).

## Choose Your Path

Pick the approach that matches your environment:

### Option A: cURL (Fastest - 2 minutes)

Perfect for testing and CI/CD pipelines.

```bash
# 1. Set your API key
export SONOTHEIA_API_KEY=your_api_key_here

# 2. Run detection
curl -X POST https://api.sonotheia.com/v1/voice/deepfake \
  -H "Authorization: Bearer ${SONOTHEIA_API_KEY}" \
  -H "Accept: application/json" \
  -F "audio=@path/to/your/audio.wav" \
  -F 'metadata={"session_id":"test-session"};type=application/json'
```

**Expected Response:**
```json
{
  "score": 0.23,
  "label": "likely_real",
  "latency_ms": 450,
  "session_id": "test-session"
}
```

✅ **Success!** You've completed your first deepfake detection.

**What the response means:**
- `score`: 0.0-1.0, higher means more likely synthetic (0.23 = probably real)
- `label`: Human-readable interpretation
- `latency_ms`: Processing time in milliseconds
- `session_id`: Identifier for linking related operations

### Option B: Python (5 minutes)

Best for production integrations and complex workflows.

```bash
# 1. Set up environment
cd examples/python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Set credentials
export SONOTHEIA_API_KEY=your_api_key_here

# 3. Run detection
python main.py path/to/your/audio.wav
```

**Output:**
```
✓ Deepfake Detection:
  Score: 0.23
  Label: likely_real
  Latency: 450ms
  Session ID: xyz123
```

✅ **Success!** You've made your first API call with Python.

**Next Steps:**
- Try with your own audio files
- Explore [enhanced features](ENHANCED_EXAMPLES.md) (retry logic, rate limiting)
- Read the [Python README](../examples/python/README.md) for advanced usage

### Option C: TypeScript/Node.js (5 minutes)

Ideal for web applications and modern JavaScript projects.

```bash
# 1. Set up environment
cd examples/typescript
npm install
npm run build

# 2. Set credentials
export SONOTHEIA_API_KEY=your_api_key_here

# 3. Run detection
node dist/index.js path/to/your/audio.wav
```

✅ **Success!** You've integrated Sonotheia with TypeScript.

**Next Steps:**
- Explore [batch processing](../examples/node/README.md) for multiple files
- Set up [webhook handlers](../examples/node/README.md#webhook-server) for async results
- Add TypeScript types to your own project

## What's Next?

Now that you've made your first API call, here are recommended next steps based on your use case:

### For Production Integration
1. Read [Best Practices](BEST_PRACTICES.md) - Security, error handling, rate limiting
2. Explore [Enhanced Examples](ENHANCED_EXAMPLES.md) - Retry logic, circuit breakers
3. Review [Audio Preprocessing](AUDIO_PREPROCESSING.md) - Optimize audio quality
4. Check [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

### For Voice MFA Implementation
1. Review [MFA Enrollment Guide](MFA_ENROLLMENT.md) - Set up voice profiles
2. Try the MFA example:
   ```bash
   python examples/python/main.py audio.wav --enrollment-id enroll-123
   ```
3. Understand the [complete workflow](USE_CASES.md#voice-mfa-workflow)

### For Compliance/SAR Reporting
1. Understand [SAR submission workflow](USE_CASES.md#sar-workflow)
2. Try submitting a test SAR:
   ```bash
   python examples/python/main.py audio.wav \
     --session-id session-123 \
     --decision review \
     --reason "Testing SAR workflow"
   ```
3. Review [Best Practices](BEST_PRACTICES.md#compliance-considerations)

### For Batch Processing
1. Check out [Node.js batch processor](../examples/node/README.md#batch-processor)
2. Try processing multiple files:
   ```bash
   cd examples/node
   npm install
   node batch-processor.js ../test-audio/*.wav
   ```
3. Implement [production patterns](BEST_PRACTICES.md#batch-processing)

## Common First-Time Issues

### "401 Unauthorized"
- **Problem**: Invalid or missing API key
- **Solution**: Double-check your `SONOTHEIA_API_KEY` environment variable
- **Verify**: `echo $SONOTHEIA_API_KEY` (should show your key, not empty)

### "400 Bad Request - Invalid audio format"
- **Problem**: Audio file doesn't meet requirements
- **Solution**: Validate your audio:
  ```bash
  python examples/python/audio_validator.py your-audio.wav
  ```
- **Requirements**: 16 kHz mono WAV recommended, 3-10 seconds optimal

### "Connection refused" or "Connection timeout"
- **Problem**: Network connectivity or firewall issues
- **Solution**: Test basic connectivity:
  ```bash
  curl -I https://api.sonotheia.com
  ```
- **Check**: Firewall rules, proxy settings, DNS resolution

### "Rate limit exceeded"
- **Problem**: Too many requests in a short time
- **Solution**: Implement rate limiting (see [Enhanced Examples](ENHANCED_EXAMPLES.md))
- **Alternative**: Use batch processing with controlled concurrency

For more issues, see the [Troubleshooting Guide](TROUBLESHOOTING.md).

## Quick Reference Card

### Environment Variables
```bash
export SONOTHEIA_API_KEY=your_key_here           # Required
export SONOTHEIA_API_URL=https://api.sonotheia.com  # Optional (default shown)
```

### API Endpoints
- **Deepfake Detection**: `POST /v1/voice/deepfake`
- **Voice MFA**: `POST /v1/mfa/voice/verify`
- **SAR Submission**: `POST /v1/reports/sar`

### Audio Requirements
- **Format**: WAV (16 kHz mono) recommended
- **Also supports**: Opus, MP3, FLAC
- **Duration**: 3-10 seconds optimal, up to 10 minutes supported with streaming
- **Size**: Maximum 10 MB per file

### Response Interpretation
- **Score 0.0-0.3**: Likely real voice
- **Score 0.4-0.7**: Uncertain, consider additional verification
- **Score 0.8-1.0**: Likely synthetic voice

### File Locations
- **Examples**: `/examples/{python|typescript|node|curl}/`
- **Test Audio**: `/examples/test-audio/`
- **Documentation**: `/documentation/`

## Getting Help

**Quick Questions:**
- Check the [FAQ](FAQ.md) - Most common questions answered

**Code Issues:**
- Search [GitHub Issues](https://github.com/doronpers/sonotheia-examples/issues)
- Review [Troubleshooting Guide](TROUBLESHOOTING.md)

**API Support:**
- Contact your Sonotheia integration engineer
- Include: error messages, request/response details, audio characteristics

**Documentation Feedback:**
- Open a [GitHub Issue](https://github.com/doronpers/sonotheia-examples/issues/new)
- Suggest improvements or corrections

## Learn More

- **[Main README](../README.md)** - Complete repository overview
- **[FAQ](FAQ.md)** - Frequently asked questions
- **[Best Practices](BEST_PRACTICES.md)** - Production integration guide
- **[API Reference](../README.md#output-format)** - Detailed API documentation
- **[Use Cases](USE_CASES.md)** - Real-world integration scenarios

---

**Time Investment:**
- ⚡ This guide: 5 minutes
- 📖 Full documentation: 30 minutes
- 🚀 Production-ready integration: 2-4 hours (with testing)

**Ready to dive deeper?** Start with [Best Practices](BEST_PRACTICES.md) or explore [example code](../examples/).
