/**
 * Golden Path Demo - Complete Sonotheia Workflow
 *
 * Demonstrates the complete end-to-end workflow:
 * 1. Deepfake detection
 * 2. Voice MFA verification (optional)
 * 3. Routing decision based on results
 * 4. Optional SAR submission
 */

import axios, { AxiosError } from 'axios';
import { Command } from 'commander';
import FormData from 'form-data';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { basename, dirname, extname, resolve } from 'path';
// Simple UUID-like generator (no external dependency)
function generateSessionId(): string {
  return 'session-' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

import { SonotheiaClient } from './index';

// Re-export types for convenience
export type DeepfakeResponse = {
  score: number;
  label: string;
  latency_ms: number;
  session_id?: string;
  recommended_action?: string;
};

export type MfaResponse = {
  verified: boolean;
  enrollment_id: string;
  confidence: number;
  session_id?: string;
};

export type SarResponse = {
  status: string;
  case_id: string;
  session_id: string;
};

// Types for Golden Path output contract
export interface GoldenPathInputs {
  audio_filename: string;
  audio_seconds: number;
  samplerate_hz: number;
}

export interface GoldenPathResults {
  deepfake: DeepfakeResponse | null;
  mfa: MfaResponse | null;
  sar: SarResponse | null;
}

export interface GoldenPathDecision {
  route: 'ALLOW' | 'REQUIRE_STEP_UP' | 'REQUIRE_CALLBACK' | 'ESCALATE_TO_HUMAN' | 'BLOCK';
  reasons: string[];
  explainability: {
    human_summary: string;
  };
}

export interface GoldenPathDiagnostics {
  request_id?: string;
  retries: number;
}

export interface GoldenPathOutput {
  session_id: string;
  timestamp: string;
  inputs: GoldenPathInputs;
  results: GoldenPathResults;
  decision: GoldenPathDecision;
  diagnostics: GoldenPathDiagnostics;
}

/**
 * Get audio file information (duration, sample rate).
 *
 * Note: This is a simplified version that returns defaults.
 * For production, use a proper audio library like:
 * - `node-ffmpeg` or `fluent-ffmpeg` (requires ffmpeg binary)
 * - `music-metadata` (pure JavaScript, no binary dependencies)
 * - `wavefile` (for WAV files only)
 *
 * Example with music-metadata:
 * ```typescript
 * import { parseFile } from 'music-metadata';
 * const metadata = await parseFile(audioPath);
 * return {
 *   audio_seconds: metadata.format.duration || 0.0,
 *   samplerate_hz: metadata.format.sampleRate || 16000,
 * };
 * ```
 */
async function getAudioInfo(audioPath: string): Promise<{ audio_seconds: number; samplerate_hz: number }> {
  // Return defaults for now - actual implementation would require additional dependencies
  // The golden path demo works correctly even with default values
  return {
    audio_seconds: 0.0,
    samplerate_hz: 16000,
  };
}

/**
 * Make routing decision based on deepfake and MFA results.
 */
export function makeRoutingDecision(
  deepfakeResult: DeepfakeResponse,
  mfaResult: MfaResponse | null = null,
  sarPolicy: 'auto' | 'never' | 'always' = 'auto'
): GoldenPathDecision & { shouldSubmitSar: boolean } {
  const reasons: string[] = [];
  let route: GoldenPathDecision['route'] = 'ALLOW';
  const humanSummaryParts: string[] = [];

  // Check deepfake results
  const deepfakeScore = deepfakeResult.score || 0.5;
  const recommendedAction = (deepfakeResult as any).recommended_action || '';
  const label = deepfakeResult.label || 'uncertain';

  // High deepfake score or defer recommendation
  if (recommendedAction === 'defer_to_review' || deepfakeScore > 0.7) {
    route = 'ESCALATE_TO_HUMAN';
    reasons.push('deepfake_defer');
    humanSummaryParts.push(`Deepfake score ${deepfakeScore.toFixed(2)} indicates potential synthetic audio`);
  } else if (deepfakeScore > 0.5) {
    route = 'REQUIRE_STEP_UP';
    reasons.push('elevated_risk');
    humanSummaryParts.push(`Elevated risk detected (score: ${deepfakeScore.toFixed(2)})`);
  }

  // Check MFA results
  if (mfaResult) {
    const verified = mfaResult.verified || false;
    const confidence = mfaResult.confidence || 0.0;

    if (!verified) {
      if (route === 'ALLOW') {
        route = 'REQUIRE_STEP_UP';
      } else if (route === 'REQUIRE_STEP_UP') {
        route = 'REQUIRE_CALLBACK';
      } else {
        route = 'ESCALATE_TO_HUMAN';
      }
      reasons.push('mfa_verification_failed');
      humanSummaryParts.push('Voice MFA verification failed');
    } else if (confidence < 0.7) {
      if (route === 'ALLOW') {
        route = 'REQUIRE_STEP_UP';
      }
      reasons.push('low_mfa_confidence');
      humanSummaryParts.push(`Low MFA confidence (${confidence.toFixed(2)})`);
    }
  }

  // Determine SAR submission
  let shouldSubmitSar = false;
  if (sarPolicy === 'always') {
    shouldSubmitSar = true;
  } else if (sarPolicy === 'never') {
    shouldSubmitSar = false;
  } else if (sarPolicy === 'auto') {
    // Submit SAR if escalating or blocking
    const routeValue: string = route;
    shouldSubmitSar = (routeValue === 'ESCALATE_TO_HUMAN' || routeValue === 'BLOCK' || deepfakeScore > 0.8);
  }

  if (shouldSubmitSar) {
    reasons.push('sar_required');
  }

  // Build human summary
  const humanSummary = humanSummaryParts.length > 0
    ? humanSummaryParts.join(' ') + '.'
    : 'Low risk detected; standard processing allowed.';

  return {
    route,
    reasons,
    explainability: {
      human_summary: humanSummary,
    },
    shouldSubmitSar,
  };
}

/**
 * Run the complete golden path workflow.
 */
export async function runGoldenPath(
  audioPath: string,
  options: {
    enrollmentId?: string;
    sessionId?: string;
    sarPolicy?: 'auto' | 'never' | 'always';
    mockMode?: boolean;
    apiUrl?: string;
    apiKey?: string;
  } = {}
): Promise<GoldenPathOutput> {
  const {
    enrollmentId,
    sessionId,
    sarPolicy = 'auto',
    mockMode = false,
    apiUrl,
    apiKey,
  } = options;

  // Generate session ID if not provided
  const finalSessionId = sessionId || generateSessionId();

  // Get audio info
  const audioInfo = await getAudioInfo(audioPath);
  console.log(
    `Audio file: ${basename(audioPath)}, ` +
    `duration: ${audioInfo.audio_seconds.toFixed(2)}s, ` +
    `sample rate: ${audioInfo.samplerate_hz}Hz`
  );

  // Initialize client
  const clientApiKey = apiKey || process.env.SONOTHEIA_API_KEY;
  if (!clientApiKey && !mockMode) {
    throw new Error('API key required. Set SONOTHEIA_API_KEY environment variable or pass apiKey option.');
  }

  const clientApiUrl = mockMode
    ? (apiUrl || process.env.SONOTHEIA_API_URL || 'http://localhost:8000')
    : (apiUrl || process.env.SONOTHEIA_API_URL || 'https://api.sonotheia.com');

  if (mockMode) {
    console.log(`Using mock API server at ${clientApiUrl}`);
  }

  const client = new SonotheiaClient({
    apiKey: clientApiKey || 'mock_api_key_12345',
    apiUrl: clientApiUrl,
  });

  const results: GoldenPathResults = {
    deepfake: null,
    mfa: null,
    sar: null,
  };
  const diagnostics: GoldenPathDiagnostics = { retries: 0 };

  // Step 1: Deepfake detection
  console.log('Running deepfake detection...');
  try {
    const startTime = Date.now();
    const deepfakeResult = await client.detectDeepfake({
      audioPath,
      metadata: { session_id: finalSessionId, channel: 'web' },
    });
    const latencyMs = Date.now() - startTime;

    // Add latency if not present
    if (!deepfakeResult.latency_ms) {
      (deepfakeResult as any).latency_ms = latencyMs;
    }

    // Add recommended_action if not present (for mock mode compatibility)
    if (!(deepfakeResult as any).recommended_action) {
      const score = deepfakeResult.score || 0.5;
      if (score > 0.7) {
        (deepfakeResult as any).recommended_action = 'defer_to_review';
      } else if (score > 0.5) {
        (deepfakeResult as any).recommended_action = 'review';
      } else {
        (deepfakeResult as any).recommended_action = 'allow';
      }
    }

    results.deepfake = deepfakeResult;
    console.log(
      `Deepfake detection: score=${(deepfakeResult.score || 0).toFixed(3)}, ` +
      `label=${deepfakeResult.label || 'unknown'}`
    );
  } catch (error) {
    console.error(`Deepfake detection failed: ${error}`);
    throw error;
  }

  // Step 2: MFA verification (if enrollment ID provided)
  if (enrollmentId && results.deepfake) {
    console.log(`Running MFA verification for enrollment: ${enrollmentId}`);
    try {
      const startTime = Date.now();
      const mfaResult = await client.verifyMfa({
        audioPath,
        enrollmentId,
        context: { session_id: finalSessionId, channel: 'ivr' },
      });
      const latencyMs = Date.now() - startTime;

      // Add latency if not present
      if (!(mfaResult as any).latency_ms) {
        (mfaResult as any).latency_ms = latencyMs;
      }

      results.mfa = mfaResult;
      console.log(
        `MFA verification: verified=${mfaResult.verified || false}, ` +
        `confidence=${(mfaResult.confidence || 0).toFixed(3)}`
      );
    } catch (error) {
      console.warn(`MFA verification failed: ${error}`);
      // Continue without MFA result
      results.mfa = null;
    }
  }

  // Step 3: Make routing decision
  console.log('Making routing decision...');
  if (!results.deepfake) {
    throw new Error('Deepfake detection result is required for routing decision');
  }

  const decision = makeRoutingDecision(results.deepfake, results.mfa, sarPolicy);
  console.log(`Routing decision: ${decision.route}`);

  // Step 4: SAR submission (if policy allows)
  if (decision.shouldSubmitSar && finalSessionId) {
    console.log('Submitting SAR...');
    try {
      const sarResult = await client.submitSar({
        sessionId: finalSessionId,
        decision: decision.route === 'ESCALATE_TO_HUMAN' ? 'review' : 'deny',
        reason: decision.explainability.human_summary,
        metadata: { source: 'golden_path_demo', route: decision.route },
      });
      results.sar = sarResult;
      console.log(`SAR submitted: case_id=${sarResult.case_id || 'unknown'}`);
    } catch (error) {
      console.warn(`SAR submission failed: ${error}`);
      results.sar = null;
    }
  }

  // Remove shouldSubmitSar from decision (internal only)
  const { shouldSubmitSar, ...finalDecision } = decision;

  // Build final output
  const output: GoldenPathOutput = {
    session_id: finalSessionId,
    timestamp: new Date().toISOString(),
    inputs: {
      audio_filename: basename(audioPath),
      ...audioInfo,
    },
    results,
    decision: finalDecision,
    diagnostics,
  };

  return output;
}

/**
 * CLI entry point for Golden Path demo.
 */
export async function goldenPathMain(): Promise<void> {
  const program = new Command();
  program
    .name('golden-path')
    .description('Golden Path Demo - Complete Sonotheia Workflow')
    .argument('<audio>', 'Path to audio file (wav/opus/mp3/flac)')
    .option('--enrollment-id <id>', 'Enrollment ID for MFA verification (for mock mode, any string works)')
    .option('--session-id <id>', 'Session identifier (auto-generated if not provided)')
    .option('--sar <mode>', 'SAR submission policy: auto, never, always', 'auto')
    .option('--mock', 'Use mock API server instead of real API (no API key required)')
    .option('--api-url <url>', 'Override API URL')
    .option('--output <file>', 'Write JSON output to file')
    .option('--pretty', 'Pretty-print JSON output')
    .option('--verbose', 'Enable verbose logging');

  program.parse(process.argv);

  const options = program.opts<{
    enrollmentId?: string;
    sessionId?: string;
    sar?: 'auto' | 'never' | 'always';
    mock?: boolean;
    apiUrl?: string;
    output?: string;
    pretty?: boolean;
    verbose?: boolean;
  }>();

  const [audioArg] = program.args;
  if (!audioArg) {
    console.error('Error: Audio file path is required');
    program.help();
    process.exit(1);
  }

  // Validate audio file
  const audioPath = resolve(audioArg);
  if (!existsSync(audioPath)) {
    console.error(`Error: Audio file not found: ${audioPath}`);
    process.exit(1);
  }

  const allowedExtensions = new Set(['.wav', '.opus', '.mp3', '.flac']);
  const extension = extname(audioPath).toLowerCase();
  if (!allowedExtensions.has(extension)) {
    const allowed = Array.from(allowedExtensions).sort().join(', ');
    console.error(`Error: Unsupported audio extension '${extension}'. Supported formats: ${allowed}`);
    process.exit(1);
  }

  // Run golden path
  try {
    const result = await runGoldenPath(audioPath, {
      enrollmentId: options.enrollmentId,
      sessionId: options.sessionId,
      sarPolicy: options.sar || 'auto',
      mockMode: options.mock || false,
      apiUrl: options.apiUrl,
    });

    // Output result
    const outputJson = JSON.stringify(result, null, options.pretty ? 2 : undefined);

    if (options.output) {
      const outputPath = resolve(options.output);
      mkdirSync(dirname(outputPath), { recursive: true });
      writeFileSync(outputPath, outputJson, 'utf-8');
      console.error(`Results written to ${outputPath}`);
    } else {
      console.log(outputJson);
    }
  } catch (error) {
    // Return error in JSON format
    const errorOutput = {
      error: {
        message: error instanceof Error ? error.message : String(error),
        type: error instanceof Error ? error.constructor.name : 'UnknownError',
      },
      timestamp: new Date().toISOString(),
    };

    const errorJson = JSON.stringify(errorOutput, null, options.pretty ? 2 : undefined);
    if (options.output) {
      const outputPath = resolve(options.output);
      mkdirSync(dirname(outputPath), { recursive: true });
      writeFileSync(outputPath, errorJson, 'utf-8');
    } else {
      console.error(errorJson);
    }
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  goldenPathMain().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}
