# Configuration Files

This directory contains configuration files for the Audio Trust Harness framework. These files externalize parameters that were previously hardcoded, enabling users to customize the behavior without modifying source code.

## Purpose

**Research & Evaluation Focus**: These configuration files contain **example parameters** for research and testing purposes. They represent generic values suitable for exploring the framework's methodology, not production-tuned detection parameters.

Users are encouraged to:
- Customize these values for their specific domain (speech, music, etc.)
- Experiment with different perturbation strategies
- Develop and integrate their own proprietary indicators and perturbations

## Configuration Files

### `perturbations.yaml`

Defines parameters for audio perturbations used in stress testing:

- **noise**: SNR levels for additive Gaussian noise
- **codec_stub**: Lowpass filter cutoff and quantization bits (approximation only)
- **pitch_shift**: Semitone shift range
- **time_stretch**: Time stretch rates
- **opus/mp3**: Bitrates for real codec integration

**Use cases:**
- Test robustness across different noise levels
- Simulate various compression scenarios
- Explore pitch/tempo manipulation effects

### `thresholds.yaml`

Defines decision thresholds for the deferral policy:

- **deferral_policy**: Fragility, clipping, and duration thresholds
- **consistency**: Temporal consistency thresholds

**Use cases:**
- Tune sensitivity to indicator variation
- Adjust quality gating for specific content types
- Balance false positive/negative rates for your domain

### `indicators.yaml`

Defines parameters for acoustic indicator computation:

- **stft**: FFT window size, overlap, and window function
- **spectral**: Rolloff percentage and power thresholds
- **perturbation**: Numerical stability constants

**Use cases:**
- Optimize time-frequency resolution tradeoffs
- Customize spectral analysis parameters
- Adjust numerical stability for edge cases

## Usage

### Default Behavior

The framework loads these YAML files at startup. If a file is missing or a parameter is not specified, the system falls back to hardcoded defaults (which match these example values).

### Custom Configuration

To use custom parameters, you have three options:

#### Option 1: Edit YAML Files Directly

Edit the YAML files in the `config/` directory:

```yaml
# config/perturbations.yaml
noise:
  snr_db: 15.0  # More aggressive noise for stress testing
```

#### Option 2: Use Environment Variable (Recommended for Private Configs)

Point to a custom configuration directory using the `AUDIO_TRUST_CONFIG_DIR` environment variable:

```bash
# Clone your private config repo
git clone https://github.com/yourorg/audio-trust-configs-private.git config-private/

# Use private configs
export AUDIO_TRUST_CONFIG_DIR=config-private/
python -m audio_trust_harness run --audio sample.wav --out audit.jsonl

# Or inline for a single command
AUDIO_TRUST_CONFIG_DIR=./config-private python -m audio_trust_harness run \
  --audio sample.wav \
  --out audit.jsonl
```

**Benefits of this approach:**
- Keep proprietary configurations in private repositories
- Switch between different config sets (development, staging, production)
- Avoid modifying the default `config/` directory

#### Option 3: Override at Runtime via CLI

Use CLI flags to override specific parameters:

```bash
python -m audio_trust_harness run \
  --audio sample.wav \
  --out audit.jsonl \
  --fragility-threshold 0.4 \
  --clipping-threshold 0.90
```

### Example: Custom Noise Testing

```yaml
# perturbations.yaml
noise:
  snr_db: 15.0  # More aggressive noise for stress testing
```

```bash
python -m audio_trust_harness run --audio sample.wav --out audit.jsonl --perturbations noise
```

### Example: Domain-Specific Thresholds

```yaml
# thresholds.yaml
deferral_policy:
  fragility_threshold: 0.4  # More tolerant for music (natural variation)
  clipping_threshold: 0.90  # Stricter clipping detection
```

## Plugin System (Future)

The configuration system is designed to support a plugin architecture for custom perturbations and indicators:

1. **Custom Perturbations**: Define new perturbation types in separate YAML/Python modules
2. **Custom Indicators**: Implement proprietary acoustic features as plugins
3. **Plugin Registry**: Load and register plugins at runtime

See `EXTENSIBILITY.md` (when available) for plugin development guidelines.

## Security & Privacy

⚠️ **Important**: Do not commit proprietary parameters, sensitive thresholds, or production-tuned configurations to public repositories. Use:

- `.gitignore` for local overrides
- Environment-specific config files (`.local.yaml`)
- Separate private repositories for proprietary implementations

## Validation

Configuration values are validated at load time:

- **Type checking**: Ensures values are correct types (float, int, string)
- **Range validation**: Some parameters have valid ranges (e.g., semitones: -24 to 24)
- **Dependency checks**: Related parameters are validated together (e.g., nperseg and noverlap)

Invalid configurations will raise clear error messages with guidance.

## Contributing

When adding new configurable parameters:

1. Add to appropriate YAML file with comments
2. Update this README with usage examples
3. Add default fallback in `config.py`
4. Document valid ranges and use cases
5. Add validation logic if needed

---

**Philosophy**: The framework is the methodology; the parameters are the experiments. By externalizing configuration, we enable users to explore the space of indicator robustness without revealing proprietary detection strategies.
