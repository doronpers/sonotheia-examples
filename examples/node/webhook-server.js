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
const processedEvents = new Set(); // Track processed event IDs for idempotency
const RESULT_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours
const MAX_RESULTS = 10000; // Maximum results to store
const MAX_EVENT_ID_CACHE = 50000; // Maximum event IDs to track

// Rate limiting configuration
const RATE_LIMIT_WINDOW_MS = 60 * 1000; // 1 minute window
const RATE_LIMIT_MAX_REQUESTS = 100; // Max requests per window
const rateLimitStore = new Map(); // IP -> { count, resetTime }

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

  // Cleanup processed event IDs if cache is too large
  if (processedEvents.size > MAX_EVENT_ID_CACHE) {
    // Clear oldest 25% of event IDs (simple FIFO approximation)
    const toDelete = Math.floor(MAX_EVENT_ID_CACHE * 0.25);
    const eventIds = Array.from(processedEvents).slice(0, toDelete);
    eventIds.forEach(id => processedEvents.delete(id));
    logger.info({ deleted: toDelete }, 'Cleaned up processed event IDs');
  }
}, 60 * 60 * 1000); // Run every hour

// Request size limit (10MB default, adjust based on your needs)
const MAX_REQUEST_SIZE = process.env.MAX_REQUEST_SIZE || '10mb';

// Middleware to parse JSON with raw body for signature verification
app.use(express.json({
  limit: MAX_REQUEST_SIZE,
  verify: (req, res, buf) => {
    req.rawBody = buf.toString('utf8');
  }
}));

/**
 * Simple rate limiting middleware
 * In production, use express-rate-limit or similar library
 */
function rateLimitMiddleware(req, res, next) {
  const clientIp = req.ip || req.connection.remoteAddress || 'unknown';
  const now = Date.now();

  // Get or create rate limit entry
  let limitEntry = rateLimitStore.get(clientIp);

  // Reset if window expired
  if (!limitEntry || now > limitEntry.resetTime) {
    limitEntry = {
      count: 0,
      resetTime: now + RATE_LIMIT_WINDOW_MS,
    };
    rateLimitStore.set(clientIp, limitEntry);
  }

  // Check limit
  if (limitEntry.count >= RATE_LIMIT_MAX_REQUESTS) {
    logger.warn({ clientIp, count: limitEntry.count }, 'Rate limit exceeded');
    return res.status(429).json({
      error: 'Rate limit exceeded',
      message: `Maximum ${RATE_LIMIT_MAX_REQUESTS} requests per minute`,
      retryAfter: Math.ceil((limitEntry.resetTime - now) / 1000),
    });
  }

  // Increment counter
  limitEntry.count++;
  next();
}

// Cleanup rate limit store periodically
setInterval(() => {
  const now = Date.now();
  for (const [ip, entry] of rateLimitStore.entries()) {
    if (now > entry.resetTime) {
      rateLimitStore.delete(ip);
    }
  }
}, 5 * 60 * 1000); // Every 5 minutes

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
 * - Rate limiting (implemented below, but consider express-rate-limit for production)
 * - Request size limits (configured via MAX_REQUEST_SIZE env var)
 * - Authentication/authorization
 * - IP whitelisting if possible
 * - HTTPS only
 */
app.post('/webhook', rateLimitMiddleware, (req, res) => {
  const signature = req.headers['x-sonotheia-signature'];

  // Verify signature if secret is configured
  if (WEBHOOK_SECRET) {
    if (!signature || !verifySignature(req.rawBody, signature, WEBHOOK_SECRET)) {
      logger.warn('Invalid webhook signature');
      return res.status(401).json({ error: 'Invalid signature' });
    }
  }

  const event = req.body;

  // Idempotency check: ignore duplicate events
  const eventId = event.id || event.event_id || `${event.type}-${event.data?.session_id || 'unknown'}`;
  if (processedEvents.has(eventId)) {
    logger.info({ event_id: eventId, event_type: event.type }, 'Duplicate event ignored (idempotency)');
    return res.json({ received: true, duplicate: true });
  }

  logger.debug({ event_type: event.type, event_id: eventId }, 'Webhook received');

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

    // Mark event as processed
    processedEvents.add(eventId);

    res.json({ received: true, event_id: eventId });
  } catch (error) {
    logger.error({ error: error.message, event_id: eventId }, 'Error processing webhook');
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
  console.log(`\nConfiguration:`);
  console.log(`  Rate limit:           ${RATE_LIMIT_MAX_REQUESTS} requests per minute`);
  console.log(`  Max request size:     ${MAX_REQUEST_SIZE}`);
  console.log(`  Idempotency:          Enabled (tracks ${MAX_EVENT_ID_CACHE} event IDs)`);

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
