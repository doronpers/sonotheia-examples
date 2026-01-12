/**
 * TypeScript client for Sonotheia voice fraud detection API
 * 
 * Provides type-safe methods for:
 * - Deepfake detection
 * - Voice MFA verification
 * - SAR (Suspicious Activity Report) submission
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import FormData from 'form-data';
import { readFileSync } from 'fs';
import { basename } from 'path';

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
    const ext = request.audioPath.toLowerCase();
    let contentType = 'application/octet-stream';
    if (ext.endsWith('.wav')) contentType = 'audio/wav';
    else if (ext.endsWith('.mp3')) contentType = 'audio/mpeg';
    else if (ext.endsWith('.opus')) contentType = 'audio/opus';
    else if (ext.endsWith('.flac')) contentType = 'audio/flac';

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
    const ext = request.audioPath.toLowerCase();
    let contentType = 'application/octet-stream';
    if (ext.endsWith('.wav')) contentType = 'audio/wav';
    else if (ext.endsWith('.mp3')) contentType = 'audio/mpeg';
    else if (ext.endsWith('.opus')) contentType = 'audio/opus';
    else if (ext.endsWith('.flac')) contentType = 'audio/flac';

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

/**
 * Example usage
 */
export async function main() {
  const apiKey = process.env.SONOTHEIA_API_KEY;
  if (!apiKey) {
    console.error('Error: SONOTHEIA_API_KEY environment variable must be set');
    process.exit(1);
  }

  const audioPath = process.argv[2];
  if (!audioPath) {
    console.error('Usage: node dist/index.js <audio-file.wav> [--enrollment-id <id>] [--session-id <id>]');
    process.exit(1);
  }

  const args = process.argv.slice(3);
  const enrollmentIdIndex = args.indexOf('--enrollment-id');
  const enrollmentId = enrollmentIdIndex !== -1 ? args[enrollmentIdIndex + 1] : undefined;
  const sessionIdIndex = args.indexOf('--session-id');
  const sessionId = sessionIdIndex !== -1 ? args[sessionIdIndex + 1] : 'demo-session';

  const client = new SonotheiaClient({ apiKey });
  const results: Record<string, any> = {};

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

    // SAR submission (if session ID provided and deepfake score is high)
    if (sessionId && results.deepfake?.score > 0.7) {
      console.log('\nSubmitting SAR for suspicious activity...');
      results.sar = await client.submitSar({
        sessionId,
        decision: 'review',
        reason: 'High deepfake score detected',
        metadata: { source: 'typescript-example', deepfake_score: results.deepfake.score },
      });
      console.log('SAR result:', results.sar);
    }

    console.log('\nAll results:');
    console.log(JSON.stringify(results, null, 2));
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
