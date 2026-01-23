/**
 * TypeScript client for Sonotheia voice fraud detection API
 *
 * Provides type-safe methods for:
 * - Deepfake detection
 * - Voice MFA verification
 * - SAR (Suspicious Activity Report) submission
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { Command } from 'commander';
import FormData from 'form-data';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { basename, dirname, extname, resolve } from 'path';

// Shared constants
const ALLOWED_AUDIO_EXTENSIONS = new Set(['.wav', '.opus', '.mp3', '.flac']);
const AUDIO_MIME_TYPES: Record<string, string> = {
  '.wav': 'audio/wav',
  '.opus': 'audio/opus',
  '.mp3': 'audio/mpeg',
  '.flac': 'audio/flac',
};
const DEFAULT_AUDIO_MIME_TYPE = 'application/octet-stream';

function getAudioMimeType(filePath: string): string {
  const ext = filePath.toLowerCase();
  for (const [extension, mimeType] of Object.entries(AUDIO_MIME_TYPES)) {
    if (ext.endsWith(extension)) {
      return mimeType;
    }
  }
  return DEFAULT_AUDIO_MIME_TYPE;
}

export interface SonotheiaConfig {
  apiKey: string;
  apiUrl?: string;
  deepfakePath?: string;
  mfaPath?: string;
  sarPath?: string;
}

export interface DeepfakeRequest {
  audioPath: string;
  metadata?: Record<string, any>;
}

export interface DeepfakeResponse {
  score: number;
  label: string;
  latency_ms: number;
  session_id?: string;
}

export interface MfaRequest {
  audioPath: string;
  enrollmentId: string;
  context?: Record<string, any>;
}

export interface MfaResponse {
  verified: boolean;
  enrollment_id: string;
  confidence: number;
  session_id?: string;
}

export interface SarRequest {
  sessionId: string;
  decision: 'allow' | 'deny' | 'review';
  reason: string;
  metadata?: Record<string, any>;
}

export interface SarResponse {
  status: string;
  case_id: string;
  session_id: string;
}

export class SonotheiaClient {
  private client: AxiosInstance;
  private config: Required<SonotheiaConfig>;
  private timeout: number;

  constructor(config: SonotheiaConfig) {
    if (!config.apiKey) {
      throw new Error('API key is required. Set SONOTHEIA_API_KEY environment variable.');
    }

    this.config = {
      apiKey: config.apiKey,
      apiUrl: config.apiUrl || process.env.SONOTHEIA_API_URL || 'https://api.sonotheia.com',
      deepfakePath: config.deepfakePath || process.env.SONOTHEIA_DEEPFAKE_PATH || '/v1/voice/deepfake',
      mfaPath: config.mfaPath || process.env.SONOTHEIA_MFA_PATH || '/v1/mfa/voice/verify',
      sarPath: config.sarPath || process.env.SONOTHEIA_SAR_PATH || '/v1/reports/sar',
    };

    this.timeout = 30000; // 30 seconds default

    this.client = axios.create({
      baseURL: this.config.apiUrl.replace(/\/$/, ''),
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'Accept': 'application/json',
      },
      timeout: this.timeout,
    });
  }

  /**
   * Detect if audio contains a deepfake
   */
  async detectDeepfake(request: DeepfakeRequest): Promise<DeepfakeResponse> {
    const form = new FormData();

    const audioBuffer = readFileSync(request.audioPath);
    const contentType = getAudioMimeType(request.audioPath);

    form.append('audio', audioBuffer, {
      filename: basename(request.audioPath),
      contentType,
    });

    if (request.metadata) {
      form.append('metadata', JSON.stringify(request.metadata), {
        contentType: 'application/json',
      });
    }

    const response: AxiosResponse<DeepfakeResponse> = await this.client.post(
      this.config.deepfakePath,
      form,
      {
        headers: form.getHeaders(),
      }
    );

    return response.data;
  }

  /**
   * Verify caller identity via voice MFA
   */
  async verifyMfa(request: MfaRequest): Promise<MfaResponse> {
    const form = new FormData();

    const audioBuffer = readFileSync(request.audioPath);
    const contentType = getAudioMimeType(request.audioPath);

    form.append('audio', audioBuffer, {
      filename: basename(request.audioPath),
      contentType,
    });

    form.append('enrollment_id', request.enrollmentId);

    if (request.context) {
      form.append('context', JSON.stringify(request.context), {
        contentType: 'application/json',
      });
    }

    const response: AxiosResponse<MfaResponse> = await this.client.post(
      this.config.mfaPath,
      form,
      {
        headers: form.getHeaders(),
      }
    );

    return response.data;
  }

  /**
   * Submit a Suspicious Activity Report (SAR)
   */
  async submitSar(request: SarRequest): Promise<SarResponse> {
    const payload = {
      session_id: request.sessionId,
      decision: request.decision,
      reason: request.reason,
      metadata: request.metadata || {},
    };

    const response: AxiosResponse<SarResponse> = await this.client.post(
      this.config.sarPath,
      payload
    );

    return response.data;
  }
}

function resolveAudioPath(pathArg: string): string {
  const resolved = resolve(pathArg);
  if (!existsSync(resolved)) {
    throw new Error(`Audio file not found: ${resolved}`);
  }

  const extension = extname(resolved).toLowerCase();
  if (!ALLOWED_AUDIO_EXTENSIONS.has(extension)) {
    const allowed = Array.from(ALLOWED_AUDIO_EXTENSIONS).sort().join(', ');
    throw new Error(`Unsupported audio extension '${extension}'. Supported formats: ${allowed}`);
  }

  return resolved;
}

function writeOutput(outputPath: string | undefined, payload: string): void {
  if (!outputPath) {
    console.log(payload);
    return;
  }

  const resolved = resolve(outputPath);
  mkdirSync(dirname(resolved), { recursive: true });
  writeFileSync(resolved, payload, 'utf-8');
  console.log(`Wrote results to ${resolved}`);
}

/**
 * Example usage
 */
export async function main() {
  const program = new Command();
  program
    .name('sonotheia-typescript-example')
    .description('TypeScript client for Sonotheia voice fraud detection API')
    .argument('<audio>', 'Path to audio file (wav/opus/mp3/flac)')
    .option('--enrollment-id <id>', 'Enrollment ID for MFA verification')
    .option('--session-id <id>', 'Session identifier for linking API calls')
    .option('--submit-sar', 'Submit SAR (requires --session-id)')
    .option('--decision <allow|deny|review>', 'SAR decision (requires --submit-sar)', 'review')
    .option('--reason <text>', 'SAR reason (requires --submit-sar)', 'Manual review requested')
    .option('--output <path>', 'Write JSON results to file')
    .option('--pretty', 'Pretty-print JSON output')
    .parse(process.argv);

  const options = program.opts<{
    enrollmentId?: string;
    sessionId?: string;
    submitSar?: boolean;
    decision: 'allow' | 'deny' | 'review';
    reason: string;
    output?: string;
    pretty?: boolean;
  }>();

  const apiKey = process.env.SONOTHEIA_API_KEY;
  if (!apiKey) {
    console.error('Error: SONOTHEIA_API_KEY environment variable must be set');
    process.exit(1);
  }

  const [audioArg] = program.args;
  let audioPath: string;
  try {
    audioPath = resolveAudioPath(audioArg);
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }

  const enrollmentId = options.enrollmentId;
  const sessionId = options.sessionId || 'demo-session';
  const client = new SonotheiaClient({ apiKey });
  const results: Record<string, any> = {};

  // Validate SAR submission requirements
  if (options.submitSar && !options.sessionId) {
    console.error('Error: --submit-sar requires --session-id');
    process.exit(1);
  }

  try {
    // Deepfake detection
    console.log('Running deepfake detection...');
    results.deepfake = await client.detectDeepfake({
      audioPath,
      metadata: { session_id: sessionId, channel: 'web' },
    });
    console.log('Deepfake result:', results.deepfake);

    // MFA verification (if enrollment ID provided)
    if (enrollmentId) {
      console.log('\nRunning MFA verification...');
      results.mfa = await client.verifyMfa({
        audioPath,
        enrollmentId,
        context: { session_id: sessionId, channel: 'ivr' },
      });
      console.log('MFA result:', results.mfa);
    }

    // SAR submission (only if explicitly requested)
    if (options.submitSar && options.sessionId) {
      console.log('\nSubmitting SAR...');
      results.sar = await client.submitSar({
        sessionId: options.sessionId,
        decision: options.decision,
        reason: options.reason,
        metadata: { source: 'typescript-example' },
      });
      console.log('SAR result:', results.sar);
    }

    console.log('\nAll results:');
    const payload = JSON.stringify(results, null, options.pretty ? 2 : undefined);
    writeOutput(options.output, payload);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('API Error:', error.response?.data || error.message);
    } else {
      console.error('Error:', error);
    }
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}
