/**
 * Unit tests for Golden Path Demo (TypeScript - compiled to JavaScript)
 *
 * Run with: npm run build && node --test tests/goldenPath.test.js
 */

const { describe, it } = require('node:test');
const assert = require('node:assert');

// Import compiled module
// Note: After building, the module exports makeRoutingDecision
const goldenPath = require('../dist/goldenPath');
const { makeRoutingDecision } = goldenPath;

describe('makeRoutingDecision', () => {
  it('should return ALLOW for low risk scenario', () => {
    const deepfakeResult = {
      score: 0.2,
      label: 'likely_real',
      latency_ms: 450,
      recommended_action: 'allow',
    };

    const decision = makeRoutingDecision(deepfakeResult);

    assert.strictEqual(decision.route, 'ALLOW');
    assert.strictEqual(decision.reasons.length, 0);
  });

  it('should return ESCALATE_TO_HUMAN for high deepfake score', () => {
    const deepfakeResult = {
      score: 0.85,
      label: 'likely_synthetic',
      latency_ms: 450,
      recommended_action: 'defer_to_review',
    };

    const decision = makeRoutingDecision(deepfakeResult);

    assert.strictEqual(decision.route, 'ESCALATE_TO_HUMAN');
    assert.ok(decision.reasons.includes('deepfake_defer'));
  });

  it('should return REQUIRE_STEP_UP for elevated risk', () => {
    const deepfakeResult = {
      score: 0.65,
      label: 'uncertain',
      latency_ms: 450,
      recommended_action: 'review',
    };

    const decision = makeRoutingDecision(deepfakeResult);

    assert.strictEqual(decision.route, 'REQUIRE_STEP_UP');
    assert.ok(decision.reasons.includes('elevated_risk'));
  });

  it('should escalate when MFA verification fails', () => {
    const deepfakeResult = {
      score: 0.3,
      label: 'likely_real',
      latency_ms: 450,
      recommended_action: 'allow',
    };
    const mfaResult = {
      verified: false,
      enrollment_id: 'enroll-123',
      confidence: 0.4,
    };

    const decision = makeRoutingDecision(deepfakeResult, mfaResult);

    assert.strictEqual(decision.route, 'REQUIRE_STEP_UP');
    assert.ok(decision.reasons.includes('mfa_verification_failed'));
  });

  it('should submit SAR when policy is auto and risk is high', () => {
    const deepfakeResult = {
      score: 0.85,
      label: 'likely_synthetic',
      latency_ms: 450,
      recommended_action: 'defer_to_review',
    };

    const decision = makeRoutingDecision(deepfakeResult, null, 'auto');

    assert.strictEqual(decision.shouldSubmitSar, true);
    assert.ok(decision.reasons.includes('sar_required'));
  });

  it('should not submit SAR when policy is never', () => {
    const deepfakeResult = {
      score: 0.85,
      label: 'likely_synthetic',
      latency_ms: 450,
      recommended_action: 'defer_to_review',
    };

    const decision = makeRoutingDecision(deepfakeResult, null, 'never');

    assert.strictEqual(decision.shouldSubmitSar, false);
  });

  it('should always submit SAR when policy is always', () => {
    const deepfakeResult = {
      score: 0.2,
      label: 'likely_real',
      latency_ms: 450,
      recommended_action: 'allow',
    };

    const decision = makeRoutingDecision(deepfakeResult, null, 'always');

    assert.strictEqual(decision.shouldSubmitSar, true);
    assert.ok(decision.reasons.includes('sar_required'));
  });
});
