# Enhanced Examples Integration Guide

This guide explains the enhanced production-ready features added to the Sonotheia examples repository.

## Overview

The enhanced examples extend the basic API integration patterns with production-ready features:

- **Resilience**: Retry logic, circuit breakers, and fault tolerance
- **Performance**: Connection pooling, rate limiting, and concurrency control
- **Observability**: Health checks, metrics, and structured logging
- **Scalability**: Docker, Kubernetes, and cloud deployment patterns
- **Efficiency**: Streaming processing for large files

## Feature Catalog

### 1. Enhanced Python Client (`examples/python/client_enhanced.py`)

**Purpose**: Production-ready Python client with advanced error handling and resilience patterns.

**Key Features**:
- Exponential backoff retry with configurable attempts (default: 3)
- Token bucket rate limiting to prevent API overload
- Circuit breaker pattern with three states (CLOSED, OPEN, HALF_OPEN)
- HTTP connection pooling for better performance
- Automatic retry on transient failures (5xx errors, timeouts)

**When to Use**:
- Production deployments requiring high reliability
- Applications with strict SLA requirements
- Systems that need to handle API rate limits gracefully
- Services requiring fault tolerance

**Example**:
```python
from client_enhanced import SonotheiaClientEnhanced, CircuitBreakerConfig

# Production configuration
circuit_config = CircuitBreakerConfig(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60.0,    # Try recovery after 60s
    success_threshold=2,      # Close after 2 successes
)

with SonotheiaClientEnhanced(
    max_retries=3,
    rate_limit_rps=2.0,      # Max 2 requests/second
    enable_circuit_breaker=True,
    circuit_breaker_config=circuit_config,
) as client:
    result = client.detect_deepfake("audio.wav")
```

**Configuration Options**:
- `max_retries`: Maximum retry attempts (default: 3)
- `rate_limit_rps`: Requests per second limit (None to disable)
- `enable_circuit_breaker`: Enable/disable circuit breaker
- `circuit_breaker_config`: Circuit breaker configuration
- `timeout`: Request timeout in seconds (default: 30)

### 2. Streaming Audio Processor (`examples/python/streaming_example.py`)

**Purpose**: Process long audio files efficiently by splitting into manageable chunks.

**Key Features**:
- Automatic audio splitting using ffmpeg
- Memory-efficient processing (doesn't load entire file)
- Chunk-level results with aggregated statistics
- Automatic SAR submission for high-risk content
- Progress tracking and error handling per chunk

**When to Use**:
- Processing audio files longer than 10 seconds
- Limited memory environments
- Real-time processing requirements
- Batch processing of large recordings

**Example**:
```bash
# Process 30-minute audio file in 10-second chunks
python streaming_example.py long_audio.wav --chunk-duration 10

# With enrollment verification
python streaming_example.py audio.wav \
  --chunk-duration 10 \
  --enrollment-id enroll-123 \
  --session-id stream-session
```

**Requirements**:
- `ffmpeg` must be installed: `apt-get install ffmpeg`
- Audio file in supported format (WAV, MP3, OPUS, FLAC)

**Output**:
```json
{
  "session_id": "stream-session",
  "chunks": [
    {
      "chunk_index": 0,
      "deepfake": {"score": 0.12, "label": "likely_real"},
      "mfa": {"verified": true, "confidence": 0.95}
    }
  ],
  "summary": {
    "total_chunks": 180,
    "avg_deepfake_score": 0.15,
    "max_deepfake_score": 0.68,
    "high_risk_chunks": 2
  }
}
```

### 3. Health Check and Monitoring (`examples/python/health_check.py`)

**Purpose**: Production health checks, readiness probes, and monitoring.

**Key Features**:
- API connectivity validation
- Authentication verification
- Prometheus metrics export
- Continuous monitoring mode
- Kubernetes probe compatible

**When to Use**:
- CI/CD pipelines (pre-deployment validation)
- Kubernetes liveness/readiness probes
- Monitoring and alerting systems
- Service health dashboards

**Modes**:

1. **Single Health Check** (for CI/CD):
```bash
python health_check.py
# Exit code 0 = healthy, 1 = unhealthy
```

2. **Continuous Monitoring**:
```bash
python health_check.py --monitor --interval 60
# Checks every 60 seconds, logs results
```

3. **Prometheus Metrics**:
```bash
python health_check.py --prometheus-port 9090
# Exposes metrics at http://localhost:9090/metrics
```

**Prometheus Metrics**:
- `sonotheia_api_health`: Health status (1=healthy, 0=unhealthy)
- `sonotheia_api_latency_ms`: API response latency
- `sonotheia_api_checks_total`: Total health checks performed
- `sonotheia_api_errors_total`: Total errors encountered

**Kubernetes Integration**:
```yaml
livenessProbe:
  exec:
    command: ["python", "health_check.py"]
  initialDelaySeconds: 30
  periodSeconds: 60

readinessProbe:
  exec:
    command: ["python", "health_check.py"]
  initialDelaySeconds: 10
  periodSeconds: 30
```

### 4. Enhanced Batch Processor (`examples/node/batch-processor-enhanced.js`)

**Purpose**: High-performance batch processing with observability.

**Key Features**:
- Circuit breaker with automatic recovery
- Retry logic with exponential backoff
- Concurrent request processing
- Prometheus metrics endpoint
- Health check endpoint
- Structured logging

**When to Use**:
- Batch processing multiple audio files
- High-throughput requirements
- Production monitoring needed
- Load testing scenarios

**Example**:
```bash
SONOTHEIA_API_KEY=xxx \
CONCURRENT_REQUESTS=10 \
MAX_RETRIES=3 \
node batch-processor-enhanced.js /path/to/*.wav
```

**Environment Variables**:
- `CONCURRENT_REQUESTS`: Parallel requests (default: 5)
- `MAX_RETRIES`: Retry attempts (default: 3)
- `METRICS_PORT`: Metrics server port (default: 9090)

**Endpoints**:
- `GET /metrics`: Prometheus metrics
- `GET /health`: Health check with circuit breaker status

**Metrics**:
- `sonotheia_files_processed_total`: Total files processed
- `sonotheia_files_succeeded_total`: Successful files
- `sonotheia_files_failed_total`: Failed files
- `sonotheia_avg_latency_ms`: Average API latency
- `sonotheia_retries_total`: Total retry attempts
- `sonotheia_circuit_breaker_trips_total`: Circuit breaker openings

### 5. Docker Support

**Purpose**: Containerized deployment of examples.

**Key Features**:
- Pre-built environment with all dependencies
- Includes ffmpeg for streaming examples
- Volume mounting for audio files
- Environment variable configuration
- Docker Compose orchestration

**Building**:
```bash
cd examples/python
docker build -t sonotheia-python .
```

**Running**:
```bash
# Basic example
docker run -e SONOTHEIA_API_KEY=xxx \
  -v $(pwd)/audio:/audio \
  sonotheia-python python main.py /audio/sample.wav

# Enhanced example
docker run -e SONOTHEIA_API_KEY=xxx \
  -v $(pwd)/audio:/audio \
  sonotheia-python python enhanced_example.py /audio/sample.wav --max-retries 5

# Streaming example
docker run -e SONOTHEIA_API_KEY=xxx \
  -v $(pwd)/audio:/audio \
  sonotheia-python python streaming_example.py /audio/long.wav
```

**Docker Compose**:
```bash
cd examples/python

# Run all services
docker-compose up

# Run specific service
docker-compose up sonotheia-enhanced

# Background mode
docker-compose up -d
```

### 6. Kubernetes Deployment (`examples/kubernetes/`)

**Purpose**: Production-grade Kubernetes deployment manifests.

**Components**:
- Deployment with replicas and resource limits
- ConfigMap for centralized configuration
- Secret for secure API key storage
- Service for metrics exposure
- PersistentVolumeClaim for shared storage
- CronJob for periodic health checks
- Health probes (liveness and readiness)

**Quick Start**:
```bash
# Update API key in deployment.yaml
kubectl apply -f examples/kubernetes/deployment.yaml

# Check status
kubectl get pods -l app=sonotheia-processor

# View logs
kubectl logs -f deployment/sonotheia-processor

# Scale deployment
kubectl scale deployment sonotheia-processor --replicas=5
```

**Production Features**:
- Horizontal pod autoscaling (HPA)
- Pod disruption budgets (PDB)
- Network policies for security
- Resource requests and limits
- Anti-affinity for high availability
- Prometheus integration

See [Kubernetes README](examples/kubernetes/README.md) for detailed documentation.

## Best Practices

### Retry Logic

1. **Use exponential backoff** to avoid overwhelming the API
2. **Set reasonable max retries** (3-5 attempts recommended)
3. **Only retry transient failures** (5xx errors, timeouts)
4. **Log retry attempts** for debugging

### Rate Limiting

1. **Know your API limits** (check documentation)
2. **Set conservative limits** (leave headroom)
3. **Use rate limiting for batch operations**
4. **Monitor queue depth** to detect bottlenecks

### Circuit Breakers

1. **Configure based on SLA** (failure threshold, timeout)
2. **Monitor circuit state** (log state transitions)
3. **Alert on circuit opens** (indicates service degradation)
4. **Test recovery behavior** in staging

### Health Checks

1. **Implement both liveness and readiness probes**
2. **Set appropriate timeouts** (don't fail on slow responses)
3. **Export metrics** for monitoring
4. **Test probe behavior** under load

### Monitoring

1. **Export Prometheus metrics** for observability
2. **Set up alerts** for errors, latency, circuit breakers
3. **Use structured logging** (JSON format)
4. **Track business metrics** (high-risk detections)

### Deployment

1. **Use secrets management** (never hardcode keys)
2. **Set resource limits** (prevent resource exhaustion)
3. **Enable autoscaling** for variable load
4. **Implement graceful shutdown**
5. **Use blue-green deployments** for zero downtime

## Troubleshooting

### High Error Rates

1. Check circuit breaker state
2. Verify API key validity
3. Check rate limits
4. Review error logs
5. Test with health check script

### Performance Issues

1. Monitor latency metrics
2. Check concurrent request limits
3. Review resource utilization
4. Optimize chunk duration (streaming)
5. Enable connection pooling

### Circuit Breaker Opens Frequently

1. Increase failure threshold
2. Adjust recovery timeout
3. Check API stability
4. Review retry configuration
5. Monitor API latency

### Kubernetes Pod Crashes

1. Check resource limits
2. Review probe configuration
3. Check persistent volume status
4. Verify API key secret
5. Check application logs

## Migration Guide

### From Basic to Enhanced Client

Replace:
```python
from client import SonotheiaClient
client = SonotheiaClient()
```

With:
```python
from client_enhanced import SonotheiaClientEnhanced
with SonotheiaClientEnhanced(
    max_retries=3,
    rate_limit_rps=2.0,
) as client:
    # Use client...
```

### Adding Health Checks

Add to your startup script:
```bash
# Verify API connectivity before starting
python health_check.py || exit 1

# Start application
python main.py
```

### Containerizing Existing Code

1. Copy `Dockerfile` to your directory
2. Update `CMD` with your script name
3. Build and test locally
4. Deploy to production

## Additional Resources

- [Kubernetes README](../kubernetes/README.md) - Detailed K8s guide
- [Python README](../python/README.md) - Python client documentation
- [Node README](../node/README.md) - Node.js examples
- [Best Practices](../../docs/BEST_PRACTICES.md) - General integration guide
- [FAQ](../../docs/FAQ.md) - Common questions

## Support

For issues with enhanced examples:
1. Check logs for error details
2. Verify configuration (API keys, URLs)
3. Test with basic examples first
4. Review health check output
5. Check Prometheus metrics
6. Consult troubleshooting section

For API-specific issues:
- Contact your Sonotheia integration engineer
- Review API documentation
- Check status page
