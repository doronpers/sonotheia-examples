/**
 * Batch processor for analyzing multiple audio files
 * 
 * Usage:
 *   SONOTHEIA_API_KEY=xxx node batch-processor.js /path/to/audio/files/*.wav
 */

import axios from 'axios';
import FormData from 'form-data';
import { readFileSync, readdirSync } from 'fs';
import { basename } from 'path';
import pino from 'pino';

const logger = pino({ level: process.env.LOG_LEVEL || 'info' });

const API_KEY = process.env.SONOTHEIA_API_KEY;
const API_URL = (process.env.SONOTHEIA_API_URL || 'https://api.sonotheia.com').replace(/\/$/, '');
const DEEPFAKE_PATH = process.env.SONOTHEIA_DEEPFAKE_PATH || '/v1/voice/deepfake';
const CONCURRENT_REQUESTS = parseInt(process.env.CONCURRENT_REQUESTS || '5', 10);

if (!API_KEY) {
  logger.error('SONOTHEIA_API_KEY environment variable is required');
  process.exit(1);
}

/**
 * Process a single audio file
 */
async function processFile(audioPath) {
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

    logger.info({
      file: basename(audioPath),
      score: response.data.score,
      label: response.data.label,
      duration_ms: duration,
    }, 'File processed successfully');

    return {
      file: audioPath,
      success: true,
      result: response.data,
      duration_ms: duration,
    };
  } catch (error) {
    logger.error({
      file: basename(audioPath),
      error: error.response?.data || error.message,
    }, 'Failed to process file');

    return {
      file: audioPath,
      success: false,
      error: error.response?.data || error.message,
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
    // Start new requests up to concurrency limit
    while (inProgress.size < CONCURRENT_REQUESTS && pending.length > 0) {
      const file = pending.shift();
      const promise = processFile(file)
        .then(result => {
          inProgress.delete(promise);
          return result;
        });
      inProgress.add(promise);
      results.push(promise);
    }

    // Wait for at least one request to complete
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
  const total = results.length;
  const successful = results.filter(r => r.success).length;
  const failed = total - successful;
  
  const scores = results
    .filter(r => r.success && r.result?.score !== undefined)
    .map(r => r.result.score);
  
  const avgScore = scores.length > 0
    ? scores.reduce((a, b) => a + b, 0) / scores.length
    : 0;
  
  const highRisk = results.filter(r => r.success && r.result?.score > 0.7).length;
  const mediumRisk = results.filter(r => r.success && r.result?.score > 0.4 && r.result?.score <= 0.7).length;
  const lowRisk = results.filter(r => r.success && r.result?.score <= 0.4).length;

  return {
    total,
    successful,
    failed,
    avgScore: avgScore.toFixed(3),
    riskDistribution: {
      high: highRisk,
      medium: mediumRisk,
      low: lowRisk,
    },
  };
}

/**
 * Main execution
 */
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.error('Usage: node batch-processor.js <audio-file1.wav> [audio-file2.wav] ...');
    console.error('   or: node batch-processor.js /path/to/directory/');
    process.exit(1);
  }

  let files = [];
  
  // Collect all audio files
  for (const arg of args) {
    try {
      const stat = await import('fs').then(m => m.promises.stat(arg));
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

  logger.info({ fileCount: files.length, concurrency: CONCURRENT_REQUESTS }, 'Starting batch processing');

  const startTime = Date.now();
  const results = await processBatch(files);
  const totalDuration = Date.now() - startTime;

  const summary = generateSummary(results);
  
  logger.info({
    ...summary,
    totalDuration_ms: totalDuration,
    avgDuration_ms: Math.round(totalDuration / results.length),
  }, 'Batch processing completed');

  // Print detailed results
  console.log('\n=== BATCH PROCESSING RESULTS ===\n');
  console.log(`Total files:     ${summary.total}`);
  console.log(`Successful:      ${summary.successful}`);
  console.log(`Failed:          ${summary.failed}`);
  console.log(`Average score:   ${summary.avgScore}`);
  console.log(`\nRisk distribution:`);
  console.log(`  High (>0.7):   ${summary.riskDistribution.high}`);
  console.log(`  Medium (0.4-0.7): ${summary.riskDistribution.medium}`);
  console.log(`  Low (<0.4):    ${summary.riskDistribution.low}`);
  console.log(`\nTotal duration:  ${(totalDuration / 1000).toFixed(2)}s`);
  console.log(`Avg per file:    ${(totalDuration / results.length).toFixed(0)}ms`);

  // Exit with error if any failures
  process.exit(summary.failed > 0 ? 1 : 0);
}

main().catch(error => {
  logger.error({ error: error.message }, 'Batch processing failed');
  process.exit(1);
});
