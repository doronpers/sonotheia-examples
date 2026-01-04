/**
 * Enhanced batch processor with monitoring and observability
 * 
 * Features:
 * - Prometheus metrics export
 * - Structured logging
 * - Health checks
 * - Circuit breaker pattern
 * - Retry logic with exponential backoff
 * 
 * Usage:
 *   SONOTHEIA_API_KEY=xxx node batch-processor-enhanced.js /path/to/audio/*.wav
 *   
 * Monitoring:
 *   curl http://localhost:9090/metrics
 */

import axios from 'axios';
import FormData from 'form-data';
import { readFileSync, readdirSync, promises as fsPromises } from 'fs';
import { basename } from 'path';
import pino from 'pino';
import http from 'http';

const logger = pino({ level: process.env.LOG_LEVEL || 'info' });

const API_KEY = process.env.SONOTHEIA_API_KEY;
const API_URL = (process.env.SONOTHEIA_API_URL || 'https://api.sonotheia.com').replace(/\/$/, '');
const DEEPFAKE_PATH = process.env.SONOTHEIA_DEEPFAKE_PATH || '/v1/voice/deepfake';
const CONCURRENT_REQUESTS = parseInt(process.env.CONCURRENT_REQUESTS || '5', 10);
const MAX_RETRIES = parseInt(process.env.MAX_RETRIES || '3', 10);
const METRICS_PORT = parseInt(process.env.METRICS_PORT || '9090', 10);

if (!API_KEY) {
  logger.error('SONOTHEIA_API_KEY environment variable is required');
  process.exit(1);
}

// Metrics collection
const metrics = {
  filesProcessed: 0,
  filesSucceeded: 0,
  filesFailed: 0,
  totalLatencyMs: 0,
  highRiskCount: 0,
  mediumRiskCount: 0,
  lowRiskCount: 0,
  retryCount: 0,
  circuitBreakerTrips: 0,
};

// Circuit breaker state
const circuitBreaker = {
  state: 'CLOSED', // CLOSED, OPEN, HALF_OPEN
  failureCount: 0,
  failureThreshold: 5,
  lastFailureTime: null,
  recoveryTimeout: 60000, // 1 minute
  successCount: 0,
  successThreshold: 2,
};

/**
 * Check circuit breaker state
 */
function checkCircuitBreaker() {
  if (circuitBreaker.state === 'OPEN') {
    const now = Date.now();
    if (now - circuitBreaker.lastFailureTime > circuitBreaker.recoveryTimeout) {
      logger.info('Circuit breaker entering HALF_OPEN state');
      circuitBreaker.state = 'HALF_OPEN';
      circuitBreaker.successCount = 0;
      return true;
    }
    return false;
  }
  return true;
}

/**
 * Handle circuit breaker success
 */
function onCircuitBreakerSuccess() {
  if (circuitBreaker.state === 'HALF_OPEN') {
    circuitBreaker.successCount++;
    if (circuitBreaker.successCount >= circuitBreaker.successThreshold) {
      logger.info('Circuit breaker closing after successful recovery');
      circuitBreaker.state = 'CLOSED';
      circuitBreaker.failureCount = 0;
    }
  } else if (circuitBreaker.state === 'CLOSED') {
    circuitBreaker.failureCount = 0;
  }
}

/**
 * Handle circuit breaker failure
 */
function onCircuitBreakerFailure() {
  circuitBreaker.failureCount++;
  circuitBreaker.lastFailureTime = Date.now();

  if (circuitBreaker.state === 'HALF_OPEN') {
    logger.warn('Circuit breaker reopening due to failure during recovery');
    circuitBreaker.state = 'OPEN';
    metrics.circuitBreakerTrips++;
  } else if (circuitBreaker.failureCount >= circuitBreaker.failureThreshold) {
    logger.error(`Circuit breaker opening after ${circuitBreaker.failureCount} failures`);
    circuitBreaker.state = 'OPEN';
    metrics.circuitBreakerTrips++;
  }
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Process a single audio file with retry logic
 */
async function processFileWithRetry(audioPath, retryCount = 0) {
  // Check circuit breaker
  if (!checkCircuitBreaker()) {
    throw new Error('Circuit breaker is OPEN - service unavailable');
  }

  const form = new FormData();
  
  try {
    const audioBuffer = readFileSync(audioPath);
    form.append('audio', audioBuffer, {
      filename: basename(audioPath),
      contentType: 'audio/wav',
    });

    const metadata = {
      session_id: `batch-${Date.now()}`,
      channel: 'batch',
      filename: basename(audioPath),
      retry_count: retryCount,
    };
    form.append('metadata', JSON.stringify(metadata), {
      contentType: 'application/json',
    });

    const startTime = Date.now();
    const response = await axios.post(
      `${API_URL}${DEEPFAKE_PATH}`,
      form,
      {
        headers: {
          ...form.getHeaders(),
          'Authorization': `Bearer ${API_KEY}`,
          'Accept': 'application/json',
        },
        timeout: 30000,
      }
    );
    const duration = Date.now() - startTime;

    // Success - update circuit breaker
    onCircuitBreakerSuccess();

    // Update metrics
    metrics.filesProcessed++;
    metrics.filesSucceeded++;
    metrics.totalLatencyMs += duration;

    const score = response.data.score || 0;
    if (score > 0.7) {
      metrics.highRiskCount++;
    } else if (score > 0.4) {
      metrics.mediumRiskCount++;
    } else {
      metrics.lowRiskCount++;
    }

    logger.info({
      file: basename(audioPath),
      score: response.data.score,
      label: response.data.label,
      duration_ms: duration,
      retries: retryCount,
    }, 'File processed successfully');

    return {
      file: audioPath,
      success: true,
      result: response.data,
      duration_ms: duration,
      retries: retryCount,
    };

  } catch (error) {
    // Failure - update circuit breaker
    onCircuitBreakerFailure();

    const isRetryable = error.response?.status >= 500 || error.code === 'ECONNABORTED';
    
    if (isRetryable && retryCount < MAX_RETRIES) {
      const backoffMs = Math.min(1000 * Math.pow(2, retryCount), 30000);
      logger.warn({
        file: basename(audioPath),
        error: error.response?.data || error.message,
        retry: retryCount + 1,
        backoff_ms: backoffMs,
      }, 'Retrying after error');

      metrics.retryCount++;
      await sleep(backoffMs);
      return processFileWithRetry(audioPath, retryCount + 1);
    }

    // Final failure
    metrics.filesProcessed++;
    metrics.filesFailed++;

    logger.error({
      file: basename(audioPath),
      error: error.response?.data || error.message,
      retries: retryCount,
    }, 'Failed to process file');

    return {
      file: audioPath,
      success: false,
      error: error.response?.data || error.message,
      retries: retryCount,
    };
  }
}

/**
 * Process files in batches with concurrency control
 */
async function processBatch(files) {
  const results = [];
  const pending = [...files];
  const inProgress = new Set();

  while (pending.length > 0 || inProgress.size > 0) {
    while (inProgress.size < CONCURRENT_REQUESTS && pending.length > 0) {
      const file = pending.shift();
      const promise = processFileWithRetry(file)
        .then(result => {
          inProgress.delete(promise);
          return result;
        });
      inProgress.add(promise);
      results.push(promise);
    }

    if (inProgress.size > 0) {
      await Promise.race(Array.from(inProgress));
    }
  }

  return Promise.all(results);
}

/**
 * Generate summary statistics
 */
function generateSummary(results) {
  const successful = results.filter(r => r.success).length;
  const failed = results.length - successful;
  
  const scores = results
    .filter(r => r.success && r.result?.score !== undefined)
    .map(r => r.result.score);
  
  const avgScore = scores.length > 0
    ? scores.reduce((a, b) => a + b, 0) / scores.length
    : 0;

  return {
    total: results.length,
    successful,
    failed,
    avgScore: avgScore.toFixed(3),
    avgLatencyMs: successful > 0 ? Math.round(metrics.totalLatencyMs / successful) : 0,
    retries: metrics.retryCount,
    circuitBreakerTrips: metrics.circuitBreakerTrips,
    riskDistribution: {
      high: metrics.highRiskCount,
      medium: metrics.mediumRiskCount,
      low: metrics.lowRiskCount,
    },
  };
}

/**
 * Export metrics in Prometheus format
 */
function exportPrometheusMetrics(summary) {
  const lines = [
    '# HELP sonotheia_files_processed_total Total number of files processed',
    '# TYPE sonotheia_files_processed_total counter',
    `sonotheia_files_processed_total ${metrics.filesProcessed}`,
    '',
    '# HELP sonotheia_files_succeeded_total Total number of successfully processed files',
    '# TYPE sonotheia_files_succeeded_total counter',
    `sonotheia_files_succeeded_total ${metrics.filesSucceeded}`,
    '',
    '# HELP sonotheia_files_failed_total Total number of failed files',
    '# TYPE sonotheia_files_failed_total counter',
    `sonotheia_files_failed_total ${metrics.filesFailed}`,
    '',
    '# HELP sonotheia_avg_latency_ms Average API latency in milliseconds',
    '# TYPE sonotheia_avg_latency_ms gauge',
    `sonotheia_avg_latency_ms ${summary.avgLatencyMs}`,
    '',
    '# HELP sonotheia_avg_score Average deepfake score',
    '# TYPE sonotheia_avg_score gauge',
    `sonotheia_avg_score ${summary.avgScore}`,
    '',
    '# HELP sonotheia_high_risk_count Number of high-risk files',
    '# TYPE sonotheia_high_risk_count gauge',
    `sonotheia_high_risk_count ${metrics.highRiskCount}`,
    '',
    '# HELP sonotheia_retries_total Total number of retries',
    '# TYPE sonotheia_retries_total counter',
    `sonotheia_retries_total ${metrics.retryCount}`,
    '',
    '# HELP sonotheia_circuit_breaker_trips_total Circuit breaker trips',
    '# TYPE sonotheia_circuit_breaker_trips_total counter',
    `sonotheia_circuit_breaker_trips_total ${metrics.circuitBreakerTrips}`,
    '',
  ];
  return lines.join('\n');
}

/**
 * Start metrics HTTP server
 */
function startMetricsServer(summary) {
  const server = http.createServer((req, res) => {
    if (req.url === '/metrics') {
      res.writeHead(200, { 'Content-Type': 'text/plain; version=0.0.4' });
      res.end(exportPrometheusMetrics(summary));
    } else if (req.url === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'healthy',
        circuit_breaker: circuitBreaker.state,
        metrics: summary,
      }));
    } else {
      res.writeHead(404);
      res.end('Not found');
    }
  });

  server.listen(METRICS_PORT, () => {
    logger.info({ port: METRICS_PORT }, 'Metrics server started');
  });

  return server;
}

/**
 * Main execution
 */
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.error('Usage: node batch-processor-enhanced.js <audio-file1.wav> [audio-file2.wav] ...');
    console.error('   or: node batch-processor-enhanced.js /path/to/directory/');
    process.exit(1);
  }

  let files = [];
  
  for (const arg of args) {
    try {
      const stat = await fsPromises.stat(arg);
      if (stat.isDirectory()) {
        const dirFiles = readdirSync(arg)
          .filter(f => f.endsWith('.wav') || f.endsWith('.opus'))
          .map(f => `${arg}/${f}`);
        files.push(...dirFiles);
      } else {
        files.push(arg);
      }
    } catch (error) {
      logger.warn({ file: arg, error: error.message }, 'Skipping invalid file');
    }
  }

  if (files.length === 0) {
    logger.error('No valid audio files found');
    process.exit(1);
  }

  logger.info({
    fileCount: files.length,
    concurrency: CONCURRENT_REQUESTS,
    maxRetries: MAX_RETRIES,
  }, 'Starting enhanced batch processing');

  const startTime = Date.now();
  const results = await processBatch(files);
  const totalDuration = Date.now() - startTime;

  const summary = generateSummary(results);
  summary.totalDuration_ms = totalDuration;
  
  logger.info(summary, 'Batch processing completed');

  // Start metrics server
  const metricsServer = startMetricsServer(summary);

  // Print detailed results
  console.log('\n=== ENHANCED BATCH PROCESSING RESULTS ===\n');
  console.log(`Total files:         ${summary.total}`);
  console.log(`Successful:          ${summary.successful}`);
  console.log(`Failed:              ${summary.failed}`);
  console.log(`Average score:       ${summary.avgScore}`);
  console.log(`Average latency:     ${summary.avgLatencyMs}ms`);
  console.log(`Total retries:       ${summary.retries}`);
  console.log(`Circuit breaker trips: ${summary.circuitBreakerTrips}`);
  console.log(`\nRisk distribution:`);
  console.log(`  High (>0.7):       ${summary.riskDistribution.high}`);
  console.log(`  Medium (0.4-0.7):  ${summary.riskDistribution.medium}`);
  console.log(`  Low (<0.4):        ${summary.riskDistribution.low}`);
  console.log(`\nTotal duration:      ${(totalDuration / 1000).toFixed(2)}s`);
  console.log(`\nMetrics available at: http://localhost:${METRICS_PORT}/metrics`);
  console.log(`Health check at:      http://localhost:${METRICS_PORT}/health`);

  // Keep server running for a bit to allow metrics scraping
  await sleep(60000);
  metricsServer.close();

  // Exit with error if any failures
  process.exit(summary.failed > 0 ? 1 : 0);
}

main().catch(error => {
  logger.error({ error: error.message }, 'Batch processing failed');
  process.exit(1);
});
