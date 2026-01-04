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

// In-memory store (use a database in production)
const results = new Map();

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
    logger.warn('WEBHOOK_SECRET not set - skipping signature verification');
    return true;
  }

  // Validate signature format
  if (!signature || typeof signature !== 'string' || !/^[a-f0-9]+$/i.test(signature)) {
    logger.warn('Invalid signature format');
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
