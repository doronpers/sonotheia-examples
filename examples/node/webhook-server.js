/**
 * Example webhook server for receiving Sonotheia API callbacks
 *
 * This demonstrates how to:
 * - Receive asynchronous processing results
 * - Verify webhook signatures
 * - Handle different event types
 * - Store results for later retrieval
 *
 * Usage:
 *   PORT=3000 node webhook-server.js
 */

import express from 'express';
import crypto from 'crypto';
import pino from 'pino';

const logger = pino({ level: process.env.LOG_LEVEL || 'info' });

const app = express();
const PORT = process.env.PORT || 3000;
const WEBHOOK_SECRET = process.env.SONOTHEIA_WEBHOOK_SECRET;

// In-memory store with TTL cleanup (use a database in production)
const results = new Map();
const RESULT_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours
const MAX_RESULTS = 10000; // Maximum results to store

// Cleanup old results periodically
setInterval(() => {
  const now = Date.now();
  let deleted = 0;
  for (const [key, value] of results.entries()) {
    const age = now - new Date(value.received_at).getTime();
    if (age > RESULT_TTL_MS) {
      results.delete(key);
      deleted++;
    }
  }
  if (deleted > 0) {
    logger.info({ deleted, remaining: results.size }, 'Cleaned up old results');
  }

  // Also enforce max size limit
  if (results.size > MAX_RESULTS) {
    const toDelete = results.size - MAX_RESULTS;
    const keys = Array.from(results.keys()).slice(0, toDelete);
    keys.forEach(key => results.delete(key));
    logger.warn({ deleted: toDelete }, 'Enforced max results limit');
  }
}, 60 * 60 * 1000); // Run every hour

// Middleware to parse JSON with raw body for signature verification
app.use(express.json({
  verify: (req, res, buf) => {
    req.rawBody = buf.toString('utf8');
  }
}));

/**
 * Verify webhook signature
 */
function verifySignature(payload, signature, secret) {
  if (!secret) {
    logger.error('WEBHOOK_SECRET not set - webhook verification required');
    return false;
  }

  // Validate signature format (64 hex characters for SHA-256)
  if (!signature || typeof signature !== 'string' || !/^[a-f0-9]{64}$/i.test(signature)) {
    logger.warn({ signature }, 'Invalid signature format - expected 64 hex characters');
    return false;
  }

  try {
    const expectedSignature = crypto
      .createHmac('sha256', secret)
      .update(payload)
      .digest('hex');

    return crypto.timingSafeEqual(
      Buffer.from(signature, 'hex'),
      Buffer.from(expectedSignature, 'hex')
    );
  } catch (error) {
    logger.error({ error: error.message }, 'Error verifying signature');
    return false;
  }
}

/**
 * Handle deepfake detection webhook
 */
function handleDeepfakeEvent(event) {
  const { session_id, score, label, timestamp } = event.data;

  logger.info({
    event: 'deepfake.completed',
    session_id,
    score,
    label,
  }, 'Deepfake detection completed');

  // Store result
  results.set(session_id, {
    type: 'deepfake',
    score,
    label,
    timestamp,
    received_at: new Date().toISOString(),
  });

  // Take action based on score
  if (score > 0.8) {
    logger.warn({ session_id, score }, 'High deepfake score detected - review required');
    // Here you could trigger alerts, create tickets, etc.
  }
}

/**
 * Handle MFA verification webhook
 */
function handleMfaEvent(event) {
  const { session_id, enrollment_id, verified, confidence } = event.data;

  logger.info({
    event: 'mfa.completed',
    session_id,
    enrollment_id,
    verified,
    confidence,
  }, 'MFA verification completed');

  // Store result
  results.set(session_id, {
    type: 'mfa',
    enrollment_id,
    verified,
    confidence,
    received_at: new Date().toISOString(),
  });

  if (!verified) {
    logger.warn({ session_id, enrollment_id }, 'MFA verification failed');
    // Handle failed verification
  }
}

/**
 * Handle SAR submission webhook
 */
function handleSarEvent(event) {
  const { session_id, case_id, status } = event.data;

  logger.info({
    event: 'sar.submitted',
    session_id,
    case_id,
    status,
  }, 'SAR submitted');

  // Store result
  results.set(session_id, {
    type: 'sar',
    case_id,
    status,
    received_at: new Date().toISOString(),
  });
}

/**
 * Main webhook endpoint
 *
 * SECURITY NOTE: In production, this endpoint should be protected with:
 * - Rate limiting (e.g., express-rate-limit middleware)
 * - Request size limits
 * - Authentication/authorization
 * - IP whitelisting if possible
 */
app.post('/webhook', (req, res) => {
  const signature = req.headers['x-sonotheia-signature'];

  // Verify signature if secret is configured
  if (WEBHOOK_SECRET) {
    if (!signature || !verifySignature(req.rawBody, signature, WEBHOOK_SECRET)) {
      logger.warn('Invalid webhook signature');
      return res.status(401).json({ error: 'Invalid signature' });
    }
  }

  const event = req.body;

  logger.debug({ event_type: event.type }, 'Webhook received');

  try {
    // Route to appropriate handler
    switch (event.type) {
      case 'deepfake.completed':
        handleDeepfakeEvent(event);
        break;

      case 'mfa.completed':
        handleMfaEvent(event);
        break;

      case 'sar.submitted':
        handleSarEvent(event);
        break;

      default:
        logger.warn({ event_type: event.type }, 'Unknown event type');
    }

    res.json({ received: true });
  } catch (error) {
    logger.error({ error: error.message }, 'Error processing webhook');
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    results_count: results.size,
  });
});

/**
 * Retrieve results endpoint
 */
app.get('/results/:session_id', (req, res) => {
  const { session_id } = req.params;
  const result = results.get(session_id);

  if (!result) {
    return res.status(404).json({ error: 'Session not found' });
  }

  res.json(result);
});

/**
 * List all results endpoint
 */
app.get('/results', (req, res) => {
  const allResults = Array.from(results.entries()).map(([session_id, data]) => ({
    session_id,
    ...data,
  }));

  res.json({
    count: allResults.length,
    results: allResults,
  });
});

/**
 * Start server
 */
app.listen(PORT, () => {
  logger.info({ port: PORT }, 'Webhook server started');
  console.log(`\nWebhook server listening on port ${PORT}`);
  console.log(`POST webhook events to: http://localhost:${PORT}/webhook`);
  console.log(`Health check:           http://localhost:${PORT}/health`);
  console.log(`View results:           http://localhost:${PORT}/results`);

  if (!WEBHOOK_SECRET) {
    console.warn('\nWARNING: SONOTHEIA_WEBHOOK_SECRET not set - signature verification disabled');
  }
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});
